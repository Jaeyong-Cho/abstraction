import { useState, useEffect } from 'react';
import type { ReactElement } from 'react';
import type { FunctionTree, FunctionInfo } from '../../types';
import './FunctionTree.css';

interface FunctionTreeProps {
  tree: FunctionTree | null;
  selectedFunctionKey: string | null;
  onSelectFunction: (functionKey: string) => void;
}

interface CollapsedState {
  directories: Set<string>;
  files: Set<string>;
}

function initializeCollapsedState(
  tree: FunctionTree,
  path: string,
  state: CollapsedState
): void {
  Object.keys(tree).forEach((item) => {
    const itemPath = path ? `${path}/${item}` : item;
    const value = tree[item];
    if (!Array.isArray(value)) {
      state.directories.add(itemPath);
      initializeCollapsedState(value as FunctionTree, itemPath, state);
    }
  });
}

function renderTreeLevel(
  node: FunctionTree,
  path: string,
  depth: number,
  collapsedState: CollapsedState,
  selectedFunctionKey: string | null,
  onToggleDirectory: (dir: string) => void,
  onToggleFile: (fileKey: string) => void,
  onSelectFunction: (functionKey: string) => void
): ReactElement[] {
  const items = Object.keys(node).sort();
  const elements: ReactElement[] = [];

  items.forEach((item) => {
    const itemPath = path ? `${path}/${item}` : item;
    const value = node[item];

    if (Array.isArray(value)) {
      const fileKey = itemPath;
      const fileCollapsed = collapsedState.files.has(fileKey);
      const indent = depth * 1.5;

      elements.push(
        <div key={`file-${fileKey}`}>
          <div
            className={`tree-item file ${fileCollapsed ? 'collapsed' : ''}`}
            onClick={() => onToggleFile(fileKey)}
            style={{ paddingLeft: `${indent}rem` }}
          >
            <span className="fold-icon">▼</span>
            <span>{item}</span>
          </div>
          {!fileCollapsed && (
            <div className="tree-group">
              {value
                .sort((a, b) => a.line - b.line)
                .map((func: FunctionInfo) => {
                  const activeClass =
                    func.key === selectedFunctionKey ? 'active' : '';
                  const predictionClass = func.has_predictions
                    ? 'has-predictions'
                    : '';
                  return (
                    <div
                      key={func.key}
                      className={`tree-item function ${activeClass} ${predictionClass}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectFunction(func.key);
                      }}
                      style={{ paddingLeft: `${indent + 1.5}rem` }}
                    >
                      {func.name} (line {func.line})
                    </div>
                  );
                })}
            </div>
          )}
        </div>
      );
    } else {
      const dirCollapsed = collapsedState.directories.has(itemPath);
      const indent = depth * 1.5;

      elements.push(
        <div key={`dir-${itemPath}`}>
          <div
            className={`tree-item directory ${dirCollapsed ? 'collapsed' : ''}`}
            onClick={() => onToggleDirectory(itemPath)}
            style={{ paddingLeft: `${indent}rem` }}
          >
            <span className="fold-icon">▼</span>
            <span>{item}</span>
          </div>
          {!dirCollapsed && (
            <div className="tree-group">
              {renderTreeLevel(
                value as FunctionTree,
                itemPath,
                depth + 1,
                collapsedState,
                selectedFunctionKey,
                onToggleDirectory,
                onToggleFile,
                onSelectFunction
              )}
            </div>
          )}
        </div>
      );
    }
  });

  return elements;
}

export function FunctionTree({
  tree,
  selectedFunctionKey,
  onSelectFunction,
}: FunctionTreeProps) {
  const [collapsedState, setCollapsedState] = useState<CollapsedState>({
    directories: new Set(),
    files: new Set(),
  });
  const [treeInitialized, setTreeInitialized] = useState(false);

  useEffect(() => {
    if (!treeInitialized && tree) {
      const newState: CollapsedState = {
        directories: new Set(),
        files: new Set(),
      };
      initializeCollapsedState(tree, '', newState);
      setCollapsedState(newState);
      setTreeInitialized(true);
    }
  }, [tree, treeInitialized]);

  const handleToggleDirectory = (dir: string) => {
    setCollapsedState((prev) => {
      const newState = {
        directories: new Set(prev.directories),
        files: new Set(prev.files),
      };
      if (newState.directories.has(dir)) {
        newState.directories.delete(dir);
      } else {
        newState.directories.add(dir);
      }
      return newState;
    });
  };

  const handleToggleFile = (fileKey: string) => {
    setCollapsedState((prev) => {
      const newState = {
        directories: new Set(prev.directories),
        files: new Set(prev.files),
      };
      if (newState.files.has(fileKey)) {
        newState.files.delete(fileKey);
      } else {
        newState.files.add(fileKey);
      }
      return newState;
    });
  };

  if (!tree) {
    return <div className="empty-state">Loading functions...</div>;
  }

  if (Object.keys(tree).length === 0) {
    return <div className="empty-state">No functions found</div>;
  }

  return (
    <div className="function-tree">
      {renderTreeLevel(
        tree,
        '',
        0,
        collapsedState,
        selectedFunctionKey,
        handleToggleDirectory,
        handleToggleFile,
        onSelectFunction
      )}
    </div>
  );
}
