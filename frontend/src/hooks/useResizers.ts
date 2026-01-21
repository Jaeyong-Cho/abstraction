import { useEffect } from 'react';

export function useResizers() {
  useEffect(() => {
    const sidebar = document.querySelector('.sidebar') as HTMLElement;
    const sidebarResizer = document.querySelector('.sidebar-resizer') as HTMLElement;
    const predictionsWrapper = document.querySelector('.predictions-section-wrapper') as HTMLElement;
    const predictionsResizer = document.querySelector('.predictions-resizer') as HTMLElement;
    const codeViewer = document.querySelector('.code-viewer') as HTMLElement;
    const graphSection = document.querySelector('.graph-section') as HTMLElement;
    const codeGraphResizer = document.querySelector('.code-graph-resizer') as HTMLElement;

    if (!sidebar || !sidebarResizer || !predictionsWrapper || !predictionsResizer || 
        !codeViewer || !graphSection || !codeGraphResizer) {
      return;
    }

    let isResizingSidebar = false;
    let isResizingPredictions = false;
    let isResizingCodeGraph = false;

    const handleSidebarMouseDown = (e: MouseEvent) => {
      isResizingSidebar = true;
      sidebarResizer.classList.add('dragging');
      document.body.style.cursor = 'col-resize';
      e.preventDefault();
    };

    const handlePredictionsMouseDown = (e: MouseEvent) => {
      isResizingPredictions = true;
      predictionsResizer.classList.add('dragging');
      document.body.style.cursor = 'col-resize';
      e.preventDefault();
    };

    const handleCodeGraphMouseDown = (e: MouseEvent) => {
      isResizingCodeGraph = true;
      codeGraphResizer.classList.add('dragging');
      document.body.style.cursor = 'row-resize';
      e.preventDefault();
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (isResizingSidebar) {
        const newWidth = e.clientX;
        if (newWidth >= 200 && newWidth <= 600) {
          sidebar.style.width = newWidth + 'px';
        }
      }

      if (isResizingPredictions) {
        const mainContent = document.querySelector('.main-content') as HTMLElement;
        if (mainContent) {
          const mainContentRect = mainContent.getBoundingClientRect();
          const sidebarRect = sidebar.getBoundingClientRect();
          const sidebarWidth = sidebarRect.width;
          const predictionsWidth = e.clientX - sidebarRect.right;
          const remainingWidth = mainContentRect.width - sidebarWidth - predictionsWidth;
          const mainContentWidth = mainContentRect.width - sidebarWidth;

          if (predictionsWidth >= 300 && remainingWidth >= 300) {
            const percentage = (predictionsWidth / mainContentWidth) * 100;
            predictionsWrapper.style.width = percentage + '%';
          }
        }
      }

      if (isResizingCodeGraph) {
        const rightPanel = document.querySelector('.right-panel') as HTMLElement;
        if (rightPanel) {
          const rightPanelRect = rightPanel.getBoundingClientRect();
          const codeHeight = e.clientY - rightPanelRect.top;
          const graphHeight = rightPanelRect.height - codeHeight;

          if (codeHeight >= 200 && graphHeight >= 200) {
            codeViewer.style.flex = '0 0 ' + codeHeight + 'px';
            graphSection.style.flex = '1 1 ' + graphHeight + 'px';
          }
        }
      }
    };

    const handleMouseUp = () => {
      if (isResizingSidebar) {
        isResizingSidebar = false;
        sidebarResizer.classList.remove('dragging');
        document.body.style.cursor = '';
      }

      if (isResizingPredictions) {
        isResizingPredictions = false;
        predictionsResizer.classList.remove('dragging');
        document.body.style.cursor = '';
      }

      if (isResizingCodeGraph) {
        isResizingCodeGraph = false;
        codeGraphResizer.classList.remove('dragging');
        document.body.style.cursor = '';
      }
    };

    sidebarResizer.addEventListener('mousedown', handleSidebarMouseDown);
    predictionsResizer.addEventListener('mousedown', handlePredictionsMouseDown);
    codeGraphResizer.addEventListener('mousedown', handleCodeGraphMouseDown);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      sidebarResizer.removeEventListener('mousedown', handleSidebarMouseDown);
      predictionsResizer.removeEventListener('mousedown', handlePredictionsMouseDown);
      codeGraphResizer.removeEventListener('mousedown', handleCodeGraphMouseDown);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);
}
