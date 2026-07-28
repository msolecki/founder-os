(function exposeWorkspaceDemo(root, factory) {
  const controller = factory(root);
  if (typeof module === 'object' && module.exports) {
    module.exports = controller;
  } else {
    root.FounderOSWorkspaceDemo = controller;
  }
}(typeof globalThis !== 'undefined' ? globalThis : this, function buildController(root) {
  'use strict';

  let defaultDocument = null;
  let defaultWindow = null;
  const originalLabels = new WeakMap();
  const resetTimers = new WeakMap();

  function workspaceElements(documentRoot) {
    return {
      currentPath: documentRoot.querySelector('#workspace-current-path'),
      fileLinks: [...documentRoot.querySelectorAll('[data-workspace-file]')],
      panels: [...documentRoot.querySelectorAll('[data-workspace-panel]')],
    };
  }

  function openWorkspaceFile(name, options = {}) {
    const documentRoot = options.documentRoot
      || defaultDocument
      || root?.document;
    const { trigger = null } = options;
    if (!documentRoot || typeof documentRoot.querySelectorAll !== 'function') {
      return null;
    }

    const { currentPath, fileLinks, panels } = workspaceElements(documentRoot);
    const activePanel = panels.find(
      (panel) => panel.dataset.workspacePanel === name,
    );
    if (!activePanel) return null;

    const outgoingPanel = panels.find(
      (panel) => panel.classList.contains('is-active'),
    );
    const shouldTransferFocus = Boolean(
      trigger
      && outgoingPanel
      && outgoingPanel !== activePanel
      && trigger.classList?.contains('sample-next')
      && outgoingPanel.contains(trigger),
    );

    panels.forEach((panel) => {
      const isActive = panel === activePanel;
      panel.classList.toggle('is-active', isActive);
      panel.setAttribute('aria-hidden', String(!isActive));
    });

    fileLinks.forEach((link) => {
      if (link.dataset.workspaceFile === name) {
        link.setAttribute('aria-current', 'true');
      } else {
        link.removeAttribute('aria-current');
      }
    });

    if (currentPath) currentPath.textContent = activePanel.dataset.path || '';

    if (shouldTransferFocus) {
      const heading = activePanel.querySelector('h1, h2, h3, h4, h5, h6');
      if (heading) {
        heading.tabIndex = -1;
        heading.focus();
      }
    }

    return activePanel;
  }

  async function copyInstallCommand(button, options = {}) {
    const documentRoot = options.documentRoot
      || defaultDocument
      || root?.document;
    const windowRoot = options.windowRoot || defaultWindow || root;
    const navigatorRoot = options.navigatorRoot || windowRoot?.navigator;
    const copyStatus = documentRoot?.querySelector('#copy-status');
    if (!button) return false;
    if (!originalLabels.has(button)) {
      originalLabels.set(button, button.textContent);
    }
    const original = originalLabels.get(button);
    const pendingReset = resetTimers.get(button);
    if (pendingReset) {
      pendingReset.windowRoot?.clearTimeout?.(pendingReset.timerId);
      resetTimers.delete(button);
    }
    let copied = false;
    let input = null;
    let previousFocus = null;

    try {
      if (
        windowRoot?.isSecureContext
        && typeof navigatorRoot?.clipboard?.writeText === 'function'
      ) {
        await navigatorRoot.clipboard.writeText(button.dataset.copy);
        copied = true;
      } else {
        previousFocus = documentRoot.activeElement;
        input = documentRoot.createElement('textarea');
        input.value = button.dataset.copy;
        input.setAttribute('readonly', '');
        input.style.position = 'fixed';
        input.style.opacity = '0';
        input.style.pointerEvents = 'none';
        documentRoot.body.appendChild(input);
        input.select();
        copied = typeof documentRoot.execCommand === 'function'
          && documentRoot.execCommand('copy') === true;
      }
    } catch {
      copied = false;
    } finally {
      try {
        if (input) input.remove();
      } catch {
        // Copy truth is still reported even if a legacy DOM cannot remove cleanly.
      }
      if (previousFocus && typeof previousFocus.focus === 'function') {
        try {
          previousFocus.focus();
        } catch {
          // Restoring focus is best effort after the fallback cleanup attempt.
        }
      }
    }

    if (!copied) {
      button.textContent = original;
      if (copyStatus) {
        copyStatus.textContent = 'Copy failed. Select and copy the command manually.';
      }
      return false;
    }

    button.textContent = '✓';
    if (copyStatus) copyStatus.textContent = 'Command copied to clipboard.';
    if (typeof windowRoot?.setTimeout === 'function') {
      const reset = { timerId: null, windowRoot };
      reset.timerId = windowRoot.setTimeout(() => {
        if (resetTimers.get(button) !== reset) return;
        button.textContent = original;
        resetTimers.delete(button);
      }, 1400);
      resetTimers.set(button, reset);
    }
    return true;
  }

  function initWorkspaceDemo(documentRoot, windowRoot, navigatorRoot) {
    if (!documentRoot || typeof documentRoot.querySelectorAll !== 'function') {
      return null;
    }

    defaultDocument = documentRoot;
    defaultWindow = windowRoot;

    const triggers = [...documentRoot.querySelectorAll('[data-workspace-open]')];
    const panels = [...documentRoot.querySelectorAll('[data-workspace-panel]')];

    const open = (name, trigger = null) => openWorkspaceFile(name, {
      documentRoot,
      trigger,
    });

    triggers.forEach((trigger) => {
      trigger.addEventListener('click', () => {
        open(trigger.dataset.workspaceOpen, trigger);
      });
    });

    function syncWorkspaceFromHash() {
      const panel = panels.find((item) => `#${item.id}` === windowRoot.location.hash);
      if (panel) open(panel.dataset.workspacePanel);
      else if (!windowRoot.location.hash || windowRoot.location.hash === '#sample-workspace') {
        open('daily');
      }
    }

    windowRoot.addEventListener('hashchange', syncWorkspaceFromHash);
    const initialPanel = panels.find(
      (panel) => `#${panel.id}` === windowRoot.location.hash,
    );
    open(initialPanel?.dataset.workspacePanel || 'daily');

    documentRoot.querySelectorAll('[data-copy]').forEach((button) => {
      button.addEventListener('click', () => copyInstallCommand(button, {
        documentRoot,
        navigatorRoot,
        windowRoot,
      }));
    });

    return {
      copyInstallCommand: (button) => copyInstallCommand(button, {
        documentRoot,
        navigatorRoot,
        windowRoot,
      }),
      openWorkspaceFile: open,
    };
  }

  return { copyInstallCommand, initWorkspaceDemo, openWorkspaceFile };
}));
