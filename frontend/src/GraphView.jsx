import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

function GraphView({ result }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !result?.graph) return;

    const nodes = result.graph.nodes.map((node) => ({
      data: {
        id: String(node.id),
        label: node.name,
        type: node.type,
      },
    }));

    const edges = result.graph.edges.map((edge, index) => ({
      data: {
        id: `edge-${index}`,
        source: String(edge.source),
        target: String(edge.target),
        label: edge.relationship || "",
      },
    }));

    const cy = cytoscape({
      container: containerRef.current,

      elements: [...nodes, ...edges],

      style: [
        // DRUG NODES
        {
          selector: 'node[type="drug"]',
          style: {
            "background-color": "#2563eb",
            label: "data(label)",
            color: "#172033",
            "font-size": "13px",
            "font-weight": "600",
            "text-valign": "bottom",
            "text-margin-y": 10,
            "text-wrap": "wrap",
            "text-max-width": "120px",
            width: 65,
            height: 65,
            "border-width": 3,
            "border-color": "#bfdbfe",
          },
        },

        // BIOLOGICAL TARGET NODES
        {
          selector: 'node[type="target"]',
          style: {
            "background-color": "#16a34a",
            shape: "diamond",
            label: "data(label)",
            color: "#172033",
            "font-size": "13px",
            "font-weight": "600",
            "text-valign": "bottom",
            "text-margin-y": 12,
            "text-wrap": "wrap",
            "text-max-width": "130px",
            width: 75,
            height: 75,
            "border-width": 3,
            "border-color": "#bbf7d0",
          },
        },

        // EDGES
        {
          selector: "edge",
          style: {
            width: 3,
            "line-color": "#64748b",
            "target-arrow-color": "#64748b",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",

            label: "data(label)",
            color: "#334155",
            "font-size": "10px",
            "font-weight": "600",

            "text-background-color": "#ffffff",
            "text-background-opacity": 1,
            "text-background-padding": "5px",
          },
        },

        // SELECTED NODE
        {
          selector: "node:selected",
          style: {
            "border-width": 5,
            "border-color": "#f59e0b",
          },
        },
      ],

      layout: {
        name: "breadthfirst",
        directed: true,
        spacingFactor: 1.8,
        padding: 60,
      },

      minZoom: 0.5,
      maxZoom: 2,
      wheelSensitivity: 0.2,
    });

    cy.resize();
    cy.fit(undefined, 60);

    return () => {
      cy.destroy();
    };
  }, [result]);

  return (
    <div className="graph-wrapper">
      <div className="graph-legend">
        <div>
          <span className="legend-dot drug-dot"></span>
          Medicine
        </div>

        <div>
          <span className="legend-diamond target-dot"></span>
          Biological Target
        </div>

        <div className="graph-help">
          Scroll to zoom • Drag to explore
        </div>
      </div>

      <div
        ref={containerRef}
        className="cytoscape-container"
      />
    </div>
  );
}

export default GraphView;