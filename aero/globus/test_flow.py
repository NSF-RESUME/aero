from globus_automate_client import create_flows_client

FLOW_ID = "58862f48-f2f1-4620-b5a0-64550acc7fc0"

flows_client = create_flows_client()

print(flows_client.scope_for_flow(FLOW_ID))

flows_client.run_flow(
    flow_id=FLOW_ID,
    flow_scope=None,
    flow_input={
        "osprey-worker-endpoint": "28054165-5187-4d29-9ba8-451478e4eb7c",
        "download-function": "a690ccf7-103c-4d7d-addb-165979c63086",
        "database-commit-function": "d6478c9d-5dc4-4d83-8deb-dee264a3262b",
        "tasks": '[{"endpoint": "28054165-5187-4d29-9ba8-451478e4eb7c", "function": "a690ccf7-103c-4d7d-addb-165979c63086", "kwargs": {"source_id": 8}}]',
    },
    label="test osprey flow",
)
