# Complaint Processing Specification

## Purpose

The system accepts customer complaints from online and phone channels,
classifies them, and triggers permitted automated business actions.

The system follows this principle:

> Deterministic where possible. Use an LLM where interpretation is required.
> Return to deterministic controls before executing business actions.

## Processing Invariants

1. Every accepted complaint must be persisted before processing begins.

2. Complaints that match an explicit deterministic rule must not invoke
   the LLM.

3. Complaints that require semantic interpretation may be classified by
   Claude through AWS Bedrock.

4. LLM output must be validated against the application's structured
   complaint classification model before it is used downstream.

5. The LLM must not directly approve refunds or execute business actions.

6. Automated actions must be selected by deterministic business rules
   in the application after loading the persisted classification. Workflow
   or client input must not supply the authorized action or status.

7. Workflow retries must not create duplicate business actions for the
   same complaint and action type.

8. If LLM classification fails, the complaint must be marked as failed
   and the downstream workflow must not be triggered.

9. A downstream workflow-delivery failure must not overwrite a successful
   classification. Complaint processing state and workflow-dispatch state
   must remain distinguishable.

10. Online and phone complaints must converge on the same complaint
   processing pipeline.

11. External integrations must not receive AWS credentials or other
    application secrets through complaint payloads.

12. `summary` must contain a short factual description of the complaint.
    Router diagnostics must not be stored in that customer-facing field.

## Current Input Contracts

### Online complaint

```json
{
  "customer_id": "CUST-1001",
  "channel": "online",
  "complaint_text": "I have a duplicate charge on my account."
}
```

## LLM Classification Contract

Claude is used only when the deterministic router cannot confidently
classify the complaint from an explicit rule.

Claude must return structured data matching this contract:

```json
{
  "category": "billing | delivery | account | product | service | other",
  "subcategory": "duplicate_charge | charge_after_cancellation | refund_not_received | delivery_delay | missing_delivery | account_access | product_issue | service_issue | other",
  "priority": "low | medium | high",
  "customer_intent": "short description",
  "summary": "short factual summary"
}
```

### LLM Constraints

- Output must be valid JSON.
- Output must pass application-level Pydantic validation.
- The model must not invent facts that are not present in the complaint.
- The model must not approve refunds or other business actions.
- Temperature should remain deterministic where practical for classification.
- Invalid or failed classification must not continue to workflow execution.

## Deterministic Routing Rules

The current implementation contains the following explicit rules:

| Complaint signal | Category | Subcategory | Priority | Route |
| --- | --- | --- | --- | --- |
| `duplicate charge` | billing | duplicate_charge | high | deterministic |
| `order not delivered` | delivery | missing_delivery | medium | deterministic |
| Anything requiring semantic interpretation | determined by classifier | determined by classifier | determined by classifier | llm |

A new deterministic rule should only be added when the input signal is
explicit enough that semantic interpretation is unnecessary.

Do not add broad keyword rules that could incorrectly classify ambiguous
customer language.

## Business Action Policy

Classification and business-action authorization are separate concerns.

The classifier describes the complaint. It does not decide which
business operation is permitted.

Current automated policies include:

| Classification | Permitted action | Initial status |
| --- | --- | --- |
| billing / duplicate_charge | initiate_duplicate_charge_refund | approved |
| billing / charge_after_cancellation | investigate_post_cancellation_charge | initiated |

Business actions are selected by deterministic application policy after
classification. `POST /complaints/{complaint_id}/actions` accepts an empty
JSON command (`{}`). The API loads the persisted complaint and derives the
permitted action, initial status, and reason. Client or n8n supplied action
fields are rejected.

Adding a new LLM classification must not automatically create a new
business action.

## Idempotency

Workflow delivery may occur more than once.

The application must therefore tolerate repeated action requests.

For the current implementation, the persistence invariant is:

```text
(complaint_id, action) must be unique
```

A repeated request for an existing complaint/action pair must return the
existing action rather than intentionally creating another action.

The database uniqueness constraint is the final persistence safeguard. If
concurrent requests race on insert, the losing request must roll back, fetch
the winning row, and return it as an idempotent replay.

## Status Semantics

Complaint status describes classification state:

| Status | Meaning |
| --- | --- |
| `received` | Raw complaint has been accepted and persisted. |
| `processing` | Routing/classification is in progress. |
| `processed` | A validated classification is persisted. It does not imply that a business action completed. |
| `needs_information` | Classification completed but the complaint is too vague for downstream action. |
| `failed` | Routing/classification failed. |

Workflow delivery is tracked separately as `not_requested`, `pending`,
`dispatched`, or `failed`.

## Failure Behaviour

If complaint classification fails:

```text
complaint
    ↓
status = processing
    ↓
classification failure
    ↓
status = failed
    ↓
NO n8n workflow trigger
    ↓
NO automated business action
```

The original error is propagated so that the API/infrastructure layer
can observe and handle the failure.

If classification succeeds but workflow delivery fails:

```text
complaint status = processed
workflow dispatch status = failed
classification fields remain persisted
```

This demo records the distinction but does not implement reliable retry
delivery. A transactional outbox is the production-grade solution.

## Testing Requirements

Changes to complaint processing must preserve tests proving that:

1. Explicit deterministic complaints do not invoke the LLM.
2. Ambiguous complaints invoke the LLM classifier.
3. Structured classification is propagated into the complaint record.
4. LLM failure marks processing as failed.
5. LLM failure does not trigger downstream workflow execution.
6. Repeated business-action requests do not create duplicate action rows.
7. Supported actions and statuses are derived from persisted classification.
8. Unsupported classifications cannot create business actions.
9. Client-supplied action/status fields are rejected.
10. Uniqueness races return the action created by the winning request.
11. Workflow-delivery failure preserves a successful classification.
12. Insufficient-information complaints do not trigger workflow delivery.

External Bedrock and n8n calls should be mocked in unit tests.

Persistence behaviour should be tested against an isolated database.
