import json
from pathlib import Path


WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / "n8n"
    / "workflows"
    / "complaint-processing.json"
)


def _load_workflow() -> dict:
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def test_workflow_connections_reference_existing_nodes():
    workflow = _load_workflow()
    node_names = {node["name"] for node in workflow["nodes"]}
    referenced_targets = set()

    for source_name, connection_groups in workflow["connections"].items():
        assert source_name in node_names
        for outputs in connection_groups.values():
            for output in outputs:
                assert output
                for connection in output:
                    assert connection["node"] in node_names
                    referenced_targets.add(connection["node"])

    assert referenced_targets == {"Request Permitted Action"}


def test_workflow_has_no_business_policy_branches():
    workflow = _load_workflow()
    node_types = {node["type"] for node in workflow["nodes"]}

    assert len(workflow["nodes"]) == 2
    assert node_types == {
        "n8n-nodes-base.webhook",
        "n8n-nodes-base.httpRequest",
    }
    assert "n8n-nodes-base.switch" not in node_types
    assert "n8n-nodes-base.if" not in node_types
    assert "n8n-nodes-base.set" not in node_types


def test_workflow_sends_only_an_empty_action_trigger():
    workflow = _load_workflow()
    request_node = next(
        node
        for node in workflow["nodes"]
        if node["type"] == "n8n-nodes-base.httpRequest"
    )
    parameters = request_node["parameters"]

    assert parameters["method"] == "POST"
    assert parameters["url"].endswith(
        "/complaints/{{ $json.body.complaint_id }}/actions"
    )
    assert parameters["sendBody"] is True
    assert parameters["bodyParameters"]["parameters"] == []


def test_workflow_contains_no_business_authorization_fields():
    workflow = _load_workflow()
    forbidden_keys = {"action", "action_status", "reason"}
    forbidden_decision_terms = {"approved", "approval", "refund"}

    for key, value in _walk(workflow):
        assert key.lower() not in forbidden_keys

        if key == "name" and isinstance(value, str):
            assert value.lower() not in forbidden_keys

        if isinstance(value, str):
            lowered = value.lower()
            assert not any(
                term in lowered for term in forbidden_decision_terms
            )
