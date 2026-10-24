let captureStream = null;
let playbackContext = null;
let captureContext = null;
let socket = null;
let playbackSourceNode = null;
let captureSourceNode = null;
let captureNode = null;
let muteNode = null;
let stopping = false;

function publishState(state) {
  chrome.runtime.sendMessage({type: 'CAPTURE_STATUS', state}).catch(() => {});
}

function waitForSocketOpen(webSocket, timeoutMs = 4000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Could not connect to the local PriceTyper process. Start the Python GUI first.')), timeoutMs);
    webSocket.addEventListener('open', () => {
      clearTimeout(timer);
      resolve();
    }, {once: true});
    webSocket.addEventListener('error', () => {
      clearTimeout(timer);
      reject(new Error('Local audio bridge connection failed. Check that the PriceTyper GUI is running.'));
    }, {once: true});
  });
}

async function stopCapture(notify = true) {
  stopping = true;
  const oldSocket = socket;
  socket = null;
  if (captureNode) captureNode.disconnect();
  if (playbackSourceNode) playbackSourceNode.disconnect();
  if (captureSourceNode) captureSourceNode.disconnect();
  if (muteNode) muteNode.disconnect();
  captureNode = playbackSourceNode = captureSourceNode = muteNode = null;
  if (captureStream) captureStream.getTracks().forEach((track) => track.stop());
  captureStream = null;
  for (const context of [captureContext, playbackContext]) {
    if (context && context.state !== 'closed') {
      try { await context.close(); } catch (_) {}
    }
  }
  captureContext = playbackContext = null;
  if (oldSocket && oldSocket.readyState < WebSocket.CLOSING) oldSocket.close(1000, 'Capture stopped');
  stopping = false;
  const state = {active: false};
  if (notify) publishState(state);
  return state;
}

async function startCapture(streamId, host, pathname, tabId) {
  await stopCapture(false);
  try {
    const audioUrl = new URL('ws://127.0.0.1:8765/audio');
    audioUrl.searchParams.set('host', host);
    audioUrl.searchParams.set('path', pathname || '');
    audioUrl.searchParams.set('browser', 'chromium');
    audioUrl.searchParams.set('tab_id', String(tabId));
    const newSocket = new WebSocket(audioUrl);
    newSocket.binaryType = 'arraybuffer';
    socket = newSocket;
    newSocket.addEventListener('message', async (event) => {
      if (typeof event.data !== 'string' || newSocket !== socket) return;
      let action;
      try { action = JSON.parse(event.data); } catch (_) { return; }
      if (action?.type !== 'TAB_ACTION' || typeof action.id !== 'string') return;
      try {
        const result = await chrome.runtime.sendMessage({type: 'TAB_ACTION', ...action});
        if (newSocket === socket && newSocket.readyState === WebSocket.OPEN) {
          newSocket.send(JSON.stringify({type: 'TAB_ACTION_RESULT', id: action.id, ...result}));
        }
      } catch (error) {
        if (newSocket === socket && newSocket.readyState === WebSocket.OPEN) {
          newSocket.send(JSON.stringify({
            type: 'TAB_ACTION_RESULT', id: action.id,
            ok: false, error: error.message || String(error)
          }));
        }
      }
    });
    await waitForSocketOpen(newSocket);
    captureStream = await navigator.mediaDevices.getUserMedia({
      audio: {mandatory: {chromeMediaSource: 'tab', chromeMediaSourceId: streamId}},
      video: false
    });
    for (const track of captureStream.getAudioTracks()) {
      track.addEventListener('ended', () => {
        if (stopping || !captureStream || captureStream.getAudioTracks().some((item) => item.readyState === 'live')) return;
        stopCapture(false).then(() => publishState({
          active: false, host, pathname, tabId,
          error: 'The selected tab audio stream ended. Start capture again.'
        }));
      }, {once: true});
    }
    playbackContext = new AudioContext();
    captureContext = new AudioContext({sampleRate: 16000});
    await captureContext.audioWorklet.addModule(chrome.runtime.getURL('pcm-worklet.js'));
    playbackSourceNode = playbackContext.createMediaStreamSource(captureStream);
    captureSourceNode = captureContext.createMediaStreamSource(captureStream);
    captureNode = new AudioWorkletNode(captureContext, 'pcm16-capture', {
      numberOfInputs: 1,
      numberOfOutputs: 1,
      outputChannelCount: [1]
    });
    muteNode = captureContext.createGain();
    muteNode.gain.value = 0;
    captureNode.port.onmessage = (event) => {
      if (socket?.readyState === WebSocket.OPEN) socket.send(event.data);
    };
    playbackSourceNode.connect(playbackContext.destination);
    captureSourceNode.connect(captureNode);
    captureNode.connect(muteNode);
    muteNode.connect(captureContext.destination);
    await Promise.all([playbackContext.resume(), captureContext.resume()]);
    newSocket.addEventListener('close', () => {
      if (!stopping && socket === newSocket) {
        stopCapture(false).then(() => publishState({active: false, error: 'Python audio bridge disconnected.'}));
      }
    }, {once: true});
    const state = {active: true, host, pathname, tabId, browser: 'chromium'};
    publishState(state);
    return state;
  } catch (error) {
    await stopCapture(false);
    const state = {active: false, host, error: error.message || String(error)};
    publishState(state);
    return state;
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === 'OFFSCREEN_START_CAPTURE') {
    startCapture(message.streamId, message.host, message.pathname, message.tabId).then(sendResponse);
    return true;
  }
  if (message?.type === 'OFFSCREEN_STOP_CAPTURE') {
    stopCapture().then(sendResponse);
    return true;
  }
});
