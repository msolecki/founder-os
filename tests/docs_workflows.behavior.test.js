const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {
  initWorkflowLibrary,
} = require('../docs/workflow-library.js');
const { initDemoTabs } = require('../docs/demo-tabs.js');
const {
  copyInstallCommand,
  initWorkspaceDemo,
  openWorkspaceFile,
} = require('../docs/workspace-demo.js');

const HTML = fs.readFileSync(
  path.join(__dirname, '..', 'docs', 'index.html'),
  'utf8',
);

class FakeClassList {
  constructor(initial = []) {
    this.values = new Set(initial);
  }

  toggle(name, force) {
    if (force) this.values.add(name);
    else this.values.delete(name);
  }

  contains(name) {
    return this.values.has(name);
  }
}

class FakeElement {
  constructor({ dataset = {}, textContent = '', children = [], classes = [] } = {}) {
    this.dataset = dataset;
    this.textContent = textContent;
    this.children = children;
    this.classList = new FakeClassList(classes);
    this.hidden = false;
    this.open = false;
    this.value = '';
    this.tabIndex = 0;
    this.attributes = {};
    this.listeners = {};
    this.focused = false;
  }

  addEventListener(type, handler) {
    this.listeners[type] = handler;
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
  }

  getAttribute(name) {
    return this.attributes[name] ?? null;
  }

  removeAttribute(name) {
    delete this.attributes[name];
    if (name === 'open') this.open = false;
  }

  querySelectorAll(selector) {
    return selector === '[data-workflow]' ? this.children : [];
  }

  focus() {
    this.focused = true;
  }

  click() {
    this.listeners.click?.({ currentTarget: this, preventDefault() {} });
  }
}

class FakeWorkspaceElement extends FakeElement {
  constructor(options = {}) {
    super(options);
    this.id = options.id || '';
    this.parentElement = null;
    this.ownerDocument = null;
    this.style = {};
    this.heading = null;
    this.selected = false;
  }

  appendChild(child) {
    child.parentElement = this;
    child.ownerDocument = this.ownerDocument;
    this.children.push(child);
    return child;
  }

  contains(element) {
    for (let current = element; current; current = current.parentElement) {
      if (current === this) return true;
    }
    return false;
  }

  focus() {
    super.focus();
    if (this.ownerDocument) this.ownerDocument.activeElement = this;
  }

  querySelector(selector) {
    if (selector === 'h1, h2, h3, h4, h5, h6') return this.heading;
    return null;
  }

  remove() {
    if (!this.parentElement) return;
    this.parentElement.children = this.parentElement.children.filter(
      (child) => child !== this,
    );
    this.parentElement = null;
  }

  select() {
    this.selected = true;
  }
}

function workflowSection() {
  const start = HTML.indexOf(
    '<section class="section workflow-library" id="workflows">',
  );
  return HTML.slice(start, HTML.indexOf('</section>', start));
}

function buildWorkflowDom() {
  const section = workflowSection();
  const groups = [...section.matchAll(
    /<details class="workflow-group"[^>]*data-category="([^"]+)"[^>]*data-search="([^"]*)"[^>]*>([\s\S]*?)<\/details>/g,
  )].map(([, category, search, body]) => {
    const children = [...body.matchAll(
      /<article class="workflow-item"[^>]*data-search="([^"]*)"[^>]*>([\s\S]*?)<\/article>/g,
    )].map(([, itemSearch, itemBody]) => new FakeElement({
      dataset: { search: itemSearch },
      textContent: itemBody
        .replace(/<[^>]+>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .toLowerCase(),
    }));

    return new FakeElement({ dataset: { category, search }, children });
  });

  const links = [...section.matchAll(
    /class="workflow-entry"[^>]*data-workflow-filter="([^"]+)"/g,
  )].map((match) => new FakeElement({
    dataset: { workflowFilter: match[1] },
  }));
  const queryLinks = [...HTML.matchAll(
    /<a class="situation-entry"[^>]*data-workflow-query="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g,
  )].map(([, query, body]) => new FakeElement({
    dataset: { workflowQuery: query },
    textContent: body.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim(),
  }));

  const catalogue = new FakeElement();
  catalogue.open = true;
  const search = new FakeElement();
  const count = new FakeElement();
  const empty = new FakeElement();
  empty.hidden = true;
  const clear = new FakeElement();
  clear.hidden = true;
  const showAll = new FakeElement();
  const workflows = groups.flatMap((group) => group.children);

  const selectorMap = new Map([
    ['#workflow-catalogue', catalogue],
    ['#workflow-search', search],
    ['#workflow-count', count],
    ['#workflow-empty', empty],
    ['[data-clear-workflow-filter]', clear],
    ['[data-show-all-workflows]', showAll],
  ]);

  return {
    catalogue,
    search,
    count,
    empty,
    clear,
    showAll,
    groups,
    links,
    queryLinks,
    workflows,
    document: {
      querySelector(selector) {
        return selectorMap.get(selector) || null;
      },
      querySelectorAll(selector) {
        if (selector === '.workflow-entry[data-workflow-filter]') return links;
        if (selector === '.situation-entry[data-workflow-query]') return queryLinks;
        if (selector === '[data-workflow-group]') return groups;
        if (selector === '[data-workflow]') return workflows;
        return [];
      },
    },
  };
}

function runWorkflowController(assertions) {
  const dom = buildWorkflowDom();
  initWorkflowLibrary(dom.document);
  assertions(dom);
}

function buildDemoDom() {
  const tabs = [...HTML.matchAll(
    /<button class="demo-tab"[^>]*aria-selected="(true|false)"[^>]*data-demo="([^"]+)"[^>]*>/g,
  )].map(([, selected, name]) => {
    const tab = new FakeElement({ dataset: { demo: name } });
    tab.setAttribute('aria-selected', selected);
    tab.tabIndex = selected === 'true' ? 0 : -1;
    return tab;
  });

  const panels = [...HTML.matchAll(
    /<div class="demo-panel([^"]*)"[^>]*data-panel="([^"]+)"[^>]*>/g,
  )].map(([, classSuffix, name]) => new FakeElement({
    dataset: { panel: name },
    classes: classSuffix.includes('is-active') ? ['is-active'] : [],
  }));

  return {
    tabs,
    panels,
    document: {
      querySelectorAll(selector) {
        if (selector === '[data-demo]') return tabs;
        if (selector === '[data-panel]') return panels;
        return [];
      },
    },
  };
}

function runDemoController(assertions) {
  const dom = buildDemoDom();
  initDemoTabs(dom.document);
  assertions(dom);
}

function buildWorkspaceDom() {
  const documentRoot = {
    activeElement: null,
    querySelector(selector) {
      if (selector === '#workspace-current-path') return currentPath;
      if (selector === '#copy-status') return copyStatus;
      return null;
    },
    querySelectorAll(selector) {
      if (selector === '[data-workspace-open]') return triggers;
      if (selector === '[data-workspace-file]') return fileLinks;
      if (selector === '[data-workspace-panel]') return panels;
      if (selector === '[data-copy]') return [];
      return [];
    },
  };

  function element(options) {
    const item = new FakeWorkspaceElement(options);
    item.ownerDocument = documentRoot;
    return item;
  }

  const currentPath = element();
  const copyStatus = element();
  const dailyHeading = element({ textContent: 'Daily brief' });
  const queueHeading = element({ textContent: 'Queue' });
  const dailyPanel = element({
    id: 'sample-daily',
    dataset: { workspacePanel: 'daily', path: 'studio / daily.md' },
    classes: ['is-active'],
  });
  const queuePanel = element({
    id: 'sample-queue',
    dataset: { workspacePanel: 'queue', path: 'studio / queue.md' },
  });
  dailyPanel.heading = dailyHeading;
  queuePanel.heading = queueHeading;
  dailyPanel.appendChild(dailyHeading);
  queuePanel.appendChild(queueHeading);

  const sidebarDaily = element({
    dataset: { workspaceFile: 'daily', workspaceOpen: 'daily' },
    classes: ['workspace-file'],
  });
  const sidebarQueue = element({
    dataset: { workspaceFile: 'queue', workspaceOpen: 'queue' },
    classes: ['workspace-file'],
  });
  const nextDaily = element({
    dataset: { workspaceOpen: 'queue' },
    classes: ['sample-next'],
  });
  dailyPanel.appendChild(nextDaily);

  const panels = [dailyPanel, queuePanel];
  const fileLinks = [sidebarDaily, sidebarQueue];
  const triggers = [sidebarDaily, sidebarQueue, nextDaily];
  const windowRoot = {
    isSecureContext: false,
    location: { hash: '' },
    listeners: {},
    addEventListener(type, listener) {
      this.listeners[type] = listener;
    },
    setTimeout() {},
  };

  return {
    currentPath,
    dailyHeading,
    dailyPanel,
    documentRoot,
    nextDaily,
    queueHeading,
    queuePanel,
    sidebarDaily,
    sidebarQueue,
    windowRoot,
  };
}

function buildClipboardDom({ execResult = true, execError = null } = {}) {
  const body = new FakeWorkspaceElement();
  const status = new FakeWorkspaceElement();
  const button = new FakeWorkspaceElement({
    dataset: { copy: '/founder-os-init' },
    textContent: '⧉',
  });
  const priorFocus = new FakeWorkspaceElement();
  const created = [];
  const documentRoot = {
    activeElement: priorFocus,
    body,
    createElement(name) {
      assert.equal(name, 'textarea');
      const textarea = new FakeWorkspaceElement();
      textarea.ownerDocument = documentRoot;
      created.push(textarea);
      return textarea;
    },
    execCommand(command) {
      assert.equal(command, 'copy');
      if (execError) throw execError;
      return execResult;
    },
    querySelector(selector) {
      return selector === '#copy-status' ? status : null;
    },
  };
  body.ownerDocument = documentRoot;
  button.ownerDocument = documentRoot;
  priorFocus.ownerDocument = documentRoot;
  status.ownerDocument = documentRoot;

  return {
    body,
    button,
    created,
    documentRoot,
    priorFocus,
    status,
    windowRoot: {
      isSecureContext: false,
      setTimeout() {},
    },
  };
}

test('workflow controller executes every approved state transition', () => {
  runWorkflowController(({
    catalogue: workflowCatalogue,
    search: workflowSearch,
    count: workflowCount,
    empty: workflowEmpty,
    clear: clearWorkflowFilter,
    showAll: showAllWorkflows,
    groups: workflowGroups,
    links: workflowFilterLinks,
  }) => {
    const expectedCounts = {
      plan: 10,
      sell: 4,
      deliver: 4,
      money: 5,
      focus: 11,
      grow: 8,
      run: 10,
    };
    assert.equal(workflowCatalogue.open, false);
    assert.equal(workflowCount.textContent, '52 of 52 workflows');

    for (const [category, expectedCount] of Object.entries(expectedCounts)) {
      const link = workflowFilterLinks.find(
        (item) => item.dataset.workflowFilter === category,
      );
      let prevented = false;
      link.listeners.click({ preventDefault() { prevented = true; } });
      assert.equal(prevented, true, `${category}: native jump not enhanced`);
      assert.equal(workflowCatalogue.open, true, `${category}: catalogue closed`);
      assert.equal(
        workflowCount.textContent,
        `${expectedCount} of 52 workflows`,
        `${category}: wrong result count`,
      );
      assert.equal(
        workflowGroups
          .filter((group) => !group.hidden)
          .every((group) => group.dataset.category === category),
        true,
        `${category}: another category leaked into results`,
      );
      assert.equal(link.getAttribute('aria-current'), 'true');
    }

    const growLink = workflowFilterLinks.find(
      (item) => item.dataset.workflowFilter === 'grow',
    );
    growLink.listeners.click({ preventDefault() {} });
    workflowSearch.value = 'voice-capture';
    workflowSearch.listeners.input({});
    assert.equal(workflowCount.textContent, '1 of 52 workflows');

    workflowSearch.listeners.keydown({ key: 'Escape' });
    assert.equal(workflowSearch.value, '');
    assert.equal(workflowCount.textContent, '8 of 52 workflows');

    workflowSearch.value = 'review';
    workflowSearch.listeners.input({});
    clearWorkflowFilter.listeners.click({});
    assert.equal(workflowSearch.value, 'review');
    assert.equal(
      workflowFilterLinks.every(
        (link) => link.getAttribute('aria-current') === null,
      ),
      true,
    );

    workflowSearch.value = 'no-such-workflow-zz';
    workflowSearch.listeners.input({});
    assert.equal(workflowCount.textContent, '0 of 52 workflows');
    assert.equal(workflowEmpty.hidden, false);

    showAllWorkflows.listeners.click({});
    assert.equal(workflowSearch.value, '');
    assert.equal(workflowCount.textContent, '52 of 52 workflows');
    assert.equal(
      workflowGroups.every((group) => !group.hidden && !group.open),
      true,
    );
  });
});

test('situational entries filter one workflow and keep a human-readable name', () => {
  runWorkflowController(({
    catalogue: workflowCatalogue,
    search: workflowSearch,
    count: workflowCount,
    queryLinks,
  }) => {
    assert.equal(queryLinks.length, 5);
    const daily = queryLinks.find(
      (item) => item.dataset.workflowQuery === '/daily-brief',
    );
    assert.ok(daily);
    assert.match(daily.textContent, /I do not know what matters today/);
    assert.doesNotMatch(daily.textContent, /^\/daily-brief$/);

    let prevented = false;
    daily.listeners.click({ preventDefault() { prevented = true; } });

    assert.equal(prevented, true);
    assert.equal(workflowSearch.value, '/daily-brief');
    assert.equal(workflowCount.textContent, '1 of 52 workflows');
    assert.equal(workflowCatalogue.open, true);
    assert.equal(workflowSearch.focused, true);
  });
});

test('demo tabs synchronize panels and wrap arrow-key navigation', () => {
  runDemoController(({ tabs, panels }) => {
    function assertSelected(name) {
      for (const tab of tabs) {
        const selected = tab.dataset.demo === name;
        assert.equal(tab.getAttribute('aria-selected'), String(selected));
        assert.equal(tab.tabIndex, selected ? 0 : -1);
      }
      for (const panel of panels) {
        const selected = panel.dataset.panel === name;
        assert.equal(panel.classList.contains('is-active'), selected);
        assert.equal(panel.hidden, !selected);
      }
    }

    assertSelected('today');
    tabs[1].click();
    assertSelected('pipeline');

    tabs[1].listeners.keydown({ key: 'ArrowRight', preventDefault() {} });
    assert.equal(tabs[2].focused, true);
    assertSelected('friday');

    tabs[2].listeners.keydown({ key: 'ArrowRight', preventDefault() {} });
    assertSelected('today');

    tabs[0].listeners.keydown({ key: 'ArrowLeft', preventDefault() {} });
    assertSelected('friday');
  });
});

test('workspace controller transfers focus only from an in-panel next control', () => {
  const dom = buildWorkspaceDom();
  const controller = initWorkspaceDemo(dom.documentRoot, dom.windowRoot, {});

  assert.ok(controller);
  assert.equal(dom.dailyPanel.classList.contains('is-active'), true);
  assert.equal(dom.dailyHeading.focused, false, 'initial render stole focus');

  dom.sidebarQueue.click();
  assert.equal(dom.queuePanel.classList.contains('is-active'), true);
  assert.equal(dom.queuePanel.getAttribute('aria-hidden'), 'false');
  assert.equal(dom.queueHeading.focused, false, 'sidebar activation stole focus');

  dom.sidebarDaily.click();
  assert.equal(dom.dailyHeading.focused, false, 'persistent sidebar stole focus');

  dom.nextDaily.listeners.click({
    currentTarget: dom.nextDaily,
    detail: 0,
    preventDefault() {},
  });
  assert.equal(dom.dailyPanel.classList.contains('is-active'), false);
  assert.equal(dom.dailyPanel.getAttribute('aria-hidden'), 'true');
  assert.equal(dom.queuePanel.classList.contains('is-active'), true);
  assert.equal(dom.queueHeading.tabIndex, -1);
  assert.equal(dom.queueHeading.focused, true);
  assert.equal(dom.documentRoot.activeElement, dom.queueHeading);
});

test('exported workspace opener returns the active panel without stealing focus', () => {
  const dom = buildWorkspaceDom();
  const activePanel = openWorkspaceFile('queue', {
    documentRoot: dom.documentRoot,
  });

  assert.equal(activePanel, dom.queuePanel);
  assert.equal(dom.currentPath.textContent, 'studio / queue.md');
  assert.equal(dom.sidebarQueue.getAttribute('aria-current'), 'true');
  assert.equal(dom.sidebarDaily.getAttribute('aria-current'), null);
  assert.equal(dom.queueHeading.focused, false);
  assert.equal(openWorkspaceFile('missing', { documentRoot: dom.documentRoot }), null);
});

test('native clipboard success is confirmed before success UI appears', async () => {
  const dom = buildClipboardDom();
  let copied = null;
  dom.windowRoot.isSecureContext = true;
  const navigatorRoot = {
    clipboard: {
      async writeText(value) {
        copied = value;
      },
    },
  };

  const didCopy = await copyInstallCommand(dom.button, {
    documentRoot: dom.documentRoot,
    navigatorRoot,
    windowRoot: dom.windowRoot,
  });

  assert.equal(didCopy, true);
  assert.equal(copied, '/founder-os-init');
  assert.equal(dom.button.textContent, '✓');
  assert.equal(dom.status.textContent, 'Command copied to clipboard.');
  assert.equal(dom.body.children.length, 0);
});

test('clipboard fallback confirms success, cleans up, and restores focus', async () => {
  const dom = buildClipboardDom({ execResult: true });

  const didCopy = await copyInstallCommand(dom.button, {
    documentRoot: dom.documentRoot,
    navigatorRoot: {},
    windowRoot: dom.windowRoot,
  });

  assert.equal(didCopy, true);
  assert.equal(dom.created.length, 1);
  assert.equal(dom.created[0].selected, true);
  assert.equal(dom.body.children.length, 0);
  assert.equal(dom.documentRoot.activeElement, dom.priorFocus);
  assert.equal(dom.priorFocus.focused, true);
  assert.equal(dom.button.textContent, '✓');
  assert.equal(dom.status.textContent, 'Command copied to clipboard.');
});

test('a failed retry removes a previously confirmed success mark', async () => {
  const dom = buildClipboardDom({ execResult: true });
  const options = {
    documentRoot: dom.documentRoot,
    navigatorRoot: {},
    windowRoot: dom.windowRoot,
  };

  assert.equal(await copyInstallCommand(dom.button, options), true);
  assert.equal(dom.button.textContent, '✓');
  dom.documentRoot.execCommand = () => false;

  assert.equal(await copyInstallCommand(dom.button, options), false);
  assert.equal(dom.button.textContent, '⧉');
  assert.equal(
    dom.status.textContent,
    'Copy failed. Select and copy the command manually.',
  );
  assert.equal(dom.body.children.length, 0);
});

test('a repeated confirmed copy replaces the earlier reset timer', async () => {
  const dom = buildClipboardDom({ execResult: true });
  let nextTimerId = 0;
  const pendingTimers = new Map();
  dom.windowRoot.setTimeout = (callback) => {
    nextTimerId += 1;
    pendingTimers.set(nextTimerId, callback);
    return nextTimerId;
  };
  dom.windowRoot.clearTimeout = (timerId) => {
    pendingTimers.delete(timerId);
  };
  const options = {
    documentRoot: dom.documentRoot,
    navigatorRoot: {},
    windowRoot: dom.windowRoot,
  };

  assert.equal(await copyInstallCommand(dom.button, options), true);
  assert.equal(pendingTimers.size, 1);
  assert.equal(await copyInstallCommand(dom.button, options), true);
  assert.equal(pendingTimers.size, 1);
  assert.equal(dom.button.textContent, '✓');
});

for (const failure of [
  { name: 'returns false', options: { execResult: false } },
  { name: 'throws', options: { execError: new Error('copy unavailable') } },
]) {
  test(`clipboard fallback ${failure.name} without claiming success`, async () => {
    const dom = buildClipboardDom(failure.options);

    const didCopy = await copyInstallCommand(dom.button, {
      documentRoot: dom.documentRoot,
      navigatorRoot: {},
      windowRoot: dom.windowRoot,
    });

    assert.equal(didCopy, false);
    assert.equal(dom.body.children.length, 0);
    assert.equal(dom.documentRoot.activeElement, dom.priorFocus);
    assert.equal(dom.priorFocus.focused, true);
    assert.equal(dom.button.textContent, '⧉');
    assert.equal(
      dom.status.textContent,
      'Copy failed. Select and copy the command manually.',
    );
  });
}

test('website loads the workspace controller from a same-origin script', () => {
  assert.match(HTML, /<script src="workspace-demo\.js"><\/script>/);
  assert.doesNotMatch(HTML, /function openWorkspaceFile\(/);
  assert.doesNotMatch(HTML, /async function copyText\(/);
});
