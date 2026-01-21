import { useState, useEffect } from 'react';
import { getWorkspace, setWorkspace, indexWorkspace } from '../../api/client';
import './SettingsModal.css';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIndexComplete?: () => void;
}

export function SettingsModal({
  isOpen,
  onClose,
  onIndexComplete,
}: SettingsModalProps) {
  const [workspacePath, setWorkspacePath] = useState('');
  const [workspaceStatus, setWorkspaceStatus] = useState<string | null>(null);
  const [indexStatus, setIndexStatus] = useState<string | null>(null);
  const [indexing, setIndexing] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadCurrentWorkspace();
    }
  }, [isOpen]);

  async function loadCurrentWorkspace() {
    try {
      const data = await getWorkspace();
      setWorkspacePath(data.workspace || '');
    } catch (error) {
      setWorkspaceStatus(
        `Error loading workspace: ${
          error instanceof Error ? error.message : 'Unknown error'
        }`
      );
    }
  }

  async function handleSaveWorkspace() {
    const path = workspacePath.trim();
    if (!path) {
      setWorkspaceStatus('Please enter a workspace path');
      return;
    }

    setWorkspaceStatus('Saving workspace...');

    try {
      const data = await setWorkspace(path);
      if (data.success) {
        setWorkspaceStatus('Workspace saved. Indexing...');
        console.log('Workspace saved:', data.workspace);
        await handleIndex();
      } else {
        setWorkspaceStatus(`Error: ${data.error || 'Failed to save workspace'}`);
      }
    } catch (error) {
      setWorkspaceStatus(
        `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async function handleIndex() {
    const path = workspacePath.trim();
    if (!path) {
      setIndexStatus('Please set and save workspace path first');
      return;
    }

    setIndexing(true);
    setIndexStatus('Indexing workspace... Please wait.');

    try {
      const data = await indexWorkspace();
      if (data.success) {
        setIndexStatus(
          data.message || `Indexed ${data.count || 0} functions`
        );
        if (onIndexComplete) {
          onIndexComplete();
        }
      } else {
        setIndexStatus(`Error: ${data.error || 'Failed to index workspace'}`);
      }
    } catch (error) {
      setIndexStatus(
        `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    } finally {
      setIndexing(false);
    }
  }

  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal show" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Workspace Settings</h2>
          <span className="modal-close" onClick={onClose}>
            &times;
          </span>
        </div>
        <div className="modal-body">
          <div className="form-group">
            <label htmlFor="workspace-path">Workspace Path</label>
            <input
              type="text"
              id="workspace-path"
              value={workspacePath}
              onChange={(e) => setWorkspacePath(e.target.value)}
              placeholder="Enter workspace directory path"
            />
            <small>
              Absolute or relative path to your source code directory
            </small>
          </div>
          {workspaceStatus && (
            <div
              className={`status-info ${
                workspaceStatus.includes('Error') ? 'error' : 'success'
              }`}
            >
              {workspaceStatus}
            </div>
          )}
          <div className="modal-actions">
            <button
              className="btn-primary"
              onClick={handleSaveWorkspace}
              disabled={indexing}
            >
              Save Workspace
            </button>
            <button
              className="btn-primary"
              onClick={handleIndex}
              disabled={indexing}
            >
              Index Workspace
            </button>
            <button className="btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
          {indexStatus && (
            <div
              className={`status-info ${
                indexStatus.includes('Error') ? 'error' : 'success'
              }`}
            >
              {indexStatus}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
