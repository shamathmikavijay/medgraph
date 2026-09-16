import { useEffect, useMemo, useState } from "react";
import GraphView from "./GraphView";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function normaliseMedicineList(data) {
  const list = data?.medicines || data || [];

  return [
    ...new Set(
      list
        .map((item) =>
          typeof item === "string"
            ? item
            : item?.drug_name || item?.name
        )
        .filter(Boolean)
    ),
  ].sort((a, b) => a.localeCompare(b));
}

function getConditionName(condition) {
  if (!condition) return "";

  if (typeof condition === "string") {
    return condition;
  }

  return (
    condition.condition_name ||
    condition.name ||
    condition.label ||
    condition.condition_id ||
    "Unknown indication"
  );
}

function getConditionKey(condition, index) {
  if (typeof condition === "string") {
    return condition;
  }

  return (
    condition?.condition_id ||
    condition?.condition_name ||
    condition?.name ||
    index
  );
}

function formatRelationship(value) {
  if (!value) return "Biological relationship";

  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function App() {
  const [page, setPage] = useState("home");

  const [conditions, setConditions] = useState([]);
  const [stats, setStats] = useState(null);

  const [conditionSearch, setConditionSearch] = useState("");
  const [selectedCondition, setSelectedCondition] = useState("");

  const [conditionMedicines, setConditionMedicines] = useState([]);
  const [allMedicines, setAllMedicines] = useState([]);

  const [medicineASearch, setMedicineASearch] = useState("");
  const [medicineBSearch, setMedicineBSearch] = useState("");

  const [drugA, setDrugA] = useState("");
  const [drugB, setDrugB] = useState("");

  const [showAllA, setShowAllA] = useState(false);
  const [showAllB, setShowAllB] = useState(false);

  const [result, setResult] = useState(null);

  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingMedicines, setLoadingMedicines] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const [error, setError] = useState("");

  // ======================================================
  // INITIAL DATA
  // ======================================================

  useEffect(() => {
    async function loadInitialData() {
      setLoadingInitial(true);
      setError("");

      try {
        const [conditionsResponse, statsResponse, medicinesResponse] =
          await Promise.all([
            fetch(`${API_URL}/conditions`),
            fetch(`${API_URL}/graph/stats`),
            fetch(`${API_URL}/medicines`),
          ]);

        if (!conditionsResponse.ok) {
          throw new Error("Could not load conditions.");
        }

        if (!statsResponse.ok) {
          throw new Error("Could not load graph statistics.");
        }

        if (!medicinesResponse.ok) {
          throw new Error("Could not load medicines.");
        }

        const conditionsData = await conditionsResponse.json();
        const statsData = await statsResponse.json();
        const medicinesData = await medicinesResponse.json();

        const rawConditions = Array.isArray(conditionsData)
          ? conditionsData
          : conditionsData.conditions || [];

        const cleanConditions = [
          ...new Set(
            rawConditions
              .map((condition) => getConditionName(condition))
              .filter(Boolean)
          ),
        ].sort((a, b) => a.localeCompare(b));

        setConditions(cleanConditions);
        setStats(statsData);
        setAllMedicines(normaliseMedicineList(medicinesData));
      } catch (err) {
        console.error(err);

        setError(
          "Could not connect to the MedGraph backend. Make sure FastAPI is running on port 8000."
        );
      } finally {
        setLoadingInitial(false);
      }
    }

    loadInitialData();
  }, []);

  // ======================================================
  // UNIVERSAL CONDITION SEARCH
  // ======================================================

  const conditionSuggestions = useMemo(() => {
    const query = conditionSearch.trim().toLowerCase();

    if (!query) return [];

    return conditions
      .filter((condition) =>
        condition.toLowerCase().includes(query)
      )
      .sort((a, b) => {
        const aLower = a.toLowerCase();
        const bLower = b.toLowerCase();

        const aStarts = aLower.startsWith(query);
        const bStarts = bLower.startsWith(query);

        if (aStarts && !bStarts) return -1;
        if (!aStarts && bStarts) return 1;

        return a.localeCompare(b);
      })
      .slice(0, 12);
  }, [conditions, conditionSearch]);

  function handleConditionInput(event) {
    const value = event.target.value;

    setConditionSearch(value);
    setError("");

    if (
      selectedCondition &&
      value.trim().toLowerCase() !==
        selectedCondition.toLowerCase()
    ) {
      setSelectedCondition("");
      setConditionMedicines([]);
      setDrugA("");
      setDrugB("");
      setMedicineASearch("");
      setMedicineBSearch("");
      setResult(null);
      setShowAllA(false);
      setShowAllB(false);
    }
  }

  async function selectCondition(condition) {
    const conditionName = getConditionName(condition);

    setSelectedCondition(conditionName);
    setConditionSearch(conditionName);

    setDrugA("");
    setDrugB("");
    setMedicineASearch("");
    setMedicineBSearch("");

    setResult(null);
    setShowAllA(false);
    setShowAllB(false);

    setLoadingMedicines(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/medicines?condition=${encodeURIComponent(
          conditionName
        )}`
      );

      if (!response.ok) {
        throw new Error(
          "Could not load medicines for this indication."
        );
      }

      const data = await response.json();

      setConditionMedicines(normaliseMedicineList(data));
    } catch (err) {
      console.error(err);

      setConditionMedicines([]);

      setError(
        "Could not load medicines associated with this indication."
      );
    } finally {
      setLoadingMedicines(false);
    }
  }

  function submitConditionSearch(event) {
    event.preventDefault();

    const query = conditionSearch.trim();

    if (!query) {
      setError("Enter a condition or indication.");
      return;
    }

    const exactMatch = conditions.find(
      (condition) =>
        condition.toLowerCase() === query.toLowerCase()
    );

    if (exactMatch) {
      selectCondition(exactMatch);
      return;
    }

    if (conditionSuggestions.length > 0) {
      selectCondition(conditionSuggestions[0]);
      return;
    }

    setError(
      "No matching indication was found in the current MedGraph dataset."
    );
  }

  // ======================================================
  // MEDICINE SEARCH
  // ======================================================

  function filterMedicines(list, search) {
    const query = search.trim().toLowerCase();

    if (!query) return list;

    return list
      .filter((medicine) =>
        medicine.toLowerCase().includes(query)
      )
      .sort((a, b) => {
        const aLower = a.toLowerCase();
        const bLower = b.toLowerCase();

        const aStarts = aLower.startsWith(query);
        const bStarts = bLower.startsWith(query);

        if (aStarts && !bStarts) return -1;
        if (!aStarts && bStarts) return 1;

        return a.localeCompare(b);
      });
  }

  const filteredAMedicines = useMemo(
    () =>
      filterMedicines(
        conditionMedicines,
        medicineASearch
      ),
    [conditionMedicines, medicineASearch]
  );

  const filteredBMedicines = useMemo(
    () =>
      filterMedicines(
        allMedicines,
        medicineBSearch
      ),
    [allMedicines, medicineBSearch]
  );

  const visibleAMedicines = showAllA
    ? filteredAMedicines
    : filteredAMedicines.slice(0, 12);

  const visibleBMedicines = showAllB
    ? filteredBMedicines
    : filteredBMedicines.slice(0, 12);

  function selectMedicineA(medicine) {
    setDrugA(medicine);
    setMedicineASearch(medicine);
    setResult(null);
    setError("");

    if (drugB === medicine) {
      setDrugB("");
      setMedicineBSearch("");
    }
  }

  function selectMedicineB(medicine) {
    if (medicine === drugA) {
      setError(
        "Medicine A and Medicine B must be different."
      );
      return;
    }

    setDrugB(medicine);
    setMedicineBSearch(medicine);
    setResult(null);
    setError("");
  }

  // ======================================================
  // ANALYZE
  // ======================================================

  async function handleAnalyze() {
    if (!drugA || !drugB) {
      setError("Please select both medicines.");
      return;
    }

    if (drugA === drugB) {
      setError("Please select two different medicines.");
      return;
    }

    setAnalyzing(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        `${API_URL}/analyze?drug_a=${encodeURIComponent(
          drugA
        )}&drug_b=${encodeURIComponent(drugB)}`
      );

      if (!response.ok) {
        throw new Error("Analysis request failed.");
      }

      const data = await response.json();

      setResult(data);
      setPage("analyze");

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    } catch (err) {
      console.error(err);

      setError(
        "Unable to analyze these medicines. Check that the backend is running."
      );
    } finally {
      setAnalyzing(false);
    }
  }

  // ======================================================
  // OTHER SAME-INDICATION OPTIONS
  // ======================================================

  const otherOptions = useMemo(
    () =>
      conditionMedicines
        .filter(
          (medicine) =>
            medicine !== drugA && medicine !== drugB
        )
        .slice(0, 4),
    [conditionMedicines, drugA, drugB]
  );

  // ======================================================
  // NAVIGATION
  // ======================================================

  function navigate(destination) {
    setPage(destination);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  // ======================================================
  // HOME
  // ======================================================

  function renderHome() {
    return (
      <>
        <section className="hero">
          <div className="hero-content">
            <div className="eyebrow">
              EXPLAINABLE BIOMEDICAL EXPLORATION
            </div>

            <h1>
              Understand how medicines are
              <span> biologically connected.</span>
            </h1>

            <p className="hero-copy">
              MedGraph connects medicines, indications and
              biological targets using evidence represented in
              biomedical datasets — then explains the
              relationship in understandable language.
            </p>

            <div className="hero-actions">
              <button
                className="primary-button"
                onClick={() => navigate("explore")}
              >
                Explore medicines
              </button>

              <button
                className="secondary-button"
                onClick={() => navigate("about")}
              >
                How MedGraph works
              </button>
            </div>

            <p className="research-note">
              Research and educational prototype. MedGraph does
              not provide prescribing or clinical safety advice.
            </p>
          </div>

          <div className="hero-visual">
            <div className="visual-card">
              <div className="visual-label">
                BIOLOGICAL RELATIONSHIP
              </div>

              <div className="mini-graph">
                <div className="mini-node medicine-node">
                  Medicine A
                </div>

                <div className="mini-line" />

                <div className="mini-node target-node">
                  Biological
                  <br />
                  Target
                </div>

                <div className="mini-line" />

                <div className="mini-node medicine-node">
                  Medicine B
                </div>
              </div>

              <p>
                Follow evidence paths instead of relying on a
                simple yes/no interaction label.
              </p>
            </div>
          </div>
        </section>

        <section className="stats-strip">
          <div>
            <strong>{stats?.drug_nodes ?? "500+"}</strong>
            <span>Medicines</span>
          </div>

          <div>
            <strong>
              {stats?.condition_nodes ?? "1,300+"}
            </strong>
            <span>Indications</span>
          </div>

          <div>
            <strong>{stats?.target_nodes ?? "195+"}</strong>
            <span>Biological targets</span>
          </div>

          <div>
            <strong>{stats?.total_edges ?? "8,000+"}</strong>
            <span>Graph relationships</span>
          </div>
        </section>

        <section className="home-section">
          <div className="section-heading">
            <span>WHY MEDGRAPH?</span>

            <h2>
              Go beyond a simple interaction lookup.
            </h2>
          </div>

          <div className="feature-grid">
            <article className="feature-card">
              <div className="feature-number">01</div>
              <h3>Condition guided</h3>

              <p>
                Begin with a medical indication and explore the
                medicines represented for it in the current
                dataset.
              </p>
            </article>

            <article className="feature-card">
              <div className="feature-number">02</div>
              <h3>Graph based</h3>

              <p>
                Trace shared targets and other represented
                relationships through the biomedical knowledge
                graph.
              </p>
            </article>

            <article className="feature-card">
              <div className="feature-number">03</div>
              <h3>Explainable</h3>

              <p>
                See both a simple explanation and the underlying
                scientific evidence instead of a black-box
                answer.
              </p>
            </article>
          </div>
        </section>
      </>
    );
  }

  // ======================================================
  // EXPLORE
  // ======================================================

  function renderExplore() {
    return (
      <section className="page-shell">
        <div className="page-heading">
          <div>
            <span className="eyebrow">
              CONDITION-GUIDED EXPLORATION
            </span>

            <h1>Explore medicines</h1>

            <p>
              Find an indication, choose Medicine A from its
              associated medicines, then compare it with another
              medicine represented in MedGraph.
            </p>
          </div>
        </div>

        <div className="explore-layout">
          <section className="selection-card">
            <div className="step-heading">
              <span>1</span>

              <div>
                <h2>Find an indication</h2>

                <p>
                  Search using any letters or part of the
                  indication name.
                </p>
              </div>
            </div>

            <form
              className="search-form"
              onSubmit={submitConditionSearch}
            >
              <div className="search-input-wrap">
                <span className="search-icon">⌕</span>

                <input
                  value={conditionSearch}
                  onChange={handleConditionInput}
                  placeholder="Search condition or indication..."
                  autoComplete="off"
                />
              </div>

              <button type="submit">Select</button>
            </form>

            {conditionSearch.trim() &&
              !selectedCondition && (
                <div className="suggestions">
                  {conditionSuggestions.length > 0 ? (
                    conditionSuggestions.map(
                      (condition) => (
                        <button
                          key={condition}
                          type="button"
                          onClick={() =>
                            selectCondition(condition)
                          }
                        >
                          {condition}
                        </button>
                      )
                    )
                  ) : (
                    <div className="no-results">
                      No matching indications.
                    </div>
                  )}
                </div>
              )}

            {selectedCondition && (
              <div className="selected-condition">
                <span>Selected indication</span>
                <strong>{selectedCondition}</strong>
              </div>
            )}
          </section>

          <section
            className={`selection-card ${
              !selectedCondition ? "disabled-card" : ""
            }`}
          >
            <div className="step-heading">
              <span>2</span>

              <div>
                <h2>Select two medicines</h2>

                <p>
                  Medicine A comes from the selected indication.
                  Medicine B can be any medicine represented in
                  the current MedGraph dataset.
                </p>
              </div>
            </div>

            {!selectedCondition ? (
              <div className="empty-selection">
                Select an indication first.
              </div>
            ) : loadingMedicines ? (
              <div className="loading-box">
                Loading medicines...
              </div>
            ) : (
              <div className="medicine-columns">
                <div className="medicine-column">
                  <div className="medicine-column-heading">
                    <div>
                      <span className="medicine-letter">
                        A
                      </span>

                      <div>
                        <h3>Medicine A</h3>

                        <p>
                          Associated with{" "}
                          {selectedCondition}
                        </p>
                      </div>
                    </div>

                    {drugA && (
                      <span className="selected-pill">
                        Selected
                      </span>
                    )}
                  </div>

                  <input
                    className="medicine-search"
                    value={medicineASearch}
                    onChange={(event) => {
                      setMedicineASearch(
                        event.target.value
                      );

                      if (
                        event.target.value !== drugA
                      ) {
                        setDrugA("");
                        setResult(null);
                      }
                    }}
                    placeholder="Search Medicine A..."
                  />

                  <div className="medicine-list">
                    {visibleAMedicines.length > 0 ? (
                      visibleAMedicines.map(
                        (medicine) => (
                          <button
                            key={medicine}
                            type="button"
                            className={
                              drugA === medicine
                                ? "medicine-option selected"
                                : "medicine-option"
                            }
                            onClick={() =>
                              selectMedicineA(medicine)
                            }
                          >
                            <span>{medicine}</span>

                            {drugA === medicine && (
                              <strong>✓</strong>
                            )}
                          </button>
                        )
                      )
                    ) : (
                      <div className="no-results">
                        No matching medicines.
                      </div>
                    )}
                  </div>

                  {filteredAMedicines.length > 12 && (
                    <button
                      type="button"
                      className="show-all-button"
                      onClick={() =>
                        setShowAllA(!showAllA)
                      }
                    >
                      {showAllA
                        ? "Show fewer"
                        : `Show all ${filteredAMedicines.length}`}
                    </button>
                  )}
                </div>

                <div className="medicine-column">
                  <div className="medicine-column-heading">
                    <div>
                      <span className="medicine-letter">
                        B
                      </span>

                      <div>
                        <h3>Medicine B</h3>

                        <p>
                          Search the complete medicine
                          catalogue
                        </p>
                      </div>
                    </div>

                    {drugB && (
                      <span className="selected-pill">
                        Selected
                      </span>
                    )}
                  </div>

                  <input
                    className="medicine-search"
                    value={medicineBSearch}
                    onChange={(event) => {
                      setMedicineBSearch(
                        event.target.value
                      );

                      if (
                        event.target.value !== drugB
                      ) {
                        setDrugB("");
                        setResult(null);
                      }
                    }}
                    placeholder="Search Medicine B..."
                  />

                  <div className="medicine-list">
                    {visibleBMedicines.length > 0 ? (
                      visibleBMedicines.map(
                        (medicine) => (
                          <button
                            key={medicine}
                            type="button"
                            disabled={medicine === drugA}
                            className={
                              drugB === medicine
                                ? "medicine-option selected"
                                : "medicine-option"
                            }
                            onClick={() =>
                              selectMedicineB(medicine)
                            }
                          >
                            <span>{medicine}</span>

                            {drugB === medicine && (
                              <strong>✓</strong>
                            )}
                          </button>
                        )
                      )
                    ) : (
                      <div className="no-results">
                        No matching medicines.
                      </div>
                    )}
                  </div>

                  {filteredBMedicines.length > 12 && (
                    <button
                      type="button"
                      className="show-all-button"
                      onClick={() =>
                        setShowAllB(!showAllB)
                      }
                    >
                      {showAllB
                        ? "Show fewer"
                        : `Show all ${filteredBMedicines.length}`}
                    </button>
                  )}
                </div>
              </div>
            )}
          </section>
        </div>

        {selectedCondition && (
          <div className="compare-bar">
            <div className="compare-summary">
              <div>
                <span className="compare-letter">A</span>

                <div>
                  <small>Medicine A</small>
                  <strong>
                    {drugA || "Not selected"}
                  </strong>
                </div>
              </div>

              <span className="compare-arrow">→</span>

              <div>
                <span className="compare-letter">B</span>

                <div>
                  <small>Medicine B</small>
                  <strong>
                    {drugB || "Not selected"}
                  </strong>
                </div>
              </div>
            </div>

            <button
              className="primary-button analyze-button"
              disabled={
                !drugA || !drugB || analyzing
              }
              onClick={handleAnalyze}
            >
              {analyzing
                ? "Analyzing..."
                : "Analyze relationship"}
            </button>
          </div>
        )}
      </section>
    );
  }

  // ======================================================
  // ANALYZE PAGE
  // ======================================================

  function renderAnalyze() {
    if (!result) {
      return (
        <section className="page-shell">
          <div className="empty-page">
            <h1>No analysis yet</h1>

            <p>
              Select two medicines from Explore to generate an
              evidence-grounded analysis.
            </p>

            <button
              className="primary-button"
              onClick={() => navigate("explore")}
            >
              Go to Explore
            </button>
          </div>
        </section>
      );
    }

    const explanations = result.explanations || {};

    const score = result.evidence_score || {
      score: 0,
      max_score: 100,
      strength: "Insufficient represented evidence",
      reasons: [],
    };

    const adverse =
      result.adverse_effect_evidence || {
        available: false,
        status: "Not represented in current dataset",
        message:
          "Pair-specific adverse-effect evidence is not represented in the current MedGraph dataset.",
      };

    const sharedConditions = Array.isArray(
      result.shared_conditions
    )
      ? result.shared_conditions
      : [];

    const sharedTargets = Array.isArray(
      result.shared_targets
    )
      ? result.shared_targets
      : [];

    return (
      <section className="page-shell analyze-page">
        <div className="analysis-top">
          <div>
            <span className="eyebrow">
              BIOLOGICAL RELATIONSHIP ANALYSIS
            </span>

            <h1>
              {result.drug_a?.name || drugA}
              <span> + </span>
              {result.drug_b?.name || drugB}
            </h1>

            <p>
              Evidence-grounded relationship exploration using
              the biological records represented in MedGraph.
            </p>
          </div>

          <button
            className="secondary-button"
            onClick={() => navigate("explore")}
          >
            ← Change medicines
          </button>
        </div>

        <div className="relationship-banner">
          <div>
            <span>RELATIONSHIP</span>

            <strong>
              {result.relationship_label ||
                "Insufficient evidence"}
            </strong>
          </div>

          <p>
            {explanations.simple_explanation ||
              result.message ||
              "No supported biological relationship was found in the current dataset."}
          </p>
        </div>

        <div className="analysis-grid">
          <section className="analysis-card graph-card">
            <div className="card-heading">
              <div>
                <span>KNOWLEDGE GRAPH</span>
                <h2>Evidence path</h2>
              </div>

              <div className="graph-key">
                {formatRelationship(
                  result.relationship_type
                )}
              </div>
            </div>

            <GraphView result={result} />
          </section>

          <section className="analysis-card score-card">
            <div className="card-heading">
              <div>
                <span>REPRESENTED EVIDENCE</span>
                <h2>Evidence score</h2>
              </div>
            </div>

            <div className="score-circle">
              <strong>{score.score ?? 0}</strong>
              <span>/ {score.max_score ?? 100}</span>
            </div>

            <h3>
              {typeof score.strength === "string"
                ? score.strength
                : "Evidence strength unavailable"}
            </h3>

            <div className="score-progress">
              <div
                style={{
                  width: `${Math.min(
                    Number(score.score) || 0,
                    100
                  )}%`,
                }}
              />
            </div>

            <div className="score-reasons">
              {Array.isArray(score.reasons) &&
              score.reasons.length > 0 ? (
                score.reasons.map(
                  (reason, index) => (
                    <div key={index}>
                      <span>
                        {typeof reason === "string"
                          ? reason
                          : reason?.label ||
                            "Evidence"}
                      </span>

                      {typeof reason === "object" &&
                        reason?.points != null && (
                          <strong>
                            +{reason.points}
                          </strong>
                        )}
                    </div>
                  )
                )
              ) : (
                <p>
                  No score-producing evidence was represented
                  for this pair.
                </p>
              )}
            </div>

            <p className="score-disclaimer">
              {typeof score.disclaimer === "string"
                ? score.disclaimer
                : "This experimental score measures biological evidence represented in MedGraph. It is not a clinical safety score."}
            </p>
          </section>
        </div>

        <div className="analysis-grid lower-grid">
          <section className="analysis-card">
            <div className="card-heading">
              <div>
                <span>PLAIN LANGUAGE</span>
                <h2>Simple explanation</h2>
              </div>
            </div>

            <p className="large-explanation">
              {explanations.simple_explanation ||
                result.message ||
                "No explanation is available."}
            </p>
          </section>

          <section className="analysis-card">
            <div className="card-heading">
              <div>
                <span>SCIENTIFIC VIEW</span>
                <h2>Scientific explanation</h2>
              </div>
            </div>

            <p className="scientific-copy">
              {explanations.scientific_explanation ||
                "No scientific explanation is available for this pair."}
            </p>

            <small className="source-line">
              Explanation source:{" "}
              {explanations.explanation_source ||
                "MedGraph evidence-grounded generator"}
            </small>
          </section>
        </div>

        <section className="analysis-card evidence-section">
          <div className="card-heading">
            <div>
              <span>TRACEABLE DATA</span>
              <h2>Biological evidence</h2>
            </div>
          </div>

          {sharedTargets.length > 0 ? (
            <div className="target-grid">
              {sharedTargets.map(
                (target, index) => (
                  <article
                    className="target-evidence-card"
                    key={
                      target.target_id ||
                      target.id ||
                      index
                    }
                  >
                    <span className="evidence-type">
                      SHARED TARGET
                    </span>

                    <h3>
                      {target.target_name ||
                        target.name ||
                        "Biological target"}
                    </h3>

                    {target.target_id && (
                      <p>
                        <strong>ChEMBL target:</strong>{" "}
                        {target.target_id}
                      </p>
                    )}

                    {target.uniprot_accessions &&
                      (Array.isArray(
                        target.uniprot_accessions
                      ) ? (
                        <p>
                          <strong>UniProt:</strong>{" "}
                          {target.uniprot_accessions.join(
                            ", "
                          )}
                        </p>
                      ) : (
                        <p>
                          <strong>UniProt:</strong>{" "}
                          {String(
                            target.uniprot_accessions
                          )}
                        </p>
                      ))}

                    {target.drug_a_relationship && (
                      <p>
                        <strong>
                          {result.drug_a?.name ||
                            drugA}
                          :
                        </strong>{" "}
                        {typeof target.drug_a_relationship ===
                        "string"
                          ? target.drug_a_relationship
                          : JSON.stringify(
                              target.drug_a_relationship
                            )}
                      </p>
                    )}

                    {target.drug_b_relationship && (
                      <p>
                        <strong>
                          {result.drug_b?.name ||
                            drugB}
                          :
                        </strong>{" "}
                        {typeof target.drug_b_relationship ===
                        "string"
                          ? target.drug_b_relationship
                          : JSON.stringify(
                              target.drug_b_relationship
                            )}
                      </p>
                    )}
                  </article>
                )
              )}
            </div>
          ) : sharedConditions.length > 0 ? (
            <div className="condition-evidence">
              <p>
                These medicines share indication evidence in
                the current MedGraph dataset:
              </p>

              <div className="chip-row">
                {sharedConditions.map(
                  (condition, index) => (
                    <span
                      key={getConditionKey(
                        condition,
                        index
                      )}
                    >
                      {getConditionName(condition)}
                    </span>
                  )
                )}
              </div>
            </div>
          ) : (
            <div className="evidence-empty">
              No supported shared biological target or shared
              indication was found for this pair in the current
              dataset.
            </div>
          )}
        </section>

        <div className="analysis-grid final-grid">
          <section className="analysis-card adverse-card">
            <div className="card-heading">
              <div>
                <span>ADVERSE-EFFECT EVIDENCE</span>

                <h2>
                  {typeof adverse.status === "string"
                    ? adverse.status
                    : "Not represented in current dataset"}
                </h2>
              </div>
            </div>

            <p>
              {typeof adverse.message === "string"
                ? adverse.message
                : "Pair-specific adverse-effect evidence is not represented in the current MedGraph dataset."}
            </p>

            <div className="neutral-notice">
              A biological connection does not by itself prove
              a clinical drug interaction or a particular
              adverse effect.
            </div>
          </section>

          <section className="analysis-card">
            <div className="card-heading">
              <div>
                <span>SAME INDICATION</span>
                <h2>Other options to explore</h2>
              </div>
            </div>

            {selectedCondition &&
            otherOptions.length > 0 ? (
              <>
                <p className="options-intro">
                  These medicines are also represented for{" "}
                  <strong>{selectedCondition}</strong> in the
                  current indication data. This is not a safety
                  ranking or treatment recommendation.
                </p>

                <div className="option-list">
                  {otherOptions.map(
                    (medicine) => (
                      <button
                        key={medicine}
                        type="button"
                        onClick={() => {
                          setDrugB(medicine);
                          setMedicineBSearch(medicine);
                          setResult(null);
                          navigate("explore");
                        }}
                      >
                        <span>{medicine}</span>
                        <strong>Explore →</strong>
                      </button>
                    )
                  )}
                </div>
              </>
            ) : (
              <p className="options-intro">
                No additional same-indication options are
                available from the current selection.
              </p>
            )}
          </section>
        </div>
      </section>
    );
  }

  // ======================================================
  // EVIDENCE PAGE
  // ======================================================

  function renderEvidence() {
    return (
      <section className="page-shell info-page">
        <span className="eyebrow">
          DATA & TRANSPARENCY
        </span>

        <h1>Where MedGraph evidence comes from</h1>

        <p className="info-lead">
          MedGraph is designed to show the evidence represented
          in its knowledge graph rather than hide it behind a
          single answer.
        </p>

        <div className="info-grid">
          <article className="info-card">
            <span>01</span>
            <h2>ChEMBL</h2>

            <p>
              Medicine records, indications, mechanisms and
              biological target relationships used by this
              prototype originate from the project's ChEMBL
              dataset.
            </p>
          </article>

          <article className="info-card">
            <span>02</span>
            <h2>UniProt identifiers</h2>

            <p>
              Where available in the imported mechanism data,
              MedGraph displays UniProt accessions associated
              with represented biological targets.
            </p>
          </article>

          <article className="info-card">
            <span>03</span>
            <h2>NetworkX knowledge graph</h2>

            <p>
              Medicines, indications and targets are converted
              into graph nodes and relationships so the system
              can search for explainable evidence paths.
            </p>
          </article>
        </div>

        <div className="limitations-card">
          <h2>Important limitation</h2>

          <p>
            MedGraph's current dataset does not constitute a
            complete clinical drug-interaction database.
            Absence of a path does not establish absence of a
            real-world interaction, and a graph connection does
            not establish that two medicines are safe or unsafe
            to use together.
          </p>
        </div>
      </section>
    );
  }

  // ======================================================
  // ABOUT PAGE
  // ======================================================

  function renderAbout() {
    return (
      <section className="page-shell info-page">
        <span className="eyebrow">
          ABOUT THE PROJECT
        </span>

        <h1>
          Explain the connection, not just the result.
        </h1>

        <p className="info-lead">
          MedGraph is an explainable biomedical exploration
          prototype built to make medicine relationships easier
          to investigate and understand.
        </p>

        <div className="process-flow">
          <div>
            <strong>1</strong>
            <h3>Choose an indication</h3>

            <p>
              Start with a condition or indication represented
              in the dataset.
            </p>
          </div>

          <span>→</span>

          <div>
            <strong>2</strong>
            <h3>Select medicines</h3>

            <p>
              Pick Medicine A from the indication and Medicine B
              from the complete catalogue.
            </p>
          </div>

          <span>→</span>

          <div>
            <strong>3</strong>
            <h3>Traverse the graph</h3>

            <p>
              NetworkX searches the represented biological
              relationships.
            </p>
          </div>

          <span>→</span>

          <div>
            <strong>4</strong>
            <h3>Explain evidence</h3>

            <p>
              MedGraph presents the graph, source identifiers
              and grounded explanations.
            </p>
          </div>
        </div>

        <div className="limitations-card">
          <h2>Built for exploration, not prescribing</h2>

          <p>
            This hackathon prototype is intended for educational
            and research exploration. It does not diagnose,
            prescribe, determine dosage, or determine whether a
            medicine combination is clinically safe.
          </p>
        </div>
      </section>
    );
  }

  // ======================================================
  // MAIN RENDER
  // ======================================================

  return (
    <div className="app">
      <header className="navbar">
        <button
          className="brand"
          onClick={() => navigate("home")}
        >
          <span className="brand-mark">
            <i />
            <i />
            <i />
          </span>

          <span>
            <strong>MedGraph</strong>
            <small>Biomedical Explorer</small>
          </span>
        </button>

        <nav>
          <button
            className={page === "home" ? "active" : ""}
            onClick={() => navigate("home")}
          >
            Home
          </button>

          <button
            className={
              page === "explore" ? "active" : ""
            }
            onClick={() => navigate("explore")}
          >
            Explore
          </button>

          <button
            className={
              page === "analyze" ? "active" : ""
            }
            onClick={() => navigate("analyze")}
          >
            Analyze
          </button>

          <button
            className={
              page === "evidence" ? "active" : ""
            }
            onClick={() => navigate("evidence")}
          >
            Evidence
          </button>

          <button
            className={
              page === "about" ? "active" : ""
            }
            onClick={() => navigate("about")}
          >
            About
          </button>
        </nav>
      </header>

      {loadingInitial ? (
        <main className="initial-loader">
          <div className="loader" />
          <h2>Loading MedGraph</h2>

          <p>
            Connecting medicines, indications and biological
            targets...
          </p>
        </main>
      ) : (
        <main>
          {page === "home" && renderHome()}
          {page === "explore" && renderExplore()}
          {page === "analyze" && renderAnalyze()}
          {page === "evidence" && renderEvidence()}
          {page === "about" && renderAbout()}
        </main>
      )}

      {error && (
        <div className="global-error">
          <span>{error}</span>

          <button onClick={() => setError("")}>
            ×
          </button>
        </div>
      )}

      <footer className="footer">
        <div>
          <strong>MedGraph</strong>

          <span>
            Explainable biomedical relationship exploration.
          </span>
        </div>

        <p>
          Educational and research prototype — not diagnostic,
          prescribing, dosage, or clinical safety advice.
        </p>
      </footer>
    </div>
  );
}

export default App;