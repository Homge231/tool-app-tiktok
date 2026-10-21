from pathlib import Path

from pricetyper import windows_entry


def test_browser_setup_pages_match_selected_browser() -> None:
    assert windows_entry._browser_page("Microsoft Edge") == "edge://extensions/"
    assert windows_entry._browser_page("Google Chrome") == "chrome://extensions/"
    assert (
        windows_entry._browser_page("Cốc Cốc (chưa nghiệm thu)")
        == "chrome://extensions/"
    )
    assert windows_entry._browser_page("Chromium khác…") == "chrome://extensions/"


def test_browser_candidates_use_known_windows_install_locations(monkeypatch) -> None:
    monkeypatch.setattr(
        windows_entry.os,
        "environ",
        {
            "LOCALAPPDATA": r"C:\Users\test\AppData\Local",
            "ProgramFiles": r"C:\Program Files",
            "ProgramFiles(x86)": r"C:\Program Files (x86)",
        },
    )

    candidates = windows_entry._browser_candidates("Google Chrome")

    assert (
        Path(r"C:\Users\test\AppData\Local\Google\Chrome\Application\chrome.exe")
        in candidates
    )
    assert Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe") in candidates


def test_find_browser_executable_returns_existing_candidate(
    monkeypatch, tmp_path
) -> None:
    executable = tmp_path / "chrome.exe"
    executable.write_bytes(b"not executed by this test")
    monkeypatch.setattr(
        windows_entry, "_browser_candidates", lambda _browser: [executable]
    )

    assert windows_entry._find_browser_executable("Google Chrome") == executable
