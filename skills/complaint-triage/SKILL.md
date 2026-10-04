# Complaint Triage Engineering Skill

## Purpose

Use this skill when implementing or modifying complaint classification,
routing, or automated complaint actions.

Before changing code, read:

- `specs/complaint-processing.md`
- the existing routing implementation
- the classification schema
- the relevant automated tests

The complaint-processing specification is the source of truth for system
invariants.

## Engineering Principle

Preserve this processing boundary:

```text
deterministic interpretation where possible
              ↓
LLM interpretation only when necessary
              ↓
validated structured output
              ↓
deterministic business policy
              ↓
permitted automated action
```

Never allow an LLM classification to directly authorize or execute a
business action.

## Workflow for Making Changes

### 1. Understand the requested behaviour

Identify whether the change affects:

- complaint input
- deterministic routing
- LLM classification
- business-action policy
- workflow orchestration
- persistence
- failure handling

Do not start implementation until the expected behaviour and affected
invariants are clear.

### 2. Prefer deterministic behaviour

If the requirement can be represented by a precise, unambiguous rule,
prefer deterministic code.

Do not call the LLM merely because an LLM is available.

Use the LLM when semantic interpretation of unstructured customer
language is genuinely required.

A deterministic rule is not automatically safe merely because it is
deterministic. Avoid weak keyword matches for negated or disclaimed language,
especially when classification can start a financial workflow. Prefer a
small explicit guard and fall back to semantic classification rather than
building a complex regex-based language parser.

### 3. Keep classification separate from authorization

Classification answers questions such as:

```text
What kind of complaint is this?
What is the subcategory?
What priority does it have?
What outcome is the customer seeking?
```

Business policy answers:

```text
What action, if any, is the system permitted to execute?
```

These concerns must remain separate.

The application API owns this policy. A workflow may request action
processing, but it must not supply an action name, approval status, or policy
reason. Load the persisted complaint and derive the permitted action from its
validated category/subcategory using an allow-listed deterministic mapping.

Complaint text alone must never produce an `approved` financial action. It may
initiate a permitted review workflow, while actual approval requires separate
deterministic transaction and eligibility evidence.

### 4. Treat LLM output as untrusted input

LLM output must:

- use the defined structured classification contract
- pass application validation
- contain only supported enum values
- fail closed if parsing or validation fails

Do not pass arbitrary model-generated action names, API arguments, SQL,
URLs, credentials, or executable instructions to downstream systems.

### 5. Preserve idempotency

Workflow systems may retry requests.

Any business action must therefore tolerate repeated delivery.

Do not rely on n8n or another orchestrator to provide exactly-once
execution.

Enforce idempotency at the application or persistence boundary.

Keep the database uniqueness constraint as the final safeguard. When two
requests race on insert, catch the uniqueness `IntegrityError`, roll back the
losing transaction, fetch the winning row, and return it.

### 6. Keep failure and status meanings precise

- `failed` means routing/classification failed.
- `processed` means a validated classification was persisted; it does not mean
  a refund, investigation, or other business action completed.
- Track downstream workflow delivery separately from complaint processing.
- A workflow-delivery failure must not erase or relabel a successful
  classification.
- Keep `summary` factual. Do not store router/debug reasons in that field.

### 7. Add tests before considering the change complete

At minimum, test the behaviour directly affected by the change.

For routing changes, test:

```text
input → expected route
```

For LLM-path changes, mock the external model boundary.

For business-action changes, verify repeated requests cannot create
duplicate effects.

Also verify unsupported classifications and caller-supplied action fields
cannot manufacture an authorized business action.

For failure-path changes, verify downstream business actions are not
triggered after an upstream failure.

### 8. Run the full test suite

Run:

```bash
python -m pytest tests/ -v
```

Do not consider the change complete while existing tests fail.

Tests must configure their own isolated database and must not require a
developer's private `.env` file.

## Security Rules

Never:

- commit AWS credentials
- put credentials in prompts
- expose AWS credentials to the browser
- send credentials through n8n complaint payloads
- trust an LLM-generated business action without deterministic validation
- log sensitive complaint text unnecessarily
- bypass application validation because model output appears correct

Browser clients call the application API.

The application owns AWS Bedrock access.

Deployment environments should use appropriate AWS identity mechanisms
rather than credentials embedded in application source code.

## Definition of Done

A complaint-processing change is complete when:

1. The behaviour is consistent with `specs/complaint-processing.md`.
2. Deterministic logic is used where appropriate.
3. LLM output is validated before downstream use.
4. Business actions remain deterministically controlled.
5. Idempotency is preserved where actions can be retried.
6. Failure behaviour is explicit.
7. Complaint and workflow-delivery states are not conflated.
8. Relevant automated tests exist.
9. The full test suite passes from a clean test configuration.
10. No secrets or credentials have been introduced into source control.
