import { useState, useEffect } from 'react';
import { FunctionTree } from './components/FunctionTree';
import { GraphViewer } from './components/GraphViewer';
import { CodeViewer } from './components/CodeViewer';
import { PredictionsPanel } from './components/PredictionsPanel';
import { SettingsModal } from './components/SettingsModal';
import { getFunctionGraph, getFunctionCode, getFunctionTree } from './api/client';
import type { FunctionGraph, FunctionCode } from './types';
import { useResizers } from './hooks/useResizers';
import './App.css';

function App() {
  const [selectedFunctionKey, setSelectedFunctionKey] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<FunctionGraph | null>(null);
  const [codeData, setCodeData] = useState<FunctionCode | null>(null);
  const [functionTree, setFunctionTree] = useState<any>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [codeLoading, setCodeLoading] = useState(false);
  const [graphError, setGraphError] = useState<string | null>(null);
  const [codeError, setCodeError] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useResizers();

  useEffect(() => {
    async function loadTree() {
      try {
        const data = await getFunctionTree();
        setFunctionTree(data.tree);
      } catch (error) {
        console.error('Failed to load function tree:', error);
      }
    }
    loadTree();
  }, []);

  useEffect(() => {
    if (!selectedFunctionKey) {
      setGraphData(null);
      setCodeData(null);
      return;
    }

    async function loadFunctionData() {
      setGraphLoading(true);
      setCodeLoading(true);
      setGraphError(null);
      setCodeError(null);

      try {
        const [graph, code] = await Promise.all([
          getFunctionGraph(selectedFunctionKey!).catch((err) => {
            setGraphError(err instanceof Error ? err.message : 'Failed to load graph');
            return null;
          }),
          getFunctionCode(selectedFunctionKey!).catch((err) => {
            setCodeError(err instanceof Error ? err.message : 'Failed to load code');
            return null;
          }),
        ]);

        if (graph) {
          setGraphData(graph);
          if (code && graph.nodes) {
            const graphNodeIds = new Set(graph.nodes.map((n) => n.id));
            const graphCallers = graph.nodes
              .filter((n) => n.id !== selectedFunctionKey && graphNodeIds.has(n.id) && n.level === 0)
              .map((n) => n.label);
            const graphCallees = graph.nodes
              .filter((n) => n.level === 2)
              .map((n) => n.label);
            setCodeData({
              ...code,
              graph_callers: graphCallers,
              graph_callees: graphCallees,
            });
          } else if (code) {
            setCodeData(code);
          }
        } else if (code) {
          setCodeData(code);
        }
      } finally {
        setGraphLoading(false);
        setCodeLoading(false);
      }
    }

    loadFunctionData();
  }, [selectedFunctionKey]);

  const handleSelectFunction = (functionKey: string) => {
    setSelectedFunctionKey(functionKey);
  };

  const handleNodeClick = (functionKey: string) => {
    setSelectedFunctionKey(functionKey);
  };

  const handleCodeFunctionClick = async (functionName: string) => {
    console.log('handleCodeFunctionClick called with:', functionName);
    
    if (graphData) {
      const node = graphData.nodes.find((n) => n.label === functionName);
      if (node) {
        console.log('Found node in graphData:', node.id);
        setSelectedFunctionKey(node.id);
        return;
      }
    }
    
    if (functionTree) {
      function findFunctionKey(tree: any, name: string, path: string = ''): string | null {
        for (const [key, value] of Object.entries(tree)) {
          const currentPath = path ? `${path}/${key}` : key;
          if (Array.isArray(value)) {
            const func = value.find((f: any) => f.name === name);
            if (func) {
              return func.key;
            }
          } else {
            const result = findFunctionKey(value as any, name, currentPath);
            if (result) {
              return result;
            }
          }
        }
        return null;
      }
      
      const foundKey = findFunctionKey(functionTree, functionName);
      if (foundKey) {
        console.log('Found function key in tree:', foundKey);
        setSelectedFunctionKey(foundKey);
        return;
      }
    }
    
    if (!selectedFunctionKey) {
      console.warn('No selected function key and function not found in tree');
      return;
    }
    
    try {
      const currentGraph = await getFunctionGraph(selectedFunctionKey);
      const node = currentGraph.nodes.find((n) => n.label === functionName);
      if (node) {
        console.log('Found node in fetched graph:', node.id);
        setSelectedFunctionKey(node.id);
      } else {
        console.warn('Function not found in graph:', functionName);
      }
    } catch (error) {
      console.error('Error fetching graph for function click:', error);
    }
  };

  const handleContractUpdate = () => {
    if (selectedFunctionKey) {
      handleSelectFunction(selectedFunctionKey);
    }
  };

  const handleIndexComplete = () => {
    window.location.reload();
  };

  return (
    <div className="app">
      <div className="header">
        <h1>Abstraction Level Tracker</h1>
        <button
          className="header-btn"
          onClick={() => setSettingsOpen(true)}
        >
          Settings
        </button>
      </div>

      <div className="container">
        <div className="sidebar">
          <h2>Functions</h2>
          <FunctionTree
            tree={functionTree}
            selectedFunctionKey={selectedFunctionKey}
            onSelectFunction={handleSelectFunction}
          />
        </div>
        <div className="sidebar-resizer"></div>

        <div className="main-content">
          <div className="predictions-section-wrapper">
            <PredictionsPanel
              functionKey={selectedFunctionKey}
              graphData={graphData}
              onContractUpdate={handleContractUpdate}
              onSelectFunction={handleSelectFunction}
            />
          </div>

          <div className="predictions-resizer"></div>

          <div className="right-panel">
            <CodeViewer
              codeData={codeData}
              loading={codeLoading}
              error={codeError}
              onFunctionClick={handleCodeFunctionClick}
            />

            <div className="code-graph-resizer"></div>

            <div className="graph-section">
              <GraphViewer
                graphData={graphData}
                loading={graphLoading}
                error={graphError}
                onNodeClick={handleNodeClick}
              />
            </div>
          </div>
        </div>
      </div>

      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onIndexComplete={handleIndexComplete}
      />
    </div>
  );
}

export default App;
