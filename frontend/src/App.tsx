import { useState } from "react";
import type { FormEvent } from "react";
import "./App.css";

type ComplaintStatus =
  | "received"
  | "processing"
  | "processed"
  | "needs_information"
  | "failed";

type WorkflowDispatchStatus =
  | "not_requested"
  | "pending"
  | "dispatched"
  | "failed";

type ComplaintResponse = {
  complaint_id: string;
  customer_id: string;
  channel: string;
  complaint_text: string;
  status: ComplaintStatus;
  workflow_dispatch_status: WorkflowDispatchStatus;

  processing_route: string | null;
  category: string | null;
  subcategory: string | null;
  priority: string | null;
  customer_intent: string | null;
  summary: string | null;
  model_used: string | null;

  created_at: string;
};

type ComplaintActionResponse = {
  action_id: string;
  complaint_id: string;
  action: string;
  action_status: string;
  reason: string;
  created_at: string;
};

function App() {
  const [customerId, setCustomerId] = useState("CUST-1001");
  const [complaintText, setComplaintText] = useState("");
  const [result, setResult] = useState<ComplaintResponse | null>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [actions, setActions] = useState<ComplaintActionResponse[]>([]);

  async function submitComplaint(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setActions([]);
    setSubmitting(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/complaints", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          customer_id: customerId,
          channel: "online",
          complaint_text: complaintText,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data: ComplaintResponse = await response.json();
      setResult(data);

      let actionData: ComplaintActionResponse[] = [];

      if (
        data.status === "processed" &&
        data.workflow_dispatch_status === "dispatched"
      ) {
        for (let attempt = 0; attempt < 5; attempt++) {
          const actionsResponse = await fetch(
            `http://127.0.0.1:8000/complaints/${data.complaint_id}/actions`
          );

          if (!actionsResponse.ok) {
            throw new Error(
              `Unable to load complaint actions: ${actionsResponse.status}`
            );
          }

          actionData = await actionsResponse.json();

          if (actionData.length > 0) {
            break;
          }

          await new Promise((resolve) => setTimeout(resolve, 500));
        }
      }

      setActions(actionData);
      setComplaintText("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to submit complaint"
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page">
      <section className="card">
        <div className="heading">
          <p className="eyebrow">Customer Care</p>
          <h1>Submit a complaint</h1>
          <p>
            Tell us what happened and we'll begin processing your complaint.
          </p>
        </div>

        <form onSubmit={submitComplaint}>
          <label htmlFor="customerId">Customer ID</label>
          <input
            id="customerId"
            value={customerId}
            onChange={(event) => setCustomerId(event.target.value)}
            required
          />

          <label htmlFor="complaint">What happened?</label>
          <textarea
            id="complaint"
            rows={7}
            value={complaintText}
            onChange={(event) => setComplaintText(event.target.value)}
            placeholder="Describe your complaint..."
            minLength={10}
            required
          />

          <button type="submit" disabled={submitting}>
            {submitting ? "Submitting..." : "Submit complaint"}
          </button>
        </form>

        {error && (
          <div className="message error">
            <strong>Submission failed</strong>
            <p>{error}</p>
          </div>
        )}

        {result && (
          <div className="result-card">
            <h2>
              {result.status === "needs_information"
                ? "More Information Needed"
                : result.status === "failed"
                ? "Complaint Processing Failed"
                : "Complaint Processed"}
            </h2>

            <p>
              <strong>Complaint ID:</strong> {result.complaint_id}
            </p>

            <p>
              <strong>Status:</strong>{" "}
              {result.status.replaceAll("_", " ")}
            </p>

            <p>
              <strong>Workflow Dispatch:</strong>{" "}
              {result.workflow_dispatch_status.replaceAll("_", " ")}
            </p>

            <p>
              <strong>Processing Route:</strong>{" "}
              {result.processing_route === "llm"
                ? "AI / Claude"
                : result.processing_route === "deterministic"
                ? "Deterministic"
                : "—"}
            </p>
            <p>
              <strong>Category:</strong> {result.category ?? "—"}
            </p>

            <p>
              <strong>Subcategory:</strong> {result.subcategory ?? "—"}
            </p>

            <p>
              <strong>Priority:</strong> {result.priority ?? "—"}
            </p>

            {result.summary && (
              <p>
                <strong>Summary:</strong> {result.summary}
              </p>
            )}

            {result.customer_intent && (
              <p>
                <strong>Customer Intent:</strong> {result.customer_intent}
              </p>
            )}

            {result.model_used && (
              <p>
                <strong>Model:</strong> {result.model_used}
              </p>
            )}

            {actions.length > 0 && (
              <div className="action-section">
                <h3>Automated Action</h3>

                {actions.map((action) => (
                  <div key={action.action_id} className="action-item">
                    <p>
                      <strong>Action:</strong>{" "}
                      {action.action.replaceAll("_", " ")}
                    </p>

                    <p>
                      <strong>Action Status:</strong>{" "}
                      {action.action_status}
                    </p>

                    <p>
                      <strong>Reason:</strong>{" "}
                      {action.reason}
                    </p>

                    <p>
                      <strong>Action ID:</strong>{" "}
                      {action.action_id}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        </section>
    </main>
  );
}

export default App;
