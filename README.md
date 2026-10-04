# AI-Assisted Customer Complaint System

A customer complaint processing system demonstrating a spec-first approach
to AI-assisted software engineering.

The system accepts complaints from online and phone-transcript channels,
uses deterministic processing where possible, uses Claude through AWS
Bedrock when semantic interpretation is required, and returns to
deterministic business rules before automated actions are executed.

## Design Principle

> Deterministic where possible. Use AI where interpretation is necessary.
> Return to deterministic controls before executing business actions.

Claude is used to **interpret** ambiguous customer language. It does not
authorize refunds or directly execute business operations.

## Architecture

```mermaid
flowchart TD
    ONLINE[React Online Form]
    PHONE[Phone / Speech-to-Text]
    API[FastAPI Complaint API]
    DB[(PostgreSQL)]
    ROUTER{Deterministic Router}
    CLAUDE[Claude via AWS Bedrock]
    VALIDATE[Pydantic Validation]
    N8N[n8n Workflow]
    POLICY{Server-Side Deterministic Policy}
    ACTION[Business Action]
    ACTIONDB[(Action Audit / PostgreSQL)]

    ONLINE --> API
    PHONE --> API

    API --> DB
    API --> ROUTER

    ROUTER -->|Explicit rule| DB
    ROUTER -->|Semantic interpretation required| CLAUDE

    CLAUDE --> VALIDATE
    VALIDATE --> DB

    DB --> N8N
    N8N -->|Empty action request| POLICY
    POLICY --> ACTION
    ACTION --> ACTIONDB
```

## Processing Flow

An online complaint enters through the React application. A phone complaint
currently enters as a speech-to-text transcript through the phone adapter.
Both are normalized into the same internal complaint contract.

The deterministic router first checks whether the complaint matches a known,
explicit rule.

For example:

```text
"I have a duplicate charge"
        ↓
deterministic classification
        ↓
billing / duplicate_charge / high
```

Ambiguous language instead uses Claude:

```text
"I cancelled last week but you've taken money again"
        ↓
Claude via AWS Bedrock
        ↓
validated structured classification
        ↓
billing / charge_after_cancellation / high
```

Both paths then converge:

```text
classification
      ↓
persisted as processed
      ↓
n8n dispatch
      ↓
server-side deterministic business policy
      ↓
permitted automated action
```

This separation prevents the LLM from directly authorizing business actions.

### Status Semantics

Complaint status describes classification progress:

- `received`: the raw complaint is persisted.
- `processing`: routing/classification is running.
- `processed`: a validated classification is persisted; no business outcome
  is implied.
- `needs_information`: the complaint is too vague for downstream action.
- `failed`: routing/classification failed.

Workflow delivery is recorded separately as `not_requested`, `pending`,
`dispatched`, or `failed`. A complaint can therefore remain `processed` while
its workflow dispatch is `failed`.

The `summary` field always contains a factual complaint summary. Internal
routing reasons are not stored in that customer-facing field.

## Key Engineering Properties

- **Spec-first:** processing invariants and contracts are defined in
  `specs/complaint-processing.md`.
- **AI coding guidance:** `skills/complaint-triage/SKILL.md` defines how
  coding agents should safely modify the complaint pipeline.
- **Structured AI output:** Claude output is parsed and validated using
  Pydantic models.
- **Deterministic control:** known complaints bypass the LLM entirely.
- **Controlled automation:** the API loads the persisted complaint and selects
  business actions from a deterministic allow-listed policy. Neither Claude,
  n8n, nor a client may supply an approved action.
- **Idempotency:** repeated or racing workflow delivery returns one action,
  protected by a database uniqueness constraint and conflict recovery.
- **Failure isolation:** classification failure and workflow-delivery failure
  are recorded separately, so a temporary n8n outage does not discard a
  successful classification.
- **Testability:** Bedrock and n8n boundaries are mocked in unit tests, while
  persistence behaviour is tested using an isolated database.

## Technology Stack

| Area | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| API | Python, FastAPI |
| Validation | Pydantic |
| Persistence | PostgreSQL, SQLAlchemy |
| AI | Claude via AWS Bedrock |
| Workflow orchestration | n8n |
| Testing | pytest |
| Local infrastructure | Docker Compose |

## Local Development

### Prerequisites

Install:

- Python 3
- Node.js and npm
- Docker Desktop
- AWS CLI

AWS credentials must not be committed to the repository.

For local development, configure an AWS CLI profile with permission to
invoke the configured Bedrock model.

### Environment Configuration

Create a local `.env` file:

```env
DATABASE_URL=postgresql+psycopg://complaint_user:complaint_password@localhost:5432/complaints

AWS_PROFILE=complaint-demo
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6

N8N_WEBHOOK_URL=http://localhost:5678/webhook/complaint-processed
```

The `.env` file is excluded from source control.

For a deployed environment, prefer an appropriate AWS IAM role or other
temporary credential mechanism rather than embedding long-lived AWS
credentials in the application.

### Start PostgreSQL and n8n

From the repository root:

```bash
docker compose up -d
```

Check the containers:

```bash
docker compose ps
```

n8n is available locally at:

```text
http://localhost:5678
```

> Do not use `docker compose down -v` unless you intentionally want to
> delete the local PostgreSQL and n8n volumes.

### Start the FastAPI Backend

Create and activate a virtual environment if required:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the API:

```bash
python -m uvicorn app.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000
```

The API is available at:

```text
http://127.0.0.1:8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

### Start the React Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

The development UI is normally available at:

```text
http://localhost:5173
```

### Run the Tests

From the repository root with the Python virtual environment activated:

```bash
python -m pytest tests/ -v
```

The test suite covers:

- deterministic routing
- LLM routing without making real Bedrock requests
- propagation of structured LLM classification
- LLM failure behaviour
- prevention of workflow execution after classification failure
- insufficient-information safety behaviour
- server-side business-action authorization
- rejection of client-supplied action/status fields
- sequential and uniqueness-race idempotency
- preservation of classification after workflow-delivery failure
- n8n export contract and connection integrity

External Bedrock and n8n calls are mocked in unit tests so the suite does
not depend on those services or incur model usage.

Persistence behaviour is tested against an isolated SQLite database.
PostgreSQL remains the runtime database.

The test bootstrap supplies its own SQLite `DATABASE_URL`, so the suite does
not require a developer `.env` and will not connect to a developer database.

## Local n8n Integration

The local n8n workflow receives processed classifications at:

```text
POST /webhook/complaint-processed
```

Because n8n runs inside Docker while FastAPI runs on the host, n8n calls
the application using:

```text
http://host.docker.internal:8000
```

The workflow selects the supported billing branches and requests action
processing through the FastAPI complaint-action endpoint. It sends an empty
JSON body:

```http
POST /complaints/{complaint_id}/actions
Content-Type: application/json

{}
```

The API then reloads the persisted complaint and derives the action, initial
status, and reason from its deterministic allow-listed policy. Any client or
workflow-supplied `action`, `action_status`, or `reason` fields are rejected.

The server-side policy includes:

```text
billing / duplicate_charge
    → initiate_duplicate_charge_refund

billing / charge_after_cancellation
    → investigate_post_cancellation_charge
```

The workflow responds to the initial webhook immediately. Business-action
creation therefore occurs asynchronously relative to the initial complaint
response, and the React demo briefly polls the action endpoint after a
successful dispatch to display the resulting action.

### Import the n8n Workflow

The repository includes the complaint-processing workflow:

```text
n8n/workflows/complaint-processing.json
```

After starting n8n, open:

```text
http://localhost:5678
```

Import `n8n/workflows/complaint-processing.json` using the n8n workflow
import option.

After importing:

1. Open the workflow.
2. Verify the FastAPI action endpoint uses:

   ```text
   http://host.docker.internal:8000
   ```

3. Publish/activate the workflow.
4. Verify the production webhook path is:

   ```text
   /webhook/complaint-processed
   ```

The FastAPI application sends processed complaints to:

```text
http://localhost:5678/webhook/complaint-processed
```

The difference between these addresses is intentional:

```text
FastAPI on host → n8n
http://localhost:5678

n8n container → FastAPI on host
http://host.docker.internal:8000
```

Do not commit n8n credentials, API keys, tokens, or other secrets in the
exported workflow.

## Production Hardening

This repository is a take-home implementation intended to demonstrate the
architecture and engineering approach. A production deployment would require
additional controls.

### Authentication and Authorization

The local n8n webhook and complaint-action endpoint are not currently secured.

In production:

- authenticate n8n-to-API communication
- authorize which callers may request complaint-action processing
- protect externally accessible complaint APIs using the application's
  authentication and authorization model

The demo already rejects client-supplied action fields and derives permitted
actions and initial statuses server-side. Authentication, customer ownership,
and operator authorization remain deployment responsibilities.

### Business Action Safety

Claude classifies complaints but does not authorize business actions.

The current duplicate-charge refund action demonstrates the policy boundary.
A real financial action would additionally validate conditions such as:

- customer ownership of the transaction
- transaction state
- refund eligibility
- amount and policy limits
- previous refunds/actions
- authorization to perform the operation

The deterministic policy layer remains responsible for these checks.

### Idempotency and Concurrency

The application checks for an existing complaint/action pair and enforces a
database uniqueness constraint. If concurrent requests both pass the initial
check, the losing insert rolls back after the uniqueness conflict, fetches the
winning row, and returns it as an idempotent replay.

A dedicated idempotency key or workflow event ID would also be preferable
for more complex action lifecycles.

### Reliable Workflow Delivery

The current API persists the classification as `processed`, records workflow
dispatch as `pending`, and then invokes n8n over HTTP. Dispatch success or
failure is recorded separately without changing the successful complaint
classification.

For production, this creates a failure window between the database commit
and workflow delivery.

A transactional outbox and asynchronous worker/queue would provide stronger
delivery guarantees:

```text
database transaction
    ├── update complaint
    └── create outbox event
              ↓
          commit once
              ↓
       asynchronous worker
              ↓
             n8n
```

The demo does not provide an asynchronous retry worker, durable delivery,
dead-letter handling, or reconciliation when `workflow_dispatch_status` is
`failed`. Those remain production limitations.

### Database Migrations

The demo creates SQLAlchemy tables automatically. Production schema changes
should use versioned migrations, such as Alembic, rather than relying on
`create_all()`. Existing local databases created before the
`workflow_dispatch_status` column must be recreated or migrated before running
this version.

### LLM Reliability and Observability

A production deployment should add bounded retries and timeouts for transient
Bedrock failures, structured telemetry for correlation IDs, model latency,
validation failures, workflow dispatch, and action execution, plus regression
evaluation datasets. Sensitive complaint content should not be logged unless
necessary.

### Phone and Deployment Boundaries

The phone endpoint accepts an existing speech-to-text transcript; telephony and
speech recognition are intentionally out of scope. Deployed workloads should
use an IAM role and temporary AWS credentials with least-privilege Bedrock
permissions rather than long-lived keys.
