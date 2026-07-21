(function exposeWorkflowLibrary(root, factory) {
  const controller = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = controller;
  } else {
    root.FounderOSWorkflowLibrary = controller;
  }
}(typeof globalThis !== 'undefined' ? globalThis : this, function buildController() {
  'use strict';

  function initWorkflowLibrary(documentRoot) {
    if (!documentRoot || typeof documentRoot.querySelector !== 'function') {
      return null;
    }

    const catalogue = documentRoot.querySelector('#workflow-catalogue');
    const search = documentRoot.querySelector('#workflow-search');
    const count = documentRoot.querySelector('#workflow-count');
    const empty = documentRoot.querySelector('#workflow-empty');
    const filterLinks = [
      ...documentRoot.querySelectorAll(
        '.workflow-entry[data-workflow-filter]',
      ),
    ];
    const clearFilter = documentRoot.querySelector(
      '[data-clear-workflow-filter]',
    );
    const showAll = documentRoot.querySelector('[data-show-all-workflows]');
    const groups = [
      ...documentRoot.querySelectorAll('[data-workflow-group]'),
    ];
    const workflows = [...documentRoot.querySelectorAll('[data-workflow]')];
    let activeCategory = 'all';

    function update({ closeGroups = false } = {}) {
      const query = search?.value.trim().toLowerCase() || '';
      const filtering = activeCategory !== 'all' || Boolean(query);
      let visibleCount = 0;

      groups.forEach((group) => {
        const categoryMatches = activeCategory === 'all'
          || group.dataset.category === activeCategory;
        const groupTextMatches = !query || group.dataset.search?.includes(query);
        const groupWorkflows = [...group.querySelectorAll('[data-workflow]')];
        let visibleInGroup = 0;

        groupWorkflows.forEach((workflow) => {
          const textMatches = !query || groupTextMatches
            || workflow.dataset.search?.includes(query)
            || workflow.textContent.toLowerCase().includes(query);
          const isVisible = categoryMatches && textMatches;
          workflow.hidden = !isVisible;
          if (isVisible) visibleInGroup += 1;
        });

        group.hidden = visibleInGroup === 0;
        if (closeGroups) group.open = false;
        else if (filtering && visibleInGroup > 0) group.open = true;
        visibleCount += visibleInGroup;
      });

      filterLinks.forEach((link) => {
        if (link.dataset.workflowFilter === activeCategory) {
          link.setAttribute('aria-current', 'true');
        } else {
          link.removeAttribute('aria-current');
        }
      });

      if (clearFilter) clearFilter.hidden = activeCategory === 'all';
      if (count) count.textContent = `${visibleCount} of ${workflows.length} workflows`;
      if (empty) empty.hidden = visibleCount !== 0;
    }

    filterLinks.forEach((link) => {
      link.addEventListener('click', (event) => {
        event.preventDefault();
        activeCategory = link.dataset.workflowFilter || 'all';
        if (catalogue) catalogue.open = true;
        update();
      });
    });

    search?.addEventListener('input', () => {
      if (catalogue) catalogue.open = true;
      const closeGroups = !search.value.trim() && activeCategory === 'all';
      update({ closeGroups });
    });

    search?.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape' || !search.value) return;
      search.value = '';
      update({ closeGroups: activeCategory === 'all' });
    });

    clearFilter?.addEventListener('click', () => {
      activeCategory = 'all';
      update({ closeGroups: !search?.value.trim() });
    });

    showAll?.addEventListener('click', () => {
      activeCategory = 'all';
      if (search) search.value = '';
      if (catalogue) catalogue.open = true;
      update({ closeGroups: true });
    });

    catalogue?.removeAttribute('open');
    update({ closeGroups: true });

    return { update };
  }

  return { initWorkflowLibrary };
}));
