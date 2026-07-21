(function exposeDemoTabs(root, factory) {
  const controller = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = controller;
  } else {
    root.FounderOSDemoTabs = controller;
  }
}(typeof globalThis !== 'undefined' ? globalThis : this, function buildController() {
  'use strict';

  function initDemoTabs(documentRoot) {
    if (!documentRoot || typeof documentRoot.querySelectorAll !== 'function') {
      return null;
    }

    const tabs = [...documentRoot.querySelectorAll('[data-demo]')];
    const panels = [...documentRoot.querySelectorAll('[data-panel]')];

    function selectPanel(selected) {
      tabs.forEach((item) => {
        const isSelected = item.dataset.demo === selected;
        item.setAttribute('aria-selected', String(isSelected));
        item.tabIndex = isSelected ? 0 : -1;
      });

      panels.forEach((panel) => {
        const isSelected = panel.dataset.panel === selected;
        panel.classList.toggle('is-active', isSelected);
        panel.hidden = !isSelected;
      });
    }

    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => {
        selectPanel(tab.dataset.demo);
      });

      tab.addEventListener('keydown', (event) => {
        if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
        event.preventDefault();
        const direction = event.key === 'ArrowRight' ? 1 : -1;
        const next = (index + direction + tabs.length) % tabs.length;
        tabs[next].focus();
        tabs[next].click();
      });
    });

    const initialTab = tabs.find(
      (tab) => tab.getAttribute('aria-selected') === 'true',
    );
    if (initialTab) selectPanel(initialTab.dataset.demo);

    return { selectPanel };
  }

  return { initDemoTabs };
}));
