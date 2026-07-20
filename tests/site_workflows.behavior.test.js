const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

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
    this.listeners.click?.({ preventDefault() {} });
  }
}

function workflowSection() {
  const start = HTML.indexOf(
    '<section class="section workflow-library" id="workflows">',
  );
  return HTML.slice(start, HTML.indexOf('</section>', start));
}

function extractController(startMarker, endMarker) {
  const start = HTML.indexOf(startMarker);
  const end = HTML.indexOf(endMarker, start);
  assert.notEqual(start, -1, `missing controller marker: ${startMarker}`);
  assert.notEqual(end, -1, `missing controller marker: ${endMarker}`);
  return HTML.slice(start, end);
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
    workflows,
    document: {
      querySelector(selector) {
        return selectorMap.get(selector) || null;
      },
      querySelectorAll(selector) {
        if (selector === '.workflow-entry[data-workflow-filter]') return links;
        if (selector === '[data-workflow-group]') return groups;
        if (selector === '[data-workflow]') return workflows;
        return [];
      },
    },
  };
}

function runWorkflowController(assertions) {
  const dom = buildWorkflowDom();
  const previousDocument = global.document;
  global.document = dom.document;
  const expectedCounts = {
    plan: 10,
    sell: 4,
    deliver: 4,
    money: 5,
    focus: 9,
    grow: 8,
    run: 9,
  };
  const controller = extractController(
    "      const workflowCatalogue = document.querySelector('#workflow-catalogue');",
    "      const tabs = [...document.querySelectorAll('[data-demo]')];",
  );

  try {
    eval(`${controller}\n(${assertions.toString()})();`);
  } finally {
    global.document = previousDocument;
  }
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
  const previousDocument = global.document;
  global.document = dom.document;
  const controller = extractController(
    "      const tabs = [...document.querySelectorAll('[data-demo]')];",
    "      const copyStatus = document.querySelector('#copy-status');",
  );

  try {
    eval(`${controller}\n(${assertions.toString()})();`);
  } finally {
    global.document = previousDocument;
  }
}

test('workflow controller executes every approved state transition', () => {
  runWorkflowController(function verifyWorkflowState() {
    assert.equal(workflowCatalogue.open, false);
    assert.equal(workflowCount.textContent, '49 of 49 workflows');

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
        `${expectedCount} of 49 workflows`,
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
    assert.equal(workflowCount.textContent, '1 of 49 workflows');

    workflowSearch.listeners.keydown({ key: 'Escape' });
    assert.equal(workflowSearch.value, '');
    assert.equal(workflowCount.textContent, '8 of 49 workflows');

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
    assert.equal(workflowCount.textContent, '0 of 49 workflows');
    assert.equal(workflowEmpty.hidden, false);

    showAllWorkflows.listeners.click({});
    assert.equal(workflowSearch.value, '');
    assert.equal(workflowCount.textContent, '49 of 49 workflows');
    assert.equal(
      workflowGroups.every((group) => !group.hidden && !group.open),
      true,
    );
  });
});

test('demo tabs synchronize panels and wrap arrow-key navigation', () => {
  runDemoController(function verifyDemoState() {
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
