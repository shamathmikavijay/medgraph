import { useEffect, useState } from "react";
import GraphView from "./GraphView";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [conditions, setConditions] = useState([]);
  const [conditionMedicines, setConditionMedicines] = useState([]);

  const [condition, setCondition] = useState("");
  const [drugA, setDrugA] = useState("");
  const [drugB, setDrugB] = useState("");

  const [result, setResult] = useState(null);
  const [view, setView] = useState("simple");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load conditions + all medicines when website opens
  useEffect(() => {
    async function loadInitialData() {
      try {
        const conditionsResponse = await fetch(`${API_URL}/conditions`);

        if (!conditionsResponse.ok) {
          throw new Error("Could not load conditions.");
        }

        const conditionsData = await conditionsResponse.json();

        setConditions(conditionsData.conditions || conditionsData);
      } catch (err) {
        setError(
          "Could not connect to the MedGraph backend. Make sure FastAPI is running."
        );
      }
    }

    loadInitialData();
  }, []);

  // Load medicines for selected condition
  async function handleConditionChange(e) {
    const selectedCondition = e.target.value;

    setCondition(selectedCondition);
    setDrugA("");
    setResult(null);

    if (!selectedCondition) {
      setConditionMedicines([]);
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/medicines?condition=${encodeURIComponent(
          selectedCondition
        )}`
      );

      if (!response.ok) {
        throw new Error("Could not load medicines.");
      }

      const data = await response.json();

      const medicineData = data.medicines || data;

      const medicineNames = medicineData
        .map((medicine) =>
          typeof medicine === "string"
            ? medicine
            : medicine.drug_name
        )
        .filter(Boolean);

      const uniqueMedicineNames = [...new Set(medicineNames)];

      setConditionMedicines(uniqueMedicineNames);
    } catch (err) {
      setError("Could not load medicines for this condition.");
    }
  }

  // Analyze medicine pair
  async function handleAnalyze() {
    if (!drugA || !drugB) {
      setError("Please select both medicines.");
      return;
    }

    if (drugA === drugB) {
      setError("Please select two different medicines.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        `${API_URL}/analyze?drug_a=${encodeURIComponent(
          drugA
        )}&drug_b=${encodeURIComponent(drugB)}`
      );

      if (!response.ok) {
        throw new Error("Analysis failed.");
      }

      const data = await response.json();

      console.log("Analyze result:", data);

      setResult(data);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to analyze these medicines. Please check the backend."
      );
    } finally {
      setLoading(false);
    }
  }
  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>MedGraph</h1>
          <p>Biomedical Interaction Explorer</p>
        </div>
      </header>

      <main className="dashboard">

        {/* LEFT PANEL */}
        <section className="panel select-panel">
          <h2>Select</h2>

          <label>Condition / Indication</label>

          <select
            value={condition}
            onChange={handleConditionChange}
          >
            <option value="">Select condition</option>

            {conditions.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>

          <label>Medicine A</label>

          <select
            value={drugA}
            onChange={(e) => setDrugA(e.target.value)}
            disabled={!condition}
          >
            <option value="">Select medicine</option>

            {conditionMedicines.map((medicine) => (
              <option key={medicine} value={medicine}>
                {medicine}
              </option>
            ))}
          </select>

          <label>Medicine B</label>

          <select
            value={drugB}
            onChange={(e) => setDrugB(e.target.value)}
          >
            <option value="">Select medicine</option>

            {conditionMedicines.map((medicine) => (
              <option key={medicine} value={medicine}>
                {medicine}
              </option>
            ))}
          </select>

          <button
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>

          {error && <p className="error">{error}</p>}
        </section>

        {/* CENTER PANEL */}
        <section className="panel graph-panel">
          <h2>Knowledge Graph</h2>

          {!result && (
            <div className="placeholder">
              Select two medicines and click Analyze.
            </div>
          )}

          {result && result.found === true && (
            <>
              <h3>
                {drugA} → {drugB}
              </h3>

              <GraphView result={result} />
            </>
          )}

          {result && result.found === false && (
            <div className="placeholder">
              No supported biological connection was found in the current dataset.
            </div>
          )}
        </section>

        {/* RIGHT PANEL */}
        <section className="panel explanation-panel">
          <h2>Explanation</h2>

          <div className="toggle">
            <button
              className={view === "simple" ? "active" : ""}
              onClick={() => setView("simple")}
            >
              Simple
            </button>

            <button
              className={view === "scientific" ? "active" : ""}
              onClick={() => setView("scientific")}
            >
              Scientific
            </button>
          </div>

          {!result && (
            <p className="placeholder">
              Select two medicines to view their biological connection.
            </p>
          )}

          {result?.found === false && (
            <p className="explanation">
              No supported biological connection was found in the current dataset.
            </p>
          )}

          {result?.found === true && view === "simple" && (
            <>
              <div className="relationship-badge">
                {result.relationship_label}
              </div>

              <p className="explanation">
                {result.message}
              </p>

              <div className="summary-box">
                <span>Connection type</span>

                <strong>
                  {result.relationship_type
                    ?.replaceAll("_", " ")
                    .replace(/\b\w/g, (letter) =>
                      letter.toUpperCase()
                    )}
                </strong>
              </div>

              <div className="summary-box">
                <span>Shared biological targets</span>
                <strong>{result.shared_target_count ?? 0}</strong>
              </div>
            </>
          )}

          {result?.found === true && view === "scientific" && (
            <>
              <div className="relationship-badge">
                Evidence View
              </div>

              <h3>Biological Relationship</h3>

              <p className="explanation">
                {result.drug_a?.name} and {result.drug_b?.name} are connected
                through the biological evidence represented in the current
                MedGraph knowledge graph.
              </p>

              <div className="evidence">
                <h3>Evidence</h3>

                {result.graph?.edges?.map((edge, index) => (
                  <div className="evidence-card" key={index}>
                    <strong>{edge.relationship}</strong>

                    <p>
                      {result.graph.nodes.find(
                        (node) => node.id === edge.source
                      )?.name || edge.source}
                      {" → "}
                      {result.graph.nodes.find(
                        (node) => node.id === edge.target
                      )?.name || edge.target}
                    </p>

                    {edge.mechanism_of_action && (
                      <p>
                        <b>Mechanism:</b> {edge.mechanism_of_action}
                      </p>
                    )}

                    <small>
                      Source: {edge.evidence_source || "ChEMBL"}
                    </small>

                    {edge.mechanism_record_id && (
                      <small className="record-id">
                        Record ID: {edge.mechanism_record_id}
                      </small>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </section>
      </main>

      <footer>
        Educational prototype — not diagnostic or prescribing advice.
      </footer>
    </div>
  );
}

export default App;