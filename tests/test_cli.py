import pytest

from pricetyper.cli import _configure_tiktok_web, main
from pricetyper.config import AppConfig


def test_help_lists_all_commands(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    for name in ("run", "gui", "replay", "record", "calibrate", "discover", "latency"):
        assert name in output


def test_gui_help_documents_youtube_recognition_mode(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["gui", "--help"])
    assert exc.value.code == 0
    output = " ".join(capsys.readouterr().out.split())
    assert "--youtube-test" in output
    assert "lock all chat senders" in output
    assert "--asr-compare" in output
    assert "--whisper-model" in output


def test_asr_comparison_requires_youtube_test_mode(capsys):
    assert main(["gui", "--asr-compare"]) == 2
    assert "--asr-compare requires --youtube-test" in capsys.readouterr().err


def test_tiktok_web_mode_keeps_selected_browser_tab_and_starts_disarmed_dry_run():
    config = AppConfig()
    _configure_tiktok_web(config)
    assert config.audio.source == "browser_tab"
    assert config.run.dry_run is True
    assert config.run.start_armed is False
    assert config.sender.playwright.channel == "chrome"
    assert config.sender.playwright.attach == "launch"
    assert config.sender.playwright.live_url == ""
    assert config.sender.playwright.focus_each_time is False
    assert config.sender.playwright.url_pattern == "**/@*/live*"


def test_youtube_and_tiktok_modes_cannot_be_combined(capsys):
    assert main(["gui", "--youtube-test", "--tiktok-web"]) == 2
    assert "separate modes" in capsys.readouterr().err
