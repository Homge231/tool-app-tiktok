const OFFSCREEN_URL = chrome.runtime.getURL('offscreen.html');

async function ensureOffscreenDocument() {
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT'],
    documentUrls: [OFFSCREEN_URL]
  });
  if (contexts.length === 0) {
    await chrome.offscreen.createDocument({
      url: 'offscreen.html',
      reasons: ['USER_MEDIA'],
      justification: 'Capture audio from the YouTube or TikTok tab the user explicitly selected.'
    });
  }
}

async function setState(state) {
  await chrome.storage.local.set({captureState: state});
  chrome.runtime.sendMessage({type: 'CAPTURE_STATUS', state}).catch(() => {});
}

function isAllowedTab(host, pathname) {
  const allowedHosts = new Set([
    'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be',
    'tiktok.com', 'www.tiktok.com', 'm.tiktok.com'
  ]);
  if (!allowedHosts.has(host)) return false;
  return !host.endsWith('tiktok.com') || /^\/@[^/]+\/live\/?$/.test(pathname);
}

async function performTabAction(action) {
  const {captureState} = await chrome.storage.local.get('captureState');
  if (!captureState?.active || !Number.isInteger(captureState.tabId)) {
    return {ok: false, error: 'No selected tab is connected.'};
  }
  const tab = await chrome.tabs.get(captureState.tabId);
  const currentUrl = new URL(tab.url || 'about:blank');
  if (
    !isAllowedTab(currentUrl.hostname, currentUrl.pathname) ||
    currentUrl.hostname !== captureState.host ||
    currentUrl.pathname !== captureState.pathname ||
    !currentUrl.hostname.endsWith('tiktok.com')
  ) {
    return {ok: false, error: 'The selected tab is no longer the captured TikTok Live page.'};
  }
  if (!['probe', 'draft', 'submit'].includes(action.action)) {
    return {ok: false, error: 'Unsupported tab action.'};
  }
  if (
    ['draft', 'submit'].includes(action.action) &&
    (typeof action.text !== 'string' || !/^@[0-9]+$/.test(action.text))
  ) {
    return {ok: false, error: 'The chat comment must be an @-prefixed ASCII number.'};
  }
  const selectors = Array.isArray(action.selectors) ? action.selectors : [];
  const [execution] = await chrome.scripting.executeScript({
    target: {tabId: captureState.tabId},
    args: [{
      action: action.action,
      text: action.text || '',
      selectors
    }],
    func: (payload) => {
      const visible = (element) => Boolean(
        element && element.getClientRects().length &&
        getComputedStyle(element).visibility !== 'hidden' &&
        getComputedStyle(element).display !== 'none'
      );
      const editable = (element) => {
        if (element.isContentEditable) return true;
        const tag = element.tagName?.toLowerCase();
        return (tag === 'input' || tag === 'textarea') &&
          !element.disabled && !element.readOnly;
      };
      const inputHint = (element) => {
        const attributes = [
          'placeholder', 'aria-label', 'data-e2e', 'data-placeholder',
          'role', 'contenteditable'
        ];
        const details = attributes
          .map((name) => [name, element.getAttribute(name)])
          .filter(([, value]) => value)
          .map(([name, value]) => `${name}=${JSON.stringify(value.slice(0, 80))}`);
        return `<${element.tagName.toLowerCase()}>${details.length ? ` ${details.join(' ')}` : ''}`;
      };
      let input = null;
      let matchedSelector = false;
      for (const selector of payload.selectors) {
        try {
          const matches = new Set();
          for (const element of document.querySelectorAll(selector)) {
            if (visible(element) && editable(element)) matches.add(element);
          }
          // Selectors are ordered from most specific to most general. Prefer an
          // exact site selector when it is available, without allowing broad
          // fallback selectors to make that exact match look ambiguous.
          if (matches.size > 1) {
            const controls = [...document.querySelectorAll(
              'input, textarea, [contenteditable], [role="textbox"]'
            )].filter(visible).slice(0, 5).map(inputHint);
            const hint = controls.length
              ? ` Visible text controls: ${controls.join('; ')}.`
              : '';
            return {
              ok: false,
              error: `More than one visible editable input matched selector ${selector}.${hint}`
            };
          }
          if (matches.size === 1) {
            input = [...matches][0];
            matchedSelector = true;
            break;
          }
        } catch (_) {
          return {ok: false, error: 'A configured chat input selector is invalid.'};
        }
      }
      if (!matchedSelector) {
        const controls = [...document.querySelectorAll(
          'input, textarea, [contenteditable], [role="textbox"]'
        )].filter(visible).slice(0, 5).map(inputHint);
        const hint = controls.length
          ? ` Visible text controls: ${controls.join('; ')}.`
          : ' No visible input-like controls were found in the page frame.';
        return {
          ok: false,
          error: `No visible editable chat input matched the configured selectors.${hint}`
        };
      }
      if (payload.action === 'probe') return {ok: true};

      const existing = input.isContentEditable
        ? input.textContent
        : ('value' in input ? input.value : input.textContent);
      if (String(existing || '').trim()) {
        return {ok: false, error: 'The chat input is not empty; clear it before filling a number.'};
      }
      input.focus();
      if (input.isContentEditable) {
        const inserted = document.execCommand('insertText', false, payload.text);
        if (!inserted) {
          input.textContent = payload.text;
          input.dispatchEvent(new InputEvent('input', {
            bubbles: true, inputType: 'insertText', data: payload.text
          }));
        }
      } else {
        const prototype = input instanceof HTMLTextAreaElement
          ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;
        if (!setter) return {ok: false, error: 'The visible chat input cannot accept text.'};
        setter.call(input, payload.text);
        input.dispatchEvent(new InputEvent('input', {
          bubbles: true, inputType: 'insertText', data: payload.text
        }));
        input.dispatchEvent(new Event('change', {bubbles: true}));
      }

      const entered = String(input.isContentEditable
        ? input.textContent
        : ('value' in input ? input.value : input.textContent)).trim();
      if (entered !== payload.text) {
        return {ok: false, error: 'The number was not confirmed in the chat input; nothing was submitted.'};
      }

      if (payload.action === 'submit') {
        input.dispatchEvent(new KeyboardEvent('keydown', {
          key: 'Enter', code: 'Enter', keyCode: 13, which: 13,
          bubbles: true, cancelable: true
        }));
        return {ok: true, delivery: 'enter_dispatched_unverified'};
      }

      return {ok: true, delivery: 'draft_filled_unsubmitted'};
    }
  });
  return execution?.result || {ok: false, error: 'The selected tab returned no action result.'};
}

async function stopIfCapturedTabChanged(tabId, tabUrl, message) {
  const {captureState} = await chrome.storage.local.get('captureState');
  if (!captureState?.active || captureState.tabId !== tabId) return;
  let stillSamePage = false;
  try {
    const url = new URL(tabUrl || 'about:blank');
    stillSamePage = url.hostname === captureState.host && url.pathname === captureState.pathname;
  } catch (_) {}
  if (stillSamePage) return;
  await chrome.runtime.sendMessage({type: 'OFFSCREEN_STOP_CAPTURE'}).catch(() => {});
  await setState({active: false, error: message});
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (typeof changeInfo.url === 'string') {
    stopIfCapturedTabChanged(tabId, changeInfo.url, 'The captured tab navigated; start capture again.').catch(() => {});
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  stopIfCapturedTabChanged(tabId, 'about:blank', 'The captured tab was closed.').catch(() => {});
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'GET_STATUS') {
    chrome.storage.local.get('captureState').then(({captureState}) => {
      sendResponse(captureState || {active: false});
    });
    return true;
  }

  if (message?.type === 'START_CAPTURE') {
    (async () => {
      if (typeof message.streamId !== 'string' || !message.streamId) {
        throw new Error('The browser did not provide a tab-audio stream.');
      }
      if (!Number.isInteger(message.tabId) || !isAllowedTab(message.host, message.pathname)) {
        throw new Error('Select a supported YouTube video or TikTok Live tab first.');
      }
      if (message.host.endsWith('tiktok.com')) {
        await chrome.scripting.executeScript({target: {tabId: message.tabId}, func: () => true});
      }
      await ensureOffscreenDocument();
      const state = await chrome.runtime.sendMessage({
        type: 'OFFSCREEN_START_CAPTURE', streamId: message.streamId,
        host: message.host, pathname: message.pathname, tabId: message.tabId
      });
      if (!state?.active) throw new Error(state?.error || 'Tab audio capture could not start.');
      const connected = {...state, tabId: message.tabId, pathname: message.pathname};
      await setState(connected);
      sendResponse(connected);
    })().catch(async (error) => {
      const state = {active: false, error: error.message || String(error)};
      await setState(state);
      sendResponse(state);
    });
    return true;
  }

  if (message?.type === 'STOP_CAPTURE') {
    chrome.runtime.sendMessage({type: 'OFFSCREEN_STOP_CAPTURE'}).then(async (state) => {
      const result = state || {active: false};
      await setState(result);
      sendResponse(result);
    }).catch(async (error) => {
      const state = {active: false, error: error.message || String(error)};
      await setState(state);
      sendResponse(state);
    });
    return true;
  }

  if (message?.type === 'TAB_ACTION' && sender.url === OFFSCREEN_URL) {
    performTabAction(message).then(sendResponse).catch((error) => {
      sendResponse({ok: false, error: error.message || String(error)});
    });
    return true;
  }

  if (message?.type === 'CAPTURE_STATUS') {
    chrome.storage.local.set({captureState: message.state || {active: false}}).catch(() => {});
  }
});
