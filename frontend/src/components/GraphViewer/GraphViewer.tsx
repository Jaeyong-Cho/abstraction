import { useRef } from 'react';
import { useCytoscape } from '../../hooks/useCytoscape';
import type { FunctionGraph } from '../../types';
import './GraphViewer.css';

interface GraphViewerProps {
  graphData: FunctionGraph | null;
  loading: boolean;
  error: string | null;
  onNodeClick: (functionKey: string) => void;
}

export function GraphViewer({
  graphData,
  loading,
  error,
  onNodeClick,
}: GraphViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  useCytoscape(containerRef as React.RefObject<HTMLDivElement>, graphData, onNodeClick);

  if (loading) {
    return (
      <div className="graph-container">
        <div className="graph-loading">Loading graph...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="graph-container">
        <div className="graph-error">Error: {error}</div>
      </div>
    );
  }

  if (!graphData) {
    return (
      <div className="graph-container">
        <div className="graph-empty">Select a function to view its call graph</div>
      </div>
    );
  }

  const centerNode = graphData.nodes.find((n) => n.isCenter);
  const title = centerNode
    ? `Call Graph: ${centerNode.label}`
    : 'Call Graph';

  return (
    <div className="graph-section">
      <h3 className="graph-title">{title}</h3>
      <div ref={containerRef} id="graph" className="graph-container" />
    </div>
  );
}
