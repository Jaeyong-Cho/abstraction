import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  getFunctionContract,
  saveFunctionContract,
} from '../../api/client';
import type { FunctionContract, FunctionGraph } from '../../types';
import './PredictionsPanel.css';

interface PredictionsPanelProps {
  functionKey: string | null;
  graphData: FunctionGraph | null;
  onContractUpdate?: () => void;
  onSelectFunction?: (functionKey: string) => void;
}

export function PredictionsPanel({
  functionKey,
  graphData,
  onContractUpdate,
  onSelectFunction,
}: PredictionsPanelProps) {
  const [contract, setContract] = useState<FunctionContract | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditingExpectedBehavior, setIsEditingExpectedBehavior] = useState(false);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    expected_behavior: '',
    abstraction_level: 'medium',
  });
  
  const [expandedCallees, setExpandedCallees] = useState<Set<string>>(new Set());
  const [calleeContracts, setCalleeContracts] = useState<Map<string, FunctionContract>>(new Map());

  useEffect(() => {
    if (!functionKey) {
      setContract(null);
      setIsEditingExpectedBehavior(false);
      setExpandedCallees(new Set());
      setCalleeContracts(new Map());
      return;
    }
    
    setExpandedCallees(new Set());
    setCalleeContracts(new Map());
    setIsEditingExpectedBehavior(false);

    async function loadContract() {
      setLoading(true);
      setError(null);
      try {
        const data = await getFunctionContract(functionKey!);
        setContract(data);
        if (data) {
          const expectedBehavior = data.expected_behavior || 
            (data.input_prediction && data.output_prediction 
              ? `${data.input_prediction}\n\n${data.output_prediction}`
              : data.input_prediction || data.output_prediction || '');
          setFormData({
            expected_behavior: expectedBehavior,
            abstraction_level: data.abstraction_level || 'medium',
          });
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contract');
      } finally {
        setLoading(false);
      }
    }

    loadContract();
  }, [functionKey]);

  const handleSave = async () => {
    if (!functionKey) return;

    setSaving(true);
    setStatusMessage('Saving...');

    try {
      const saveData = {
        ...formData,
        expected_behavior: formData.expected_behavior,
      };
      const result = await saveFunctionContract(functionKey!, saveData);
      if (result.success) {
        setStatusMessage('Contract saved successfully!');
        setIsEditingExpectedBehavior(false);
        
        let updatedContract: FunctionContract | null = null;
        if (result.contract) {
          updatedContract = result.contract;
        } else {
          updatedContract = await getFunctionContract(functionKey!);
        }
        
        if (updatedContract) {
          setContract(updatedContract);
          const expectedBehavior = updatedContract.expected_behavior || 
            (updatedContract.input_prediction && updatedContract.output_prediction 
              ? `${updatedContract.input_prediction}\n\n${updatedContract.output_prediction}`
              : updatedContract.input_prediction || updatedContract.output_prediction || '');
          setFormData({
            expected_behavior: expectedBehavior,
            abstraction_level: updatedContract.abstraction_level || 'medium',
          });
        }
        
        if (onContractUpdate) {
          onContractUpdate();
        }
        setTimeout(() => setStatusMessage(null), 3000);
      } else {
        setStatusMessage(`Error: ${result.error || 'Failed to save'}`);
      }
    } catch (err) {
      setStatusMessage(
        `Error: ${err instanceof Error ? err.message : 'Failed to save'}`
      );
    } finally {
      setSaving(false);
    }
  };

  const handleCancelExpectedBehavior = () => {
    if (contract) {
      const expectedBehavior = contract.expected_behavior || 
        (contract.input_prediction && contract.output_prediction 
          ? `${contract.input_prediction}\n\n${contract.output_prediction}`
          : contract.input_prediction || contract.output_prediction || '');
      setFormData({
        expected_behavior: expectedBehavior,
        abstraction_level: contract.abstraction_level || 'medium',
      });
    }
    setIsEditingExpectedBehavior(false);
    setStatusMessage(null);
  };
  
  const handleSaveExpectedBehavior = async () => {
    if (!functionKey) return;

    setSaving(true);
    setStatusMessage('Saving...');

    try {
      const saveData = {
        expected_behavior: formData.expected_behavior,
        abstraction_level: formData.abstraction_level,
      };
      const result = await saveFunctionContract(functionKey!, saveData);
      if (result.success) {
        setStatusMessage('Contract saved successfully!');
        setIsEditingExpectedBehavior(false);
        
        let updatedContract: FunctionContract | null = null;
        if (result.contract) {
          updatedContract = result.contract;
        } else {
          updatedContract = await getFunctionContract(functionKey!);
        }
        
        if (updatedContract) {
          setContract(updatedContract);
          const expectedBehavior = updatedContract.expected_behavior || 
            (updatedContract.input_prediction && updatedContract.output_prediction 
              ? `${updatedContract.input_prediction}\n\n${updatedContract.output_prediction}`
              : updatedContract.input_prediction || updatedContract.output_prediction || '');
          setFormData({
            expected_behavior: expectedBehavior,
            abstraction_level: updatedContract.abstraction_level || 'medium',
          });
        }
        
        if (onContractUpdate) {
          onContractUpdate();
        }
        setTimeout(() => setStatusMessage(null), 3000);
      } else {
        setStatusMessage(`Error: ${result.error || 'Failed to save'}`);
      }
    } catch (err) {
      setStatusMessage(
        `Error: ${err instanceof Error ? err.message : 'Failed to save'}`
      );
    } finally {
      setSaving(false);
    }
  };
  
  const handleToggleCallee = async (calleeId: string) => {
    if (expandedCallees.has(calleeId)) {
      setExpandedCallees(prev => {
        const newSet = new Set(prev);
        newSet.delete(calleeId);
        return newSet;
      });
    } else {
      setExpandedCallees(prev => new Set(prev).add(calleeId));
      
      if (!calleeContracts.has(calleeId)) {
        try {
          const calleeContract = await getFunctionContract(calleeId);
          if (calleeContract) {
            setCalleeContracts(prev => {
              const newMap = new Map(prev);
              newMap.set(calleeId, calleeContract);
              return newMap;
            });
          }
        } catch (err) {
          console.error('Failed to load callee contract:', err);
        }
      }
    }
  };

  if (!functionKey) {
    return (
      <div className="predictions-section">
        <h3>Function Contract</h3>
        <div className="predictions-content">
          <div className="empty-state">
            <p>Select a function to view and edit its contract</p>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="predictions-section">
        <h3>Function Contract</h3>
        <div className="predictions-content">
          <div className="empty-state">Loading contract...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="predictions-section">
        <h3>Function Contract</h3>
        <div className="predictions-content">
          <div className="status error">Error: {error}</div>
        </div>
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="predictions-section">
        <h3>Function Contract</h3>
        <div className="predictions-content">
          <div className="empty-state">No contract found for this function</div>
          {graphData && onSelectFunction && (
            <div className="related-functions">
              {(() => {
                const callers = graphData.nodes.filter(
                  (n) => n.id !== functionKey && n.level === 0
                );
                const callees = graphData.nodes.filter((n) => n.level === 2);
                
                return (callers.length > 0 || callees.length > 0) ? (
                  <>
                    {callers.length > 0 && (
                      <div className="prediction-group">
                        <h4>Callers</h4>
                        <div className="function-list">
                          {callers.map((caller) => (
                            <div
                              key={caller.id}
                              className={`function-item ${caller.hasPredictions ? 'has-predictions' : ''}`}
                              onClick={() => onSelectFunction(caller.id)}
                            >
                              <span className="function-name">{caller.label}</span>
                              {caller.hasPredictions && (
                                <span className="predictions-badge">Contract</span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {callees.length > 0 && (
                      <div className="prediction-group">
                        <h4>Callees</h4>
                        <div className="function-list">
                          {callees.map((callee) => {
                            const isExpanded = expandedCallees.has(callee.id);
                            const calleeContract = calleeContracts.get(callee.id);
                            return (
                              <div key={callee.id}>
                                <div
                                  className={`function-item ${callee.hasPredictions ? 'has-predictions' : ''} ${isExpanded ? 'expanded' : ''}`}
                                  onClick={() => handleToggleCallee(callee.id)}
                                >
                                  <span className="function-name">{callee.label}</span>
                                  <div className="function-item-actions">
                                    {callee.hasPredictions && (
                                      <span className="predictions-badge">Contract</span>
                                    )}
                                    <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
                                  </div>
                                </div>
                                {isExpanded && calleeContract && (
                                  <div className="callee-contract">
                                    <div className="callee-contract-header">
                                      <strong>{calleeContract.name}</strong>
                                    </div>
                                    <div className="callee-contract-content markdown-content">
                                      {(() => {
                                        const expectedBehavior = calleeContract.expected_behavior || 
                                          (calleeContract.input_prediction && calleeContract.output_prediction 
                                            ? `${calleeContract.input_prediction}\n\n${calleeContract.output_prediction}`
                                            : calleeContract.input_prediction || calleeContract.output_prediction || '');
                                        return expectedBehavior ? (
                                          <ReactMarkdown>{expectedBehavior}</ReactMarkdown>
                                        ) : (
                                          <span className="empty-text">No expected behavior recorded</span>
                                        );
                                      })()}
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </>
                ) : null;
              })()}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
      <div className="predictions-section">
        <h3>Function Contract</h3>
        <div className="predictions-content">
          <div className="function-info">
            <div>
              <strong>Function:</strong> {contract.name}
            </div>
            <div>
              <strong>File:</strong> {contract.file_path}
            </div>
            <div>
              <strong>Line:</strong> {contract.line_number}
            </div>
            <div>
              <strong>Abstraction Level:</strong> {contract.abstraction_level}
            </div>
          </div>

          {statusMessage && (
            <div
              className={`status ${
                statusMessage.includes('Error') ? 'error' : 'success'
              }`}
            >
              {statusMessage}
            </div>
          )}

          <div className="prediction-group">
            <h4>Expected Behavior</h4>
            {!isEditingExpectedBehavior ? (
              <div
                className={`prediction-content markdown-content editable ${
                  contract.expected_behavior || contract.input_prediction || contract.output_prediction ? '' : 'empty'
                }`}
                onClick={() => setIsEditingExpectedBehavior(true)}
                title="Click to edit"
              >
                {(() => {
                  const expectedBehavior = contract.expected_behavior || 
                    (contract.input_prediction && contract.output_prediction 
                      ? `${contract.input_prediction}\n\n${contract.output_prediction}`
                      : contract.input_prediction || contract.output_prediction || '');
                  return expectedBehavior ? (
                    <ReactMarkdown>{expectedBehavior}</ReactMarkdown>
                  ) : (
                    <span className="empty-text">Click to add expected behavior</span>
                  );
                })()}
              </div>
            ) : (
              <div className="prediction-content editing">
                <textarea
                  value={formData.expected_behavior}
                  onChange={(e) =>
                    setFormData({ ...formData, expected_behavior: e.target.value })
                  }
                  onKeyDown={(e) => {
                    if (e.key === 'Escape') {
                      e.preventDefault();
                      handleCancelExpectedBehavior();
                    } else if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                      e.preventDefault();
                      handleSaveExpectedBehavior();
                    }
                  }}
                  placeholder="Describe the expected behavior of this function...&#10;&#10;Include inputs, outputs, side effects, etc.&#10;&#10;You can use **bold**, *italic*, `code`, lists, etc."
                  autoFocus
                  style={{
                    width: '100%',
                    minHeight: '150px',
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontFamily: 'Monaco, Menlo, Ubuntu Mono, monospace',
                    fontSize: '0.85rem',
                    lineHeight: '1.5',
                    resize: 'vertical',
                  }}
                />
                <div className="edit-actions">
                  <button
                    type="button"
                    onClick={handleSaveExpectedBehavior}
                    disabled={saving}
                    style={{ marginRight: '0.5rem' }}
                  >
                    {saving ? 'Saving...' : 'Save'}
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelExpectedBehavior}
                    style={{ background: '#95a5a6' }}
                  >
                    Cancel
                  </button>
                  <span className="edit-hint">Press Esc to cancel, Cmd/Ctrl+Enter to save</span>
                </div>
              </div>
            )}
          </div>

        {contract.preconditions && contract.preconditions.length > 0 && (
          <div className="prediction-group">
            <h4>Preconditions</h4>
            <div className="prediction-content markdown-content">
              <ul>
                {contract.preconditions.map((p, idx) => (
                  <li key={idx}>
                    <ReactMarkdown>{p}</ReactMarkdown>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {contract.postconditions && contract.postconditions.length > 0 && (
          <div className="prediction-group">
            <h4>Postconditions</h4>
            <div className="prediction-content markdown-content">
              <ul>
                {contract.postconditions.map((p, idx) => (
                  <li key={idx}>
                    <ReactMarkdown>{p}</ReactMarkdown>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {graphData && (
          <>
            {(() => {
              const callers = graphData.nodes.filter(
                (n) => n.id !== functionKey && n.level === 0
              );
              const callees = graphData.nodes.filter((n) => n.level === 2);
              
              return (callers.length > 0 || callees.length > 0) ? (
                <div className="related-functions">
                  {callers.length > 0 && (
                    <div className="prediction-group">
                      <h4>Callers</h4>
                      <div className="function-list">
                        {callers.map((caller) => (
                          <div
                            key={caller.id}
                            className={`function-item ${caller.hasPredictions ? 'has-predictions' : ''}`}
                            onClick={() => onSelectFunction?.(caller.id)}
                          >
                            <span className="function-name">{caller.label}</span>
                            {caller.hasPredictions && (
                              <span className="predictions-badge">Contract</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {callees.length > 0 && (
                    <div className="prediction-group">
                      <h4>Callees</h4>
                      <div className="function-list">
                        {callees.map((callee) => {
                          const isExpanded = expandedCallees.has(callee.id);
                          const calleeContract = calleeContracts.get(callee.id);
                          return (
                            <div key={callee.id}>
                              <div
                                className={`function-item ${callee.hasPredictions ? 'has-predictions' : ''} ${isExpanded ? 'expanded' : ''}`}
                                onClick={() => handleToggleCallee(callee.id)}
                              >
                                <span className="function-name">{callee.label}</span>
                                <div className="function-item-actions">
                                  {callee.hasPredictions && (
                                    <span className="predictions-badge">Contract</span>
                                  )}
                                  <button
                                    className="navigate-button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onSelectFunction?.(callee.id);
                                    }}
                                    title="Navigate to this function"
                                  >
                                    →
                                  </button>
                                  <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
                                </div>
                              </div>
                              {isExpanded && calleeContract && (
                                <div className="callee-contract">
                                  <div className="callee-contract-header">
                                    <strong>{calleeContract.name}</strong>
                                  </div>
                                  <div className="callee-contract-content markdown-content">
                                    {(() => {
                                      const expectedBehavior = calleeContract.expected_behavior || 
                                        (calleeContract.input_prediction && calleeContract.output_prediction 
                                          ? `${calleeContract.input_prediction}\n\n${calleeContract.output_prediction}`
                                          : calleeContract.input_prediction || calleeContract.output_prediction || '');
                                      return expectedBehavior ? (
                                        <ReactMarkdown>{expectedBehavior}</ReactMarkdown>
                                      ) : (
                                        <span className="empty-text">No expected behavior recorded</span>
                                      );
                                    })()}
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              ) : null;
            })()}
          </>
        )}
      </div>
    </div>
  );
}
