import json
from pathlib import Path


WORKFLOW_PATH = Path("n8n/workflows/complaint-processing.json")


def _load_workflow() -> dict:
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_workflow_connections_reference_existing_nodes():
    workflow = _load_workflow()
    node_names = {node["name"] for node in workflow["nodes"]}

    for source_name, connection_groups in workflow["connections"].items():
        assert source_name in node_names
        for outputs in connection_groups.values():
            for output in outputs:
                for connection in output:
                    assert connection["node"] in node_names


def test_workflow_does_not_send_business_policy_fields():
    workflow = _load_workflow()
    forbidden_fields = {"action", "action_status", "reason"}

    for node in workflow["nodes"]:
        body_parameters = (
            node.get("parameters", {})
            .get("bodyParameters", {})
            .get("parameters", [])
        )
        sent_fields = {
            parameter.get("name") for parameter in body_parameters
        }
        assert sent_fields.isdisjoint(forbidden_fields)
