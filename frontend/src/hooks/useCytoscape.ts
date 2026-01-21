import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import elk from 'cytoscape-elk';
import type { FunctionGraph, GraphNode } from '../types';

try {
  cytoscape.use(elk);
} catch (e) {
  console.warn('Failed to register cytoscape-elk:', e);
}

function getCytoscapeNodeColor(node: GraphNode, level: number | undefined) {
  if (node.isCenter) {
    return {
      background: 'rgba(52, 152, 219, 0.15)',
      border: '#2980b9',
    };
  }

  if (level === 0) {
    return {
      background: 'rgba(231, 76, 60, 0.15)',
      border: 'rgba(192, 57, 43, 0.7)',
    };
  }

  if (level === 2) {
    return {
      background: 'rgba(46, 204, 113, 0.15)',
      border: 'rgba(39, 174, 96, 0.7)',
    };
  }

  if (node.hasPredictions) {
    return {
      background: 'rgba(46, 204, 113, 0.2)',
      border: '#27ae60',
    };
  } else if (node.hasContract) {
    return {
      background: 'rgba(243, 156, 18, 0.2)',
      border: '#e67e22',
    };
  } else {
    return {
      background: 'rgba(236, 240, 241, 0.3)',
      border: '#bdc3c7',
    };
  }
}

export function useCytoscape(
  containerRef: React.RefObject<HTMLDivElement>,
  graphData: FunctionGraph | null,
  onNodeClick: (functionKey: string) => void
): cytoscape.Core | null {
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current || !graphData) {
      return;
    }

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const elements: cytoscape.ElementDefinition[] = [];

    graphData.nodes.forEach((node) => {
      const labelLength = node.label.length;
      const width = Math.max(120, Math.min(250, labelLength * 8 + 40));
      const height = node.isCenter ? 60 : 50;
      const color = getCytoscapeNodeColor(node, node.level);

      elements.push({
        data: {
          id: node.id,
          label: node.label,
          width: width,
          height: height,
          level: node.level !== undefined ? node.level : 1,
          isCenter: node.isCenter || false,
          hasPredictions: node.hasPredictions || false,
          hasContract: node.hasContract || false,
          backgroundColor: color.background,
          borderColor: color.border,
          borderWidth: node.isCenter ? 4 : 2,
        },
      });
    });

    const nodeIds = new Set(graphData.nodes.map((n) => n.id));

    graphData.edges.forEach((edge) => {
      if (nodeIds.has(edge.from) && nodeIds.has(edge.to)) {
        elements.push({
          data: {
            id: `${edge.from}-${edge.to}`,
            source: edge.from,
            target: edge.to,
          },
        });
      }
    });

    const centerNodeIds = graphData.nodes
      .filter((n) => n.isCenter)
      .map((n) => n.id);

    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'overlay-opacity': 0,
            'background-color': 'data(backgroundColor)',
            'background-opacity': 1,
            opacity: 1,
            'border-color': 'data(borderColor)',
            'border-width': 'data(borderWidth)',
            width: 'data(width)',
            height: 'data(height)',
            label: 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': (ele: cytoscape.NodeSingular) => (ele.data('isCenter') ? '14px' : '12px'),
            'font-weight': (ele: cytoscape.NodeSingular) => (ele.data('isCenter') ? 'bold' : 'normal'),
            'font-family': 'monospace',
            shape: 'round-rectangle',
            'text-wrap': 'wrap',
            'text-max-width': (ele: cytoscape.NodeSingular) => String(ele.data('width') - 20),
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#3498db',
            'border-width': 4,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2.5,
            'line-color': '#7f8c8d',
            'target-arrow-color': '#7f8c8d',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 1.2,
          },
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#3498db',
            'target-arrow-color': '#3498db',
            width: 3,
          },
        },
      ],
      layout: {
        name: 'breadthfirst',
        directed: true,
        roots: centerNodeIds.length > 0 ? centerNodeIds : undefined,
        spacingFactor: 1.5,
        padding: 50,
      },
    });

    cyRef.current = cy;

    cy.ready(async () => {
      if (cy.nodes().length === 0) {
        console.warn('No nodes to layout');
        return;
      }

      let useElkLayout = false;
      try {
        const testLayout = cy.layout({ name: 'elk' });
        if (testLayout) {
          useElkLayout = true;
        }
      } catch (e) {
        console.warn('ELK layout not available, using breadthfirst');
      }

      if (useElkLayout) {
        try {
          const layout = cy.layout({
            name: 'elk',
            // @ts-ignore - cytoscape-elk extends layout options
            elk: {
              algorithm: 'layered',
              'elk.direction': 'RIGHT',
              'elk.layered.spacing.nodeNodeBetweenLayers': '300',
              'elk.spacing.nodeNode': '250',
              'elk.layered.nodePlacement.strategy': 'BRANDES_KOEPF',
              'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
              'elk.insideSelfLoops.activate': 'true',
              'elk.spacing.edgeNode': '50',
              'elk.spacing.edgeEdge': '20',
              'elk.spacing.edgeNodeBetweenLayers': '50',
              'elk.layered.spacing.edgeNodeBetweenLayers': '50',
              'elk.layered.spacing.edgeEdgeBetweenLayers': '20',
              'elk.portAlignment.basic': 'JUSTIFIED',
              'elk.nodeSize.constraints': 'MINIMUM_SIZE',
              'elk.nodeSize.minimum': '120 50',
              'elk.nodeSize.options': 'DEFAULT_MINIMUM_SIZE',
            },
          });
          layout.run();
        } catch (error) {
          console.error('ELK layout error:', error);
          cy.layout({ name: 'breadthfirst', directed: true }).run();
        }
      } else {
        cy.layout({ name: 'breadthfirst', directed: true, spacingFactor: 1.5 }).run();
      }
    });

    cy.on('tap', 'node', () => {
      const clickedNodeId = cy.$('node:selected').id();
      if (clickedNodeId) {
        onNodeClick(clickedNodeId);
      }
    });

    cy.on('mouseover', 'node', (evt) => {
      if (!evt.target.selected()) {
        evt.target.style('border-color', '#3498db');
        evt.target.style('border-width', 3);
      }
    });

    cy.on('mouseout', 'node', (evt) => {
      if (!evt.target.selected()) {
        const nodeData = evt.target.data();
        evt.target.style('border-color', nodeData.borderColor);
        evt.target.style('border-width', nodeData.borderWidth);
      }
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [containerRef, graphData, onNodeClick]);

  return cyRef.current;
}
