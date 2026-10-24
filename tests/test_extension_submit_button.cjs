const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const serviceWorker = fs.readFileSync(
  path.join(__dirname, '..', 'browser_extension', 'service-worker.js'),
  'utf8'
);

function makeExtension(buttonCount) {
  let messageListener;
  let clickCount = 0;
  const input = {
    tagName: 'DIV',
    isContentEditable: true,
    isConnected: true,
    disabled: false,
    readOnly: false,
    textContent: '',
    parentElement: null,
    getAttribute: () => null,
    getClientRects: () => [{}],
    getBoundingClientRect: () => ({top: 10, bottom: 40}),
    focus() {},
    dispatchEvent() {},
  };
  const buttons = Array.from({length: buttonCount}, () => ({
    tagName: 'DIV',
    isConnected: true,
    disabled: false,
    getAttribute: (name) => name === 'data-e2e' ? 'room-chat-send-btn' : null,
    getClientRects: () => [{}],
    click() { clickCount += 1; },
  }));
  const container = {
    parentElement: null,
    querySelectorAll: (selector) => selector === '[data-e2e="room-chat-send-btn"]'
      ? buttons : [],
  };
  input.parentElement = container;

  const page = {
    document: {
      querySelectorAll: (selector) =>
        selector === '[data-e2e="room-chat-input-field"]' ? [input] : [],
      execCommand(command, _ui, text) {
        assert.equal(command, 'insertText');
        input.textContent = text;
        return true;
      },
    },
    window: {},
    getComputedStyle: () => ({visibility: 'visible', display: 'block'}),
  };
  const captureState = {
    active: true,
    tabId: 7,
    host: 'www.tiktok.com',
    pathname: '/@seller/live',
  };
  const context = vm.createContext({
    URL,
    ...page,
    chrome: {
      runtime: {
        getURL: (file) => `chrome-extension://test/${file}`,
        onMessage: {addListener: (listener) => { messageListener = listener; }},
        sendMessage: async () => ({}),
      },
      storage: {
        local: {
          get: async () => ({captureState}),
          set: async () => {},
        },
      },
      tabs: {
        get: async () => ({url: 'https://www.tiktok.com/@seller/live'}),
        onUpdated: {addListener() {}},
        onRemoved: {addListener() {}},
      },
      scripting: {
        executeScript: async ({target, func, args}) => {
          assert.equal(target.tabId, captureState.tabId);
          return [{result: await func(...args)}];
        },
      },
    },
  });
  vm.runInContext(serviceWorker, context);

  return {
    input,
    get clickCount() { return clickCount; },
    async submit() {
      return new Promise((resolve) => {
        const handled = messageListener({
          type: 'TAB_ACTION',
          action: 'submit',
          text: '@12',
          selectors: ['[data-e2e="room-chat-input-field"]'],
        }, {url: 'chrome-extension://test/offscreen.html'}, resolve);
        assert.equal(handled, true);
      });
    },
  };
}

test('clicks TikTok send control once after filling @number', async () => {
  const extension = makeExtension(1);

  const result = await extension.submit();

  assert.deepEqual({...result}, {ok: true, delivery: 'send_button_clicked_unverified'});
  assert.equal(extension.input.textContent, '@12');
  assert.equal(extension.clickCount, 1);
});

test('leaves the input unchanged when the exact send control is ambiguous', async () => {
  const extension = makeExtension(2);

  const result = await extension.submit();

  assert.equal(result.ok, false);
  assert.match(result.error, /nothing was changed/);
  assert.equal(extension.input.textContent, '');
  assert.equal(extension.clickCount, 0);
});
