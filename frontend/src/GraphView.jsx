import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

function GraphView({ result }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    if (cyRef.current) {
      cyRef.current.destroy();
      cyRef.current = null;
    }

    if (!result) return;

    const drugA =
      result.drug_a?.name || "Medicine A";

    const drugB =
      result.drug_b?.name || "Medicine B";

    const sharedTargets =
      result.shared_targets || [];

    const sharedConditions =
      result.shared_conditions || [];

    const elements = [];

    // =====================================================
    // MEDICINE NODES
    // =====================================================

    elements.push({
      data: {
        id: "drug-a",
        label: drugA,
        type: "drug",
      },
      position: {
        x: 120,
        y: 220,
      },
    });

    elements.push({
      data: {
        id: "drug-b",
        label: drugB,
        type: "drug",
      },
      position: {
        x: 680,
        y: 220,
      },
    });

    // =====================================================
    // SHARED TARGET PATH
    // Keep graph focused: maximum 3 targets.
    // =====================================================

    if (sharedTargets.length > 0) {
      sharedTargets
        .slice(0, 3)
        .forEach((target, index) => {
          const targetId = `target-${index}`;

          const targetName =
            target.target_name ||
            target.name ||
            target.target_id ||
            "Biological target";

          const y =
            sharedTargets.length === 1
              ? 220
              : 120 + index * 110;

          elements.push({
            data: {
              id: targetId,
              label: targetName,
              type: "target",
            },
            position: {
              x: 400,
              y,
            },
          });

          elements.push({
            data: {
              id: `a-target-${index}`,
              source: "drug-a",
              target: targetId,
              label:
                target.drug_a_relationship ||
                target.drug_a_action ||
                "biological relationship",
              type: "evidence",
            },
          });

          elements.push({
            data: {
              id: `target-b-${index}`,
              source: targetId,
              target: "drug-b",
              label:
                target.drug_b_relationship ||
                target.drug_b_action ||
                "biological relationship",
              type: "evidence",
            },
          });
        });
    }

    // =====================================================
    // SHARED INDICATION PATH
    // Used only if no shared target exists.
    // Maximum 2 indications.
    // =====================================================

    else if (sharedConditions.length > 0) {
      sharedConditions
        .slice(0, 2)
        .forEach((condition, index) => {
          const conditionId =
            `condition-${index}`;

          const y =
            sharedConditions.length === 1
              ? 220
              : 170 + index * 120;

          const conditionName =
  typeof condition === "string"
    ? condition
    : condition.condition_name ||
      condition.name ||
      condition.label ||
      condition.condition_id ||
      "Unknown indication";

elements.push({
  data: {
    id: conditionId,
    label: conditionName,
    type: "condition",
  },
            position: {
              x: 400,
              y,
            },
          });

          elements.push({
            data: {
              id: `a-condition-${index}`,
              source: "drug-a",
              target: conditionId,
              label: "associated with",
              type: "indication",
            },
          });

          elements.push({
            data: {
              id: `condition-b-${index}`,
              source: conditionId,
              target: "drug-b",
              label: "associated with",
              type: "indication",
            },
          });
        });
    }

    // =====================================================
    // CYTOSCAPE
    // =====================================================

    const cy = cytoscape({
      container: containerRef.current,

      elements,

      layout: {
        name: "preset",
        fit: true,
        padding: 65,
      },

      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "text-wrap": "wrap",
            "text-max-width": "125px",
            "text-valign": "bottom",
            "text-halign": "center",
            "text-margin-y": 12,
            "font-size": "12px",
            "font-weight": "600",
            color: "#17352c",
            "overlay-opacity": 0,
          },
        },

        // MEDICINES
        {
          selector: 'node[type="drug"]',
          style: {
            width: 74,
            height: 74,
            shape: "ellipse",
            "background-color": "#173f34",
            "border-width": 5,
            "border-color": "#dceee5",
            color: "#17352c",
          },
        },

        // TARGETS
        {
          selector: 'node[type="target"]',
          style: {
            width: 72,
            height: 72,
            shape: "diamond",
            "background-color": "#9fd8bd",
            "border-width": 3,
            "border-color": "#5ca582",
          },
        },

        // CONDITIONS
        {
          selector: 'node[type="condition"]',
          style: {
            width: 76,
            height: 76,
            shape: "round-rectangle",
            "background-color": "#ead59c",
            "border-width": 3,
            "border-color": "#c5a95f",
          },
        },

        // EDGES
        {
          selector: "edge",
          style: {
            width: 2.5,
            "line-color": "#8aa79b",
            "target-arrow-color": "#8aa79b",
            "target-arrow-shape": "triangle",
            "arrow-scale": 0.9,
            "curve-style": "bezier",

            label: "data(label)",
            "font-size": "9px",
            "font-weight": "600",
            color: "#557067",

            "text-background-color": "#fbfaf5",
            "text-background-opacity": 1,
            "text-background-padding": "4px",

            "text-rotation": "autorotate",
          },
        },

        {
          selector: 'edge[type="indication"]',
          style: {
            "line-style": "dashed",
            "line-color": "#b99e5c",
            "target-arrow-color": "#b99e5c",
          },
        },

        {
          selector: "node:selected",
          style: {
            "border-width": 5,
            "border-color": "#d8b75d",
          },
        },
      ],

      minZoom: 0.55,
      maxZoom: 2,
      wheelSensitivity: 0.18,
      userPanningEnabled: true,
      userZoomingEnabled: true,
      boxSelectionEnabled: false,
    });

    cyRef.current = cy;

    setTimeout(() => {
      if (cyRef.current) {
        cyRef.current.resize();
        cyRef.current.fit(undefined, 60);
      }
    }, 50);

    return () => {
      cy.destroy();

      if (cyRef.current === cy) {
        cyRef.current = null;
      }
    };
  }, [result]);

  // =======================================================
  // RESET GRAPH
  // =======================================================

  function resetGraph() {
    if (!cyRef.current) return;

    cyRef.current.fit(undefined, 60);
    cyRef.current.center();
  }

  const hasTargets =
    (result?.shared_targets?.length || 0) > 0;

  const hasConditions =
    (result?.shared_conditions?.length || 0) > 0;

  const hasEvidence =
    hasTargets || hasConditions;

  return (
    <div className="graph-wrapper">
      <div className="graph-toolbar">
        <div className="graph-legend">
          <div>
            <span className="legend-shape drug-legend" />
            Medicine
          </div>

          {hasTargets && (
            <div>
              <span className="legend-shape target-legend" />
              Biological target
            </div>
          )}

          {!hasTargets && hasConditions && (
            <div>
              <span className="legend-shape condition-legend" />
              Shared indication
            </div>
          )}
        </div>

        <button
          className="reset-graph-button"
          onClick={resetGraph}
        >
          Reset view
        </button>
      </div>

      <div className="graph-canvas-wrap">
        <div
          ref={containerRef}
          className="cytoscape-container"
        />

        {!hasEvidence && (
          <div className="graph-empty-overlay">
            <div className="empty-path-icon">
              ?
            </div>

            <h3>
              No supported evidence path found
            </h3>

            <p>
              The current MedGraph dataset does not
              contain a shared biological target or
              shared indication for this medicine pair.
            </p>
          </div>
        )}
      </div>

      <div className="graph-caption">
        Drag nodes to explore • Scroll to zoom •
        Display limited to the most relevant represented
        evidence to keep the graph readable.
      </div>
    </div>
  );
}

export default GraphView;