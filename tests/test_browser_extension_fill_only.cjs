const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');

function createHarness({
  existingText = '',
  exactMatchCount = 1,
  otherEditableCount = 0,
} = {}) {
  const extensionUrl = 'chrome-extension://test-extension/offscreen.html';
  const events = [];
  const submitted = [];
  let onMessage;
  const makeInput = ({isChat = false, initialText = ''} = {}) => {
    const element = {
      tagName: 'DIV',
      isContentEditable: true,
      disabled: false,
      readOnly: false,
      textContent: initialText,
      getClientRects: () => [{}],
      getAttribute: (name) => ({
        'data-e2e': isChat ? 'room-chat-input-field' : null,
        contenteditable: 'plaintext-only',
        placeholder: isChat ? 'Type...' : 'Other editable area',
      })[name] || null,
      focus: () => events.push('focus'),
      click: () => events.push('click'),
      dispatchEvent: (event) => {
        events.push(event.key ? `key:${event.key}` : event.type);
        // Model a local fake chat app whose submit handler reacts to Enter.
        if (event.type === 'keydown' && event.key === 'Enter') {
          const text = element.textContent.trim();
          if (text) {
            submitted.push(text);
            element.textContent = '';
          }
        }
        return true;
      },
    };
    return element;
  };
  const input = makeInput({isChat: true, initialText: existingText});
  const exactMatches = Array.from({length: exactMatchCount}, (_, index) =>
    index === 0 ? input : makeInput({isChat: true})
  );
  const otherEditables = Array.from({length: otherEditableCount}, () => makeInput());

  const context = vm.createContext({
    URL,
    chrome: {
      runtime: {
        getURL: (resource) => `chrome-extension://test-extension/${resource}`,
        onMessage: {addListener: (listener) => { onMessage = listener; }},
        sendMessage: async () => ({}),
      },
      storage: {
        local: {
          get: async () => ({captureState: {
            active: true,
            tabId: 17,
            host: 'www.tiktok.com',
            pathname: '/@seller/live',
          }}),
          set: async () => {},
        },
      },
      tabs: {
        get: async () => ({
          id: 17,
          url: 'https://www.tiktok.com/@seller/live',
        }),
        onUpdated: {addListener: () => {}},
        onRemoved: {addListener: () => {}},
      },
      scripting: {
        executeScript: async ({args, func}) => {
          context.payload = args[0];
          const document = {
            querySelectorAll: (selector) => {
              if (selector.includes('input, textarea,')) {
                return [input, ...otherEditables];
              }
              if (selector === '[data-e2e="room-chat-input-field"]') {
                return exactMatches;
              }
              if (selector.includes('contenteditable')) {
                return [input, ...otherEditables];
              }
              return [];
            },
            execCommand: (command, _showUi, text) => {
              events.push(`execCommand:${command}`);
              input.textContent = text;
              return true;
            },
          };
          context.document = document;
          context.getComputedStyle = () => ({visibility: 'visible', display: 'block'});
          context.InputEvent = class InputEvent {
            constructor(type) { this.type = type; }
          };
          context.Event = class Event {
            constructor(type) { this.type = type; }
          };
          context.KeyboardEvent = class KeyboardEvent {
            constructor(type, options) {
              this.type = type;
              this.key = options.key;
              this.code = options.code;
            }
          };
          const result = vm.runInContext(`(${func.toString()})(payload)`, context);
          return [{result}];
        },
      },
    },
  });

  const source = fs.readFileSync(
    path.join(__dirname, '..', 'browser_extension', 'service-worker.js'),
    'utf8'
  );
  vm.runInContext(source, context);

  async function request(action) {
    return new Promise((resolve) => {
      onMessage(
        {type: 'TAB_ACTION', ...action},
        {url: extensionUrl},
        resolve
      );
    });
  }
  return {events, input, request, submitted};
}

test('draft action fills digits and never clicks or dispatches submit keys', async () => {
  const {events, input, request, submitted} = createHarness();
  const result = await request({
    action: 'draft',
    text: '100000',
    selectors: ['[data-e2e="room-chat-input-field"]'],
  });

  assert.equal(result.ok, true);
  assert.equal(result.delivery, 'draft_filled_unsubmitted');
  assert.equal(input.textContent, '100000');
  assert.equal(events.includes('click'), false);
  assert.equal(events.some((event) => /^(key|submit)/i.test(event)), false);
  assert.ok(events.includes('execCommand:insertText'));
});

test('send action is rejected by the extension bridge', async () => {
  const {request} = createHarness();
  const result = await request({action: 'send', text: '100000'});
  assert.equal(result.ok, false);
  assert.match(result.error, /Unsupported tab action/);
});

test('submit action fills digits then dispatches one Enter key without clicking', async () => {
  const {events, input, request, submitted} = createHarness();
  const result = await request({
    action: 'submit',
    text: '9',
    selectors: ['[data-e2e="room-chat-input-field"]'],
  });

  assert.equal(result.ok, true);
  assert.equal(result.delivery, 'enter_dispatched_unverified');
  assert.equal(input.textContent, '');
  assert.equal(events.filter((event) => event === 'key:Enter').length, 1);
  assert.equal(events.includes('click'), false);
  assert.deepEqual(submitted, ['9']);
});

test('non-empty chat input is not overwritten', async () => {
  const {events, input, request, submitted} = createHarness({existingText: 'my draft'});
  const result = await request({
    action: 'draft',
    text: '100000',
    selectors: ['[data-e2e="room-chat-input-field"]'],
  });

  assert.equal(result.ok, false);
  assert.match(result.error, /not empty/);
  assert.equal(input.textContent, 'my draft');
  assert.equal(events.includes('click'), false);
});

test('submit refuses to send if the input already contains user text', async () => {
  const {events, input, request, submitted} = createHarness({existingText: 'my draft'});
  const result = await request({
    action: 'submit',
    text: '9',
    selectors: ['[data-e2e="room-chat-input-field"]'],
  });

  assert.equal(result.ok, false);
  assert.match(result.error, /not empty/);
  assert.equal(input.textContent, 'my draft');
  assert.equal(events.includes('key:Enter'), false);
  assert.deepEqual(submitted, []);
});

test('prefers the exact TikTok chat field when other editable controls are visible', async () => {
  const {input, request} = createHarness({otherEditableCount: 2});
  const result = await request({
    action: 'draft',
    text: '140',
    selectors: [
      '[data-e2e="room-chat-input-field"]',
      '[contenteditable]:not([contenteditable="false"])',
    ],
  });

  assert.equal(result.ok, true);
  assert.equal(input.textContent, '140');
});

test('refuses when the exact TikTok chat selector matches more than one visible field', async () => {
  const {input, request} = createHarness({exactMatchCount: 2});
  const result = await request({
    action: 'probe',
    selectors: [
      '[data-e2e="room-chat-input-field"]',
      '[contenteditable]:not([contenteditable="false"])',
    ],
  });

  assert.equal(result.ok, false);
  assert.match(result.error, /More than one visible editable input matched selector/);
  assert.equal(input.textContent, '');
});
