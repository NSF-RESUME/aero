# AERO Server Walkthrough

AERO is a FastAPI service that lets users register **Flows** (Globus Compute functions wrapped in Globus Flows state machines), automatically re-runs them when their input **Data** changes, and records **Provenance** so chained pipelines can be traced end-to-end. Globus is the execution substrate: Globus Auth for identity, Globus Compute for function execution, Globus Flows for orchestration, Globus Transfer/GCS for data movement, Globus Search for discovery, and Globus Timer for periodic triggers.

## 1. Bootstrapping (`aero/main.py`, `__init__.py`, `config.py`)

- `aero/__init__.py` constructs a module-level `GLOBUS_CLIENT` singleton from `Config.SEARCH_INDEX`. Routers import it directly.
- `aero/config.py` reads all environment variables at import (DB credentials, Globus IDs, OAuth client secrets, GCS endpoint/collection/gateway IDs) and assembles `SQLALCHEMY_DATABASE_URI`.
- `aero/main.py` builds the `FastAPI` app with a `lifespan` that calls `create_db_and_tables()` and creates the Globus Search index if missing, then mounts the three routers (`data`, `flow`, `provenance`).

## 2. Persistence (`database.py`, `database_info.py`, `migrations/`)

- `database.py` builds the SQLModel engine and exposes `get_session()` for FastAPI DI.
- `database_info.py` puts everything in an `aero-schema` Postgres schema.
- `aero/migrations/` is Alembic; schema is also created eagerly at startup for dev.

## 3. Domain model (`aero/models/`)

The model carries the whole AERO conceptual model:

- **Data** (`data.py`) is the central entity — a logical dataset with a name, optional URL, and a Globus collection (`collection_uuid`, `collection_url`). It has many `versions` and many `tags`.
- **DataVersion** (`data_version.py`) is a snapshot: `version`, `checksum`, `created_at`, FK to Data, plus one DataFile and m:n links into Provenance via `ProvenanceDerivation` (consumed) and `ProvenanceContribution` (produced).
- **DataFile** (`data_file.py`) is the physical artifact: filename, size, encoding, type.
- **Flow** (`flows.py`) is the automation unit. It references a Function plus optional pull/commit functions, stores `function_args` as JSON, a `policy` (TriggerEnum: INGESTION, TIMER, ANY_INPUT, ALL_INPUT), a `timer` interval, and the resulting Globus `timer_job_id`. Flows link to their input Data via `derived_from` (FlowDerivation) and to output Data via `contributed_to` (FlowContribution). `_run_flow()` consults the trigger policy: ANY_INPUT fires when any input version is newer than `last_executed`; ALL_INPUT requires all inputs to be newer.
- **Function** (`function.py`) wraps a Globus Compute function UUID; one Function can back many Flows.
- **Provenance** (`provenance.py`) is the lineage record. Each row links a `flow_id` to a set of input DataVersions (`derived_from`) and output DataVersions (`contributed_to`). This is what makes chaining safe: when a Provenance row is created, any downstream Flow whose inputs just got a new version becomes eligible to fire.
- **Tag** (`tag.py`) supports discovery; many-to-many with Data.

The picture: **Data → DataVersion → DataFile** on the data side; **Flow ↔ Data** through derivation/contribution tables on the registration side; **Provenance ↔ DataVersion** through derivation/contribution tables on the execution side. Together they form a DAG of versioned data and the flows that produced it.

## 4. HTTP API (`aero/routers/`)

**`data.py` — `/data`**
- `GET /` list (paginated, 15/page), `GET /{id}`, `GET /{id}/versions`, `GET /{id}/latest`.
- `GET /search?query=…` proxies into the Globus Search index, giving cross-team discovery.

**`flow.py` — `/flow`**
- `GET /`, `GET /{flow_id}` return flows with their input/output Data graph and execution history.
- `POST /register` is the meaty one. The body (`FlowIn`) carries:
  - `gc_endpoint` (Globus Compute endpoint),
  - `function_uuid` plus optional `pull_function_uuid` / `commit_function_uuid` (the download → user-fn → commit triple the workflow templates use),
  - `input_data` / `output_data` dicts (each entry resolves to a Data record, possibly creating one for outputs),
  - `flow_kwargs`, `timer`, `rule` (policy), and notification `email`.

  Registration deduplicates by hashing kwargs+inputs, persists Function/Flow/Data rows, and wires up the derived_from/contributed_to relationships. Execution itself is handled by Globus Flows + Globus Timer — the router only writes metadata.

**`provenance.py` — `/prov`**
- `GET /` lists provenance rows.
- `POST /new` is the callback the running flow hits when it finishes. It looks up input DataVersions, creates DataVersion+DataFile rows for outputs, links them via the Provenance derivation/contribution tables, then calls `data.add_new_version()` and `data.rerun_flow()` on each output Data — which is the mechanism that **chains flows together**: a freshly produced DataVersion immediately re-evaluates trigger policies on every downstream Flow that derives from it.

## 5. Globus integration (`aero/globus/client.py`, `utils.py`)

`GlobusClient` is a thin facade over four Globus SDK clients:
- **SearchClient** — `add_search_entry()` and `search()` for the discovery index seeded on startup.
- **SpecificFlowClient** — `run_flow()` to actually execute a registered flow (USER_FLOW, VERIFY_AND_MODIFY variants matching the templates in `workflow/`).
- **TimerClient** — `set_timer()` schedules periodic flow runs and returns `timer_job_id` stored on the Flow row.
- **AuthClient** — `oauth2_token_introspect()` for auth and email→UUID lookup for notifications.

`auth.py` validates Bearer tokens via that AuthClient and raises `UnauthorizedError` / `ForbiddenError` from `error_handler.py`. (Decorators are currently commented out; endpoints are effectively open in this dev branch.)

## 6. Flow templates (`workflow/`)

These are JSON Globus Flows state machines — the actual execution graphs AERO hands to `SpecificFlowClient.run_flow()`:

- **`download-commit-flow`** — `download → prepare-commit → database-commit`. Pure data import, no user code.
- **`single-function-compute`** — `download → custom-user-function → database-commit`, with an `ActionFailureHandler` that emails the registered user a stack trace. This is the canonical user-flow template.
- **`user-flow`** — `getVersions → execute → updateMetadata`, used when version-aware metadata updates are required.
- **`trial`** — minimal `S1 → S2` example showing result chaining via `ResultPath`/`$.` expressions.

The "commit" terminal state in each template is what calls back into `POST /prov/new`, closing the loop between Globus Flows execution and AERO's lineage database.

## 7. Deployment (`docker-compose.yml`, `Dockerfiles/`, `nginx/`, `scripts/`)

- **web** — Python 3.11 / Uvicorn serving FastAPI on :8081, hot-reloaded by mounting `/app/aero`.
- **database** — Postgres 17.4 with persistent volume `osprey-postgres-data`.
- **nginx** — reverse proxy on :80/:443; `/` → web, `/adminer` → adminer.
- **adminer** — DB UI for dev.
- **endpoint** (separate Dockerfile) — runs `globus-compute-endpoint start default` so the deployment can execute its own Compute functions.
- `scripts/prepare_start.sh` provisions the Docker volume and verifies Postgres before `docker compose up`.
- `scripts/setup_globus_connect.sh` installs Globus Connect Server 5.4 on the host and registers the collection AERO uses for transfers.

## How the parts connect end-to-end

1. A user `POST /flow/register`s a flow, naming input Data, output Data, a Compute function, and a trigger policy. AERO persists Flow/Function/Data and (if `timer` is set) schedules a Globus Timer job.
2. When the trigger fires (timer tick, or a freshly-written DataVersion satisfying ANY/ALL_INPUT), `GLOBUS_CLIENT` launches one of the `workflow/` templates on the user's Globus Compute endpoint.
3. The template downloads inputs from the GCS collection, runs the user function, and on success POSTs to `/prov/new`.
4. The provenance router writes the new DataVersion + DataFile, links a Provenance row to inputs and outputs, and calls `rerun_flow()` on the output Data — which re-evaluates trigger policies on every Flow that `derived_from` it, propagating execution along the DAG.
5. New Data entries are indexed into Globus Search so other users can discover and build on them via `GET /data/search`.

That cycle — *register → trigger → execute → record provenance → re-trigger downstream* — is the collaborative automation hub.
