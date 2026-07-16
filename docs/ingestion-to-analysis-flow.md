# How an analysis flow dependent on ingestion data gets run

Traced through the aero server code under `aero/`.
File links below are relative to this file's location (`docs/`).

## Short version

It's **event-driven but synchronous** — there's no background scheduler or message
queue. When an ingestion flow reports new output data via `POST /prov/new`, that same
request handler inline-detects every analysis flow depending on that data and runs the
ones whose policy is satisfied.

## The dependency link (set up at registration)

When a flow is registered ([routers/flow.py](../aero/routers/flow.py) `POST /flow/register`),
its `input_data` and `output_data` become graph edges in the DB:

- `input_data` → rows in the `FlowDerivation` junction table (`Flow.derived_from` → `Data`)
- `output_data` → rows in `FlowContribution` (`Flow.contributed_to` → `Data`)

So an analysis flow declares "I depend on Data X" by listing X in its `input_data`, and
the ingestion flow declares "I produce Data X" via its `output_data`. They're linked
through the shared `Data` record — no direct flow-to-flow reference.

The trigger behavior is stored per-flow as `policy`
([models/flows.py:26](../aero/models/flows.py#L26) `TriggerEnum`):

| Policy | Value | Meaning |
|---|---|---|
| `INGESTION` | 0 | this flow *is* an ingestion flow (runs on a timer to pull data) |
| `TIMER` | 1 | run on a schedule |
| `ANY_INPUT` | 2 | run when **any** dependency gets a new version |
| `ALL_INPUT` | 3 | run when **all** dependencies have a newer version than last run |

## The trigger chain (data ingested → analysis launched)

1. **Ingestion completes** → client posts to
   [routers/provenance.py:53](../aero/routers/provenance.py#L53) `add_record` with the
   produced `output_data`.

2. **New version written** — for each output, `d.add_new_version(...)` appends an immutable
   `DataVersion` to the `Data` record
   ([provenance.py:70](../aero/routers/provenance.py#L70)).

3. **Dependents detected** — immediately after,
   [provenance.py:81](../aero/routers/provenance.py#L81) calls `d.rerun_flow(session)`.
   That method ([models/data.py:102](../aero/models/data.py#L102)) queries:
   ```python
   select(Flow).where(Flow.derived_from.any(id=self.id))
   ```
   i.e. every flow that lists this Data as an input — the analysis flows.

4. **Policy check + launch** — for each such flow it calls `_run_flow()`
   ([models/flows.py:113](../aero/models/flows.py#L113)). For an `ANY_INPUT` analysis it
   checks whether any dependency's `last_version().created_at > self.last_executed`; if so it
   fires:
   ```python
   GLOBUS_CLIENT.run_flow(endpoint_uuid=..., function_uuid=self.function_id,
                          pull_function_uuid=..., commit_function_uuid=...,
                          tasks=function_args, email=self.email)
   ```
   then stamps `last_executed`. `ALL_INPUT` is the same but requires *every* dependency to be
   newer.

5. **Globus launches the analysis** — `run_flow`
   ([globus/client.py:81](../aero/globus/client.py#L81)) submits the `USER_FLOW` Globus
   Flow (`0d8ace1a-…`, [globus/utils.py](../aero/globus/utils.py)) with the
   pull/commit/analysis function UUIDs.

6. **Loop closes** — when the analysis finishes it posts its own results back to
   `POST /prov/new`, which can in turn trigger anything downstream of *its* output.

## Things worth flagging

- **It runs inside the ingestion request.** The launch happens synchronously in the
  `POST /prov/new` handler, so an ingestion post blocks on kicking off dependent flows.
  There's no retry/queue — if `run_flow` fails, the whole request 500s
  ([provenance.py:94](../aero/routers/provenance.py#L94)).
- **`INGESTION`/`TIMER` don't launch from `rerun_flow`.** Only `ANY_INPUT`/`ALL_INPUT` fire
  the analysis via `run_flow`. `INGESTION` and `TIMER` set up timer flows instead — so an
  analysis meant to react to new data must be registered with `rule: 2` (ANY) or `rule: 3`
  (ALL), not `0`.
- **Two `# TODO`s sit right on this path** — `rerun_flow` is marked "Fix implementation"
  ([data.py:103](../aero/models/data.py#L103)) and the trigger call is marked "maybe fix"
  ([provenance.py:80](../aero/routers/provenance.py#L80)), so this mechanism may still be
  in flux.
