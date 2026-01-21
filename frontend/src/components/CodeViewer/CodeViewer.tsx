import { useMemo, useEffect, useRef } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { FunctionCode } from '../../types';
import './CodeViewer.css';

interface CodeViewerProps {
  codeData: FunctionCode | null;
  loading: boolean;
  error: string | null;
  onFunctionClick?: (functionName: string) => void;
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function CodeViewer({
  codeData,
  loading,
  error,
  onFunctionClick,
}: CodeViewerProps) {
  const codeRef = useRef<HTMLDivElement>(null);

  const customStyle = useMemo(
    () => ({
      ...oneLight,
      'pre[class*="language-"]': {
        ...oneLight['pre[class*="language-"]'],
        background: '#fafafa',
        margin: 0,
        padding: '1rem 0',
      },
      'code[class*="language-"]': {
        ...oneLight['code[class*="language-"]'],
        background: 'transparent',
        color: '#383a42',
      },
    }),
    []
  );

  useEffect(() => {
    if (!codeRef.current || !codeData) {
      return;
    }

    console.log('CodeViewer effect - codeData:', {
      hasCode: !!codeData.code,
      graphCallers: codeData.graph_callers?.length || 0,
      graphCallees: codeData.graph_callees?.length || 0,
      callers: codeData.callers?.length || 0,
      callees: codeData.callees?.length || 0,
      functionName: codeData.function_name,
    });

    const graphCallers = codeData.graph_callers || [];
    const graphCallees = codeData.graph_callees || [];
    const functionName = codeData.function_name || '';
    const codeLines = (codeData.code || '').split('\n');

    console.log('Processing:', {
      graphCallers,
      graphCallees,
      functionName,
      codeLinesCount: codeLines.length,
    });

    const processCode = () => {
      const codeElement = codeRef.current?.querySelector('pre code');
      if (!codeElement) {
        console.log('Code element not found');
        return false;
      }

      const fullText = codeElement.textContent || '';
      console.log('Code element found, full text length:', fullText.length);
      console.log('Looking for callees:', graphCallees);
      console.log('Looking for callers:', graphCallers);

      let highlighted = false;
      let clickable = false;

      const allSpans = codeElement.querySelectorAll('span');
      console.log('Found spans:', allSpans.length);

      codeLines.forEach((line, lineIndex) => {
        const trimmedLine = line.trim();
        if (!trimmedLine) return;
        
        const isFunctionDef =
          functionName &&
          (trimmedLine.startsWith('def ' + functionName + '(') ||
            trimmedLine.startsWith('function ' + functionName + '(') ||
            trimmedLine.match(
              new RegExp(
                '^\\s*(public|private|static)?\\s*\\w+\\s+' +
                  functionName +
                  '\\s*\\('
              )
            ));

        const hasCaller = graphCallers.some((caller) => {
          const regex = new RegExp('\\b' + escapeRegex(caller) + '\\s*\\(', 'g');
          return regex.test(line);
        });

        const hasCallee = graphCallees.some((callee) => {
          const regex = new RegExp('\\b' + escapeRegex(callee) + '\\s*\\(', 'g');
          return regex.test(line);
        });

        if (!isFunctionDef && !hasCaller && !hasCallee) return;

        const lineKey = trimmedLine.substring(0, Math.min(20, trimmedLine.length));
        console.log(`Processing line ${lineIndex}: ${lineKey}...`, { isFunctionDef, hasCaller, hasCallee });

        if (isFunctionDef) {
          const functionDefRegex = new RegExp('\\b(def|function)\\s+(' + escapeRegex(functionName) + ')\\s*\\(', 'g');
          const walker = document.createTreeWalker(
            codeElement,
            NodeFilter.SHOW_TEXT,
            null
          );
          
          let textNode: Node | null;
          while ((textNode = walker.nextNode())) {
            const text = textNode.textContent || '';
            if (!text.includes(functionName)) continue;
            
            const matches = Array.from(text.matchAll(functionDefRegex));
            if (matches.length === 0) continue;
            
            const parent = textNode.parentElement;
            if (!parent) continue;
            if (parent.classList.contains('highlight-function')) continue;
            
            const fragment = document.createDocumentFragment();
            let lastIndex = 0;
            
            matches.forEach((match) => {
              if (match.index === undefined) return;
              
              if (match.index > lastIndex) {
                fragment.appendChild(
                  document.createTextNode(text.slice(lastIndex, match.index))
                );
              }
              
              fragment.appendChild(document.createTextNode(match[1] + ' '));
              
              const highlightSpan = document.createElement('span');
              highlightSpan.className = 'highlight-function';
              highlightSpan.textContent = match[2];
              fragment.appendChild(highlightSpan);
              
              fragment.appendChild(document.createTextNode('('));
              
              lastIndex = match.index + match[0].length;
            });
            
            if (lastIndex < text.length) {
              fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
            }
            
            try {
              parent.replaceChild(fragment, textNode);
              highlighted = true;
              console.log(`✓ Highlighted function def "${functionName}"`);
            } catch (e) {
              console.error('Error highlighting function def:', e);
            }
          }
        } else if (hasCaller) {
          graphCallers.forEach((caller) => {
            const callerRegex = new RegExp('\\b(' + escapeRegex(caller) + ')\\s*\\(', 'g');
            const walker = document.createTreeWalker(
              codeElement,
              NodeFilter.SHOW_TEXT,
              null
            );
            
            let textNode: Node | null;
            while ((textNode = walker.nextNode())) {
              const text = textNode.textContent || '';
              if (!text.includes(caller)) continue;
              
              const matches = Array.from(text.matchAll(callerRegex));
              if (matches.length === 0) continue;
              
              const parent = textNode.parentElement;
              if (!parent) continue;
              if (parent.classList.contains('highlight-caller') || parent.classList.contains('clickable-callee')) continue;
              
              const fragment = document.createDocumentFragment();
              let lastIndex = 0;
              
              matches.forEach((match) => {
                if (match.index === undefined) return;
                
                if (match.index > lastIndex) {
                  fragment.appendChild(
                    document.createTextNode(text.slice(lastIndex, match.index))
                  );
                }
                
                const highlightSpan = document.createElement('span');
                highlightSpan.className = 'highlight-caller';
                highlightSpan.textContent = match[1];
                fragment.appendChild(highlightSpan);
                
                fragment.appendChild(document.createTextNode('('));
                
                lastIndex = match.index + match[0].length;
              });
              
              if (lastIndex < text.length) {
                fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
              }
              
              try {
                parent.replaceChild(fragment, textNode);
                highlighted = true;
                console.log(`✓ Highlighted caller "${caller}"`);
              } catch (e) {
                console.error('Error highlighting caller:', e);
              }
            }
          });
        }
      });

      if (onFunctionClick && graphCallees.length > 0) {
        graphCallees.forEach((callee) => {
          console.log(`Looking for callee: ${callee}`);
          
          const walker = document.createTreeWalker(
            codeElement,
            NodeFilter.SHOW_TEXT,
            null
          );

          const textNodes: Text[] = [];
          let textNode: Node | null;
          while ((textNode = walker.nextNode())) {
            const text = textNode.textContent || '';
            if (text.includes(callee) && !textNode.parentElement?.classList.contains('clickable-callee') && 
                !textNode.parentElement?.classList.contains('highlight-callee')) {
              textNodes.push(textNode as Text);
            }
          }

          console.log(`Found ${textNodes.length} text nodes containing "${callee}"`);

          textNodes.forEach((textNode, idx) => {
            const parent = textNode.parentElement;
            if (!parent) return;
            if (parent.classList.contains('clickable-callee')) return;
            if (parent.closest('.clickable-callee')) return;
            if (parent.classList.contains('highlight-callee')) return;

            const text = textNode.textContent || '';
            
            const patterns = [
              new RegExp('\\b(' + escapeRegex(callee) + ')\\s*\\(', 'g'),
              new RegExp('\\b(' + escapeRegex(callee) + ')\\b', 'g'),
            ];

            let matches: RegExpMatchArray[] = [];
            let usedPattern: RegExp | null = null;

            for (const pattern of patterns) {
              const testMatches = Array.from(text.matchAll(pattern));
              if (testMatches.length > 0) {
                matches = testMatches;
                usedPattern = pattern;
                break;
              }
            }

            if (matches.length === 0) {
              console.log(`Text node ${idx}: no matches in text: "${text.substring(0, 80)}"`);
              return;
            }

            console.log(`Text node ${idx}: found ${matches.length} matches with pattern`);

            const fragment = document.createDocumentFragment();
            let lastIndex = 0;

            matches.forEach((match) => {
              if (match.index === undefined) return;

              if (match.index > lastIndex) {
                fragment.appendChild(
                  document.createTextNode(text.slice(lastIndex, match.index))
                );
              }

              const span = document.createElement('span');
              span.className = 'clickable-callee highlight-callee';
              span.textContent = match[1];
              span.style.cursor = 'pointer';
              span.style.textDecoration = 'underline';
              span.style.color = '#1b5e20';
              span.style.fontWeight = '700';
              span.style.backgroundColor = 'rgba(76, 175, 80, 0.15)';
              span.style.padding = '2px 4px';
              span.style.borderRadius = '3px';
              span.style.display = 'inline';
              span.onclick = (e) => {
                e.stopPropagation();
                e.preventDefault();
                console.log('Clicking callee function:', callee);
                onFunctionClick(callee);
              };

              fragment.appendChild(span);
              
              if (usedPattern?.source.includes('\\s*\\(')) {
                fragment.appendChild(document.createTextNode('('));
              }

              lastIndex = match.index + match[0].length;
            });

            if (lastIndex < text.length) {
              fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
            }

            try {
              parent.replaceChild(fragment, textNode);
              clickable = true;
              highlighted = true;
              console.log(`✓ Made callee "${callee}" clickable and highlighted`);
            } catch (e) {
              console.error('Error replacing node:', e, {
                parent: parent.tagName,
                parentClasses: parent.className,
                textNodeLength: text.length,
                textPreview: text.substring(0, 80),
              });
            }
          });
        });
      }

      console.log('Process result:', { highlighted, clickable });
      return highlighted || clickable;
    };

    let attempts = 0;
    const maxAttempts = 10;
    let timeoutId: NodeJS.Timeout | null = null;
    let processedSuccessfully = false;

    const tryProcess = () => {
      if (processedSuccessfully) return;
      
      attempts++;
      console.log(`Attempt ${attempts} to process code`);
      const processed = processCode();

      if (processed) {
        processedSuccessfully = true;
        timeoutId = null;
        console.log('Code processing completed successfully');
      } else if (attempts < maxAttempts) {
        timeoutId = setTimeout(tryProcess, 200);
      } else {
        timeoutId = null;
        console.warn('Code processing failed after max attempts');
        console.log('Final state:', {
          codeElement: !!codeRef.current?.querySelector('pre code'),
          graphCallees,
          graphCallers,
          codeLines: codeLines.length,
        });
      }
    };

    const observer = new MutationObserver(() => {
      if (!processedSuccessfully && attempts < maxAttempts && !timeoutId) {
        attempts = 0;
        timeoutId = setTimeout(tryProcess, 100);
      }
    });

    if (codeRef.current) {
      observer.observe(codeRef.current, {
        childList: true,
        subtree: true,
        characterData: true,
      });
    }

    timeoutId = setTimeout(tryProcess, 300);

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      observer.disconnect();
    };
  }, [codeData, onFunctionClick]);

  if (loading) {
    return (
      <div className="code-viewer">
        <div className="code-content">
          <div className="empty-state">Loading code...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="code-viewer">
        <div className="code-content">
          <div className="status error">Error: {error}</div>
        </div>
      </div>
    );
  }

  if (!codeData) {
    return (
      <div className="code-viewer">
        <div className="code-content">
          <div className="empty-state">
            Select a function to view its source code
          </div>
        </div>
      </div>
    );
  }

  const language =
    codeData.language === 'python'
      ? 'python'
      : codeData.language === 'c'
        ? 'c'
        : codeData.language === 'cpp'
          ? 'cpp'
          : 'text';

  return (
    <div className="code-viewer">
      <div className="code-content" ref={codeRef}>
        <SyntaxHighlighter
          language={language}
          style={customStyle}
          customStyle={{
            margin: 0,
            padding: '1rem 0',
            background: 'transparent',
          }}
          codeTagProps={{
            style: {
              fontFamily: "'Monaco', 'Menlo', 'Ubuntu Mono', monospace",
              fontSize: '13px',
            },
          }}
        >
          {codeData.code || ''}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}
