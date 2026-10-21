const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');

async function runPopup(tabCaptureResult, tabUrl = 'https://www.youtube.com/watch?v=test') {
  const messages = [];
  const listeners = new Map();
  const statusElement = {textContent: ''};
  const toggleButton = {
    textContent: '',
    disabled: false,
    classList: {toggle() {}},
    addEventListener(name, callback) {
      listeners.set(name, callback);
    }
  };
  const chrome = {
    runtime: {
      onMessage: {addListener() {}},
      async sendMessage(message) {
        messages.push(message);
        if (message.type === 'GET_STATUS') return {active: false};
        if (message.type === 'START_CAPTURE') return {active: true};
        throw new Error(`Unexpected message: ${message.type}`);
      }
    },
    tabs: {
      async query() {
        return [{id: 12, url: tabUrl}];
      }
    },
    tabCapture: {
      async getMediaStreamId(options) {
        assert.equal(options.targetTabId, 12);
        return tabCaptureResult;
      }
    }
  };
  const document = {
    getElementById(id) {
      return id === 'status' ? statusElement : toggleButton;
    }
  };
  const source = fs.readFileSync(
    path.join(__dirname, '..', 'browser_extension', 'popup.js'),
    'utf8'
  );
  vm.runInNewContext(source, {chrome, document, URL, Error, Boolean});
  await listeners.get('click')();
  return {messages, statusElement, toggleButton};
}

test('forwards Chrome tabCapture stream ID string to the service worker', async () => {
  const {messages} = await runPopup('opaque-capture-id');
  const startMessage = messages.find((message) => message.type === 'START_CAPTURE');
  assert.ok(startMessage);
  assert.equal(startMessage.streamId, 'opaque-capture-id');
  assert.equal(startMessage.host, 'www.youtube.com');
  assert.equal(startMessage.pathname, '/watch');
  assert.equal(startMessage.tabId, 12);
});

test('shows Vietnamese tab-capture status and controls', async () => {
  const {statusElement, toggleButton} = await runPopup('opaque-capture-id');
  assert.equal(
    statusElement.textContent,
    'Đang thu âm thanh của tab này. Âm thanh vẫn phát qua thiết bị bạn đã chọn.'
  );
  assert.equal(toggleButton.textContent, 'Dừng thu tab');
});

test('allows a TikTok Live tab and forwards its hostname and path', async () => {
  const {messages} = await runPopup(
    'opaque-capture-id',
    'https://www.tiktok.com/@seller/live'
  );
  const startMessage = messages.find((message) => message.type === 'START_CAPTURE');
  assert.equal(startMessage.host, 'www.tiktok.com');
  assert.equal(startMessage.pathname, '/@seller/live');
  assert.equal(startMessage.tabId, 12);
});

test('rejects an ordinary TikTok page before requesting a tab stream', async () => {
  const {messages, statusElement} = await runPopup(
    'opaque-capture-id',
    'https://www.tiktok.com/@seller/video/123'
  );
  assert.equal(messages.some((message) => message.type === 'START_CAPTURE'), false);
  assert.match(statusElement.textContent, /Hãy chọn đúng trang TikTok Live/i);
});

test('shows a useful error and does not start when the browser returns no stream ID', async () => {
  const {messages, statusElement} = await runPopup(undefined);
  assert.equal(messages.some((message) => message.type === 'START_CAPTURE'), false);
  assert.match(statusElement.textContent, /không cấp được audio của tab/i);
  assert.match(statusElement.textContent, /tải lại tiện ích NumberTyper/i);
});
