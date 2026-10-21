const statusText = document.getElementById('status');
const toggleButton = document.getElementById('toggle');
let active = false;

function localizeError(message) {
  const translations = new Map([
    ['Could not connect to the local PriceTyper process. Start the Python GUI first.', 'Không kết nối được ứng dụng NumberTyper trên máy. Hãy mở ứng dụng trước.'],
    ['Local audio bridge connection failed. Check that the PriceTyper GUI is running.', 'Kết nối audio cục bộ thất bại. Hãy kiểm tra NumberTyper đang mở.'],
    ['Python audio bridge disconnected.', 'Ứng dụng NumberTyper đã ngắt kết nối audio.'],
    ['No selected tab is connected.', 'Chưa có tab được kết nối.'],
    ['The selected tab is no longer the captured TikTok Live page.', 'Tab đã chọn không còn là trang TikTok Live đang thu.'],
    ['Unsupported tab action.', 'Thao tác trên tab này không được hỗ trợ.'],
    ['Only an ASCII number can be filled into the chat input.', 'Ứng dụng chỉ điền được số vào ô chat.'],
    ['A configured chat input selector is invalid.', 'Cấu hình ô nhập chat không hợp lệ.'],
    ['No visible chat input matched the configured selectors.', 'Không tìm thấy ô chat đang hiển thị trên tab.']
  ]);
  return translations.get(message) || message;
}

function render(state) {
  active = Boolean(state && state.active);
  statusText.textContent = state?.error
    ? localizeError(state.error)
    : active
      ? `Đang thu âm thanh của ${state.host || 'tab này'}. Âm thanh vẫn phát qua thiết bị bạn đã chọn.`
      : 'Mở video YouTube hoặc tab TikTok Live, sau đó bắt đầu thu âm thanh.';
  toggleButton.textContent = active ? 'Dừng thu tab' : 'Bắt đầu thu tab này';
  toggleButton.classList.toggle('stop', active);
  toggleButton.disabled = false;
}

async function refresh() {
  try {
    render(await chrome.runtime.sendMessage({type: 'GET_STATUS'}));
  } catch (error) {
    statusText.textContent = `Không đọc được trạng thái NumberTyper: ${error.message}`;
    toggleButton.disabled = false;
  }
}

toggleButton.addEventListener('click', async () => {
  toggleButton.disabled = true;
  statusText.textContent = active ? 'Đang dừng thu…' : 'Đang bắt đầu thu…';
  try {
    if (active) {
      render(await chrome.runtime.sendMessage({type: 'STOP_CAPTURE'}));
      return;
    }
    const [tab] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
    if (!tab || !Number.isInteger(tab.id)) throw new Error('Không tìm thấy tab trình duyệt đang hoạt động.');
    const url = new URL(tab.url || '');
    const allowedHosts = [
      'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be',
      'tiktok.com', 'www.tiktok.com', 'm.tiktok.com'
    ];
    if (!allowedHosts.includes(url.hostname)) {
      throw new Error('Trước tiên hãy chọn video YouTube hoặc tab TikTok Live.');
    }
    if (url.hostname.endsWith('tiktok.com') && !/^\/@[^/]+\/live\/?$/.test(url.pathname)) {
      throw new Error('Hãy chọn đúng trang TikTok Live dạng /@tên-người-dùng/live.');
    }
    const streamId = await chrome.tabCapture.getMediaStreamId({targetTabId: tab.id});
    if (typeof streamId !== 'string' || streamId.length === 0) {
      throw new Error('Trình duyệt không cấp được audio của tab. Hãy tải lại tiện ích NumberTyper rồi thử lại.');
    }
    render(await chrome.runtime.sendMessage({
      type: 'START_CAPTURE', streamId, host: url.hostname,
      pathname: url.pathname, tabId: tab.id
    }));
  } catch (error) {
    render({active: false, error: error.message || String(error)});
  }
});

chrome.runtime.onMessage.addListener((message) => {
  if (message?.type === 'CAPTURE_STATUS') render(message.state);
});

refresh();
