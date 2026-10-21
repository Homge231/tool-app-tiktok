from __future__ import annotations

import os
import subprocess
import sys
import traceback
from pathlib import Path
from tkinter import StringVar, Tk, filedialog, messagebox, ttk

from pricetyper.asr.factory import create_asr_engine
from pricetyper.asr.zipformer_engine import MODEL_NAME
from pricetyper.config import load_config
from pricetyper.runtime_paths import resource_root, user_data_dir

_BROWSER_OPTIONS = (
    "Microsoft Edge",
    "Google Chrome",
    "Cốc Cốc (chưa nghiệm thu)",
    "Chromium khác…",
)


def _browser_page(browser: str) -> str:
    if browser == "Microsoft Edge":
        return "edge://extensions/"
    return "chrome://extensions/"


def _browser_candidates(browser: str) -> list[Path]:
    """Return common per-user and machine install locations for setup guidance."""
    env = os.environ
    roots = [
        Path(env[key])
        for key in ("LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)")
        if env.get(key)
    ]
    relative_paths = {
        "Microsoft Edge": (Path("Microsoft/Edge/Application/msedge.exe"),),
        "Google Chrome": (Path("Google/Chrome/Application/chrome.exe"),),
        "Cốc Cốc (chưa nghiệm thu)": (Path("CocCoc/Browser/Application/browser.exe"),),
    }.get(browser, ())
    candidates = [root / relative for root in roots for relative in relative_paths]

    # App Paths covers custom installation locations without walking the disk.
    app_path_names = {
        "Microsoft Edge": "msedge.exe",
        "Google Chrome": "chrome.exe",
        "Cốc Cốc (chưa nghiệm thu)": "browser.exe",
    }
    executable = app_path_names.get(browser)
    if executable and sys.platform == "win32":
        try:
            import winreg

            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                key_path = (
                    "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\"
                    f"{executable}"
                )
                try:
                    with winreg.OpenKey(hive, key_path) as key:
                        value, _ = winreg.QueryValueEx(key, None)
                    candidates.insert(0, Path(value))
                except OSError:
                    continue
        except ImportError:
            pass

    seen: set[str] = set()
    unique: list[Path] = []
    for candidate in candidates:
        normalized = str(candidate).casefold()
        if normalized not in seen:
            seen.add(normalized)
            unique.append(candidate)
    return unique


def _find_browser_executable(browser: str) -> Path | None:
    for candidate in _browser_candidates(browser):
        if candidate.is_file():
            return candidate
    return None


def _available_browser_options() -> tuple[str, ...]:
    installed = [
        browser
        for browser in _BROWSER_OPTIONS[:-1]
        if _find_browser_executable(browser) is not None
    ]
    installed.append(_BROWSER_OPTIONS[-1])
    return tuple(installed)


def _show_startup_error(message: str) -> None:
    root = Tk()
    root.withdraw()
    try:
        messagebox.showerror("NumberTyper không khởi động được", message, parent=root)
    finally:
        root.destroy()


def _write_fatal_error(path: Path, exc_type, exc, tb) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write("\n--- Lỗi khởi động NumberTyper ---\n")
        traceback.print_exception(exc_type, exc, tb, file=stream)


def _required_resources() -> list[Path]:
    root = resource_root()
    model_dir = root / "models" / MODEL_NAME
    return [
        model_dir / "encoder.int8.onnx",
        model_dir / "decoder.onnx",
        model_dir / "joiner.int8.onnx",
        model_dir / "tokens.txt",
        root / "models" / "silero_vad.onnx",
        root / "browser_extension" / "manifest.json",
    ]


def _show_first_run(extension_dir: Path, completion_marker: Path) -> bool:
    """Show the manual extension setup required by this private preview."""
    root = Tk()
    root.title("NumberTyper — thiết lập lần đầu")
    root.geometry("640x500")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", root.destroy)

    content = ttk.Frame(root, padding=18)
    content.pack(fill="both", expand=True)
    ttk.Label(
        content,
        text="Chào mừng đến với NumberTyper",
        font=("Segoe UI", 17, "bold"),
    ).pack(anchor="w", pady=(0, 10))
    ttk.Label(
        content,
        text=(
            "Đây là bản preview cá nhân. Để nghe âm thanh của tab, bạn cần nạp "
            "tiện ích NumberTyper vào trình duyệt một lần. Ứng dụng không tự cài "
            "tiện ích; bản extension chưa được phát hành trên cửa hàng. Khi có "
            "bản cửa hàng, trình duyệt vẫn sẽ hỏi bạn xác nhận quyền."
        ),
        wraplength=525,
        justify="left",
    ).pack(anchor="w", pady=(0, 10))
    browser_row = ttk.Frame(content)
    browser_row.pack(fill="x", pady=(0, 8))
    ttk.Label(browser_row, text="Trình duyệt:").pack(side="left")
    browser_options = _available_browser_options()
    browser_name = StringVar(value=browser_options[0])
    browser_select = ttk.Combobox(
        browser_row,
        textvariable=browser_name,
        values=browser_options,
        state="readonly",
        width=27,
    )
    browser_select.pack(side="left", padx=(8, 10))

    instructions = (
        "1. Mở trang quản lý tiện ích bằng nút bên dưới.\n"
        "2. Với bản preview này, bật Chế độ nhà phát triển → Nạp tiện ích đã "
        "giải nén.\n"
        "3. Chọn thư mục NumberTyper Tab Audio.\n"
        "4. Mở TikTok Live, bấm biểu tượng NumberTyper và bắt đầu thu tab.\n"
        "5. App mặc định chạy thử/chưa kích hoạt nên không điền số. Muốn điền, "
        "kết nối và kiểm tra tab, bỏ chọn Chạy thử rồi nhấn F8. Gửi Enter cần "
        "bật lựa chọn riêng; F10 dừng khẩn."
    )
    ttk.Label(
        content,
        text=instructions,
        wraplength=590,
        justify="left",
    ).pack(anchor="w", pady=(0, 12))
    ttk.Label(
        content,
        text=(
            "Hỗ trợ trình duyệt chưa được nghiệm thu đầy đủ. Tiện ích chỉ hoạt "
            "động với trình duyệt Chromium tương thích; không dùng microphone "
            "hoặc âm thanh toàn hệ thống thay thế."
        ),
        wraplength=590,
        justify="left",
    ).pack(anchor="w", pady=(0, 10))

    actions = ttk.Frame(content)
    actions.pack(fill="x", side="bottom")

    def open_extension_folder() -> None:
        os.startfile(str(extension_dir))

    def open_extensions_page() -> None:
        browser = browser_name.get()
        executable = _find_browser_executable(browser)
        if browser == "Chromium khác…":
            selected = filedialog.askopenfilename(
                parent=root,
                title="Chọn tệp chạy trình duyệt Chromium",
                filetypes=[("Ứng dụng Windows", "*.exe")],
            )
            executable = Path(selected) if selected else None
        if executable is None or not executable.is_file():
            messagebox.showinfo(
                "Chưa tìm thấy trình duyệt",
                "Hãy chọn đúng trình duyệt hoặc dùng mục Chromium khác… để chọn "
                "tệp .exe. NumberTyper không tự cài extension vào trình duyệt.",
                parent=root,
            )
            return
        try:
            subprocess.Popen(
                [str(executable), _browser_page(browser)],
                close_fds=True,
            )
        except OSError as exc:
            messagebox.showerror(
                "Không mở được trang tiện ích",
                f"Không thể mở {browser}: {exc}",
                parent=root,
            )

    def copy_extension_path() -> None:
        root.clipboard_clear()
        root.clipboard_append(str(extension_dir))
        root.update_idletasks()
        messagebox.showinfo(
            "Đã sao chép",
            "Đường dẫn thư mục extension đã được sao chép.",
            parent=root,
        )

    ttk.Button(
        browser_row,
        text="Mở trang tiện ích",
        command=open_extensions_page,
    ).pack(side="left")

    def continue_to_app() -> None:
        completion_marker.parent.mkdir(parents=True, exist_ok=True)
        completion_marker.write_text("shown\n", encoding="utf-8")
        root.destroy()

    ttk.Button(
        actions,
        text="Mở thư mục tiện ích",
        command=open_extension_folder,
    ).pack(side="left")
    ttk.Button(
        actions,
        text="Sao chép đường dẫn",
        command=copy_extension_path,
    ).pack(side="left", padx=(8, 0))
    ttk.Button(
        actions,
        text="Mở NumberTyper",
        command=continue_to_app,
    ).pack(side="right")
    root.mainloop()
    return completion_marker.exists()


def main() -> int:
    data_dir = user_data_dir()
    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    startup_log = log_dir / "startup.log"
    fatal_log = log_dir / "crash.log"

    missing = [path for path in _required_resources() if not path.is_file()]
    if missing:
        listed = "\n".join(str(path) for path in missing)
        _show_startup_error(
            "Bản cài NumberTyper thiếu tài nguyên bắt buộc:\n\n"
            f"{listed}\n\nHãy cài lại ứng dụng hoặc liên hệ người cung cấp bản cài."
        )
        return 1

    smoke_check = sys.argv[1:] == ["--smoke-check"]
    first_run_marker = data_dir / "first_run_complete"
    if (
        not smoke_check
        and not first_run_marker.exists()
        and not _show_first_run(resource_root() / "browser_extension", first_run_marker)
    ):
        return 0

    # A windowed PyInstaller build has no console streams. Keep CLI startup
    # diagnostics local so failures can be shown to the user without a shell.
    previous_stdout, previous_stderr = sys.stdout, sys.stderr
    try:
        with startup_log.open("a", encoding="utf-8") as stream:
            sys.stdout = stream
            sys.stderr = stream
            if smoke_check:
                engine = create_asr_engine(load_config(), emit_partials=False)
                del engine
                print("SMOKE CHECK OK: local ASR and VAD models loaded")
                result = 0
            else:
                from pricetyper.cli import main as cli_main

                result = cli_main(["gui", "--tiktok-web"])
    except Exception as exc:  # noqa: BLE001 - report any startup crash to the user
        _write_fatal_error(fatal_log, type(exc), exc, exc.__traceback__)
        _show_startup_error(
            f"NumberTyper gặp lỗi khi khởi động. Chi tiết đã được lưu tại:\n{fatal_log}"
        )
        return 1
    finally:
        sys.stdout, sys.stderr = previous_stdout, previous_stderr

    if result:
        details = ""
        if startup_log.exists():
            lines = startup_log.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
            details = "\n".join(lines[-8:])
        message = f"Không thể mở NumberTyper (mã lỗi {result})."
        if details:
            message += f"\n\n{details}"
        message += f"\n\nNhật ký: {startup_log}"
        _show_startup_error(message)
    return int(result or 0)


if __name__ == "__main__":
    raise SystemExit(main())
