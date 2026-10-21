from pathlib import Path

import pytest

from pricetyper.audio.browser_tab import TIKTOK_HOSTS
from pricetyper.config import PlaywrightConfig
from pricetyper.senders.desktop_sender import SenderPrepareError
from pricetyper.senders.playwright_sender import PlaywrightSender


def _browser_channel():
    import os
    import shutil
    from pathlib import Path
    program_files = os.environ.get('PROGRAMFILES', 'C:/Program Files')
    program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')
    local_app_data = os.environ.get('LOCALAPPDATA', 'C:/Users/Default/AppData/Local')
    edge_candidates = [
        shutil.which('msedge'),
        shutil.which('msedge.exe'),
        Path(program_files) / 'Microsoft/Edge/Application/msedge.exe',
        Path(program_files_x86) / 'Microsoft/Edge/Application/msedge.exe',
        Path(local_app_data) / 'Microsoft/Edge/Application/msedge.exe',
    ]
    if any(path and Path(path).exists() for path in edge_candidates):
        return 'msedge'
    chrome_candidates = [
        shutil.which('chrome'),
        shutil.which('chrome.exe'),
        Path(program_files) / 'Google/Chrome/Application/chrome.exe',
        Path(program_files_x86) / 'Google/Chrome/Application/chrome.exe',
        Path(local_app_data) / 'Google/Chrome/Application/chrome.exe',
    ]
    if any(path and Path(path).exists() for path in chrome_candidates):
        return 'chrome'
    return None


@pytest.mark.browser
def test_playwright_sender_against_local_fake_page(tmp_path):
    pytest.importorskip('playwright')
    channel = _browser_channel()
    if channel is None:
        pytest.skip('Google Chrome and Microsoft Edge are not installed')
    fixture = Path(__file__).parent / 'fixtures' / 'fake_live.html'
    config = PlaywrightConfig(
        user_data_dir=str(tmp_path / 'chrome-profile'),
        channel=channel,
        live_url=fixture.resolve().as_uri(),
        chat_input_selectors=["[data-testid='chat-input']"],
        focus_each_time=True,
    )
    sender = PlaywrightSender(config)
    try:
        sender.prepare()
        result = sender.send('199')
        assert result.ok
        assert sender.sent_messages_for_test() == ['199']
        for value in range(20):
            assert sender.send(str(value)).ok
        assert sender.sent_messages_for_test() == ['199'] + [str(value) for value in range(20)]
    finally:
        sender.close()


@pytest.mark.parametrize(
    'url,allowed',
    [
        ('https://www.tiktok.com/@seller/live', True),
        ('https://www.tiktok.com/@seller/video/123', False),
        ('https://example.com/@seller/live', False),
    ],
)
def test_tiktok_sender_validates_active_live_url(url, allowed):
    config = PlaywrightConfig(url_pattern='https://*.tiktok.com/@*/live*')
    sender = PlaywrightSender(config, expected_hosts=TIKTOK_HOSTS)

    class Page:
        def __init__(self, page_url):
            self.url = page_url

    sender.page = Page(url)
    if allowed:
        sender._validate_active_page()
    else:
        with pytest.raises(SenderPrepareError):
            sender._validate_active_page()
