from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from pricetyper.asr.factory import create_asr_engine
from pricetyper.audio.browser_tab import TIKTOK_HOSTS, YOUTUBE_HOSTS
from pricetyper.cli import (
    _configure_tiktok_web,
    _make_sender,
    _make_source,
)
from pricetyper.controller import Controller
from pricetyper.logging_utils import JsonlLogger
from pricetyper.pipeline import Pipeline
from pricetyper.senders.browser_extension_sender import BrowserExtensionSender
from pricetyper.senders.null_sender import NullSender
from pricetyper.ui.audio_meter import format_audio_level
from pricetyper.ui.formatting import format_vnd
from pricetyper.ui.hotkeys import register
from pricetyper.ui.recognition_display import RecognitionDisplay


def _is_unverified_send_error(error: object) -> bool:
    return isinstance(error, str) and error.startswith("send_unverified:")


def launch(
    config,
    youtube_test=False,
    tiktok_web=False,
    asr_compare=False,
    whisper_model="small",
):
    if youtube_test and tiktok_web:
        raise ValueError("YouTube test and TikTok Web are separate modes")
    if youtube_test:
        config.audio.source = "browser_tab"
        config.run.dry_run = True
        config.run.start_armed = False
    elif tiktok_web:
        _configure_tiktok_web(config)
    elif asr_compare:
        raise ValueError("ASR comparison is available only in YouTube test mode")

    root = tk.Tk()
    # TikTok mode defaults to auto-submit after the user connects the tab.
    # The app still starts disarmed and requires an explicit F8 press.
    submit_live = tk.BooleanVar(value=tiktok_web)
    root.title(
        "NumberTyper — YouTube · Zipformer-VI"
        if youtube_test
        else "NumberTyper — TikTok Web · Zipformer-VI"
        if tiktok_web
        else f"NumberTyper · {config.asr.engine.title()}"
    )
    root.geometry("680x790" if tiktok_web else "650x710")
    root.minsize(580, 660)

    logger = JsonlLogger(config.run.log_dir, config.run.log_level)
    source = _make_source(
        config,
        expected_hosts=(
            YOUTUBE_HOSTS if youtube_test else TIKTOK_HOSTS if tiktok_web else None
        ),
    )
    tiktok_sender = (
        BrowserExtensionSender(source, config.sender.playwright) if tiktok_web else None
    )
    sender = (
        NullSender()
        if youtube_test or tiktok_web or config.run.dry_run
        else _make_sender(config)
    )
    controller = Controller(sender, logger)
    asr = create_asr_engine(config, emit_partials=not tiktok_web)
    comparison_session = None
    if asr_compare:
        from pricetyper.asr.comparison import ASRComparisonSession

        comparison_session = ASRComparisonSession(
            config, whisper_model_name=whisper_model
        )
    pipeline = Pipeline(
        source,
        asr,
        sender,
        config,
        controller,
        logger,
        audio_observer=comparison_session,
        log_transcript_text=not asr_compare,
        candidate_scope="number" if youtube_test or tiktok_web else "price",
        send_final_only=tiktok_web,
        draft_only=tiktok_web,
    )

    state = tk.StringVar(
        value=(
            "NHẬN DIỆN SỐ — KHÔNG GỬI"
            if youtube_test
            else "NUMBERTYPER — CHẠY THỬ · GỬI ĐÃ KHÓA"
            if tiktok_web
            else "ĐANG NGHE — KHÔNG GỬI"
        )
    )
    recognized = tk.StringVar(value="—")
    interim = tk.StringVar(value="—")
    asr_status = tk.StringVar(value="Đang chờ audio từ tab…" if tiktok_web else "—")
    asr_status_state = {
        "last_event_ns": 0,
        "speech_active": False,
        "speech_started_ns": None,
        "stall_warning": False,
    }
    provisional_candidate = tk.StringVar(value="—")
    candidate = tk.StringVar(value="—")
    asr_chunk_delay = tk.StringVar(value="—")
    recognition_display = RecognitionDisplay()
    tab_capture_mode = youtube_test or tiktok_web
    audio_status = tk.StringVar(
        value="Đang chờ extension…" if tab_capture_mode else "—"
    )
    audio_level = tk.StringVar(value="Chưa nhận mẫu audio" if tab_capture_mode else "—")
    latest_sent = tk.StringVar(value="—")
    latency = tk.StringVar(value="—")
    totals = {"sent": 0, "skipped": {}}
    poll_interval_ms = 10 if tiktok_web else 50

    state_label = ttk.Label(
        root, textvariable=state, font=("Segoe UI", 18, "bold"), anchor="center"
    )
    state_label.pack(fill="x", padx=12, pady=(12, 4))
    warning_frame = tk.Frame(
        root, bg="#fff3cd", highlightbackground="#d9a300", highlightthickness=1
    )
    warning_message = tk.Label(
        warning_frame,
        text="",
        bg="#fff3cd",
        fg="#664d03",
        anchor="w",
        justify="left",
        wraplength=570,
        padx=8,
        pady=6,
        font=("Segoe UI", 9, "bold"),
    )
    warning_message.pack(side="left", fill="x", expand=True)
    warning_code = {"value": None}
    warning_level = {"value": None}

    def clear_health_warning():
        warning_code["value"] = None
        warning_level["value"] = None
        warning_frame.pack_forget()

    ttk.Button(warning_frame, text="Ẩn", command=clear_health_warning).pack(
        side="right", padx=6, pady=4
    )

    def show_health_warning(code, message, level="warning"):
        priority = {"info": 0, "warning": 1, "error": 2}
        if warning_frame.winfo_manager() and priority.get(level, 1) < priority.get(
            warning_level["value"], 1
        ):
            return
        is_new_warning = (
            not warning_frame.winfo_manager() or warning_code["value"] != code
        )
        warning_code["value"] = code
        warning_level["value"] = level
        warning_message.configure(text=message)
        if level == "error":
            warning_frame.configure(bg="#f8d7da", highlightbackground="#b02a37")
            warning_message.configure(bg="#f8d7da", fg="#842029")
        elif level == "info":
            warning_frame.configure(bg="#d1e7dd", highlightbackground="#198754")
            warning_message.configure(bg="#d1e7dd", fg="#0f5132")
        else:
            warning_frame.configure(bg="#fff3cd", highlightbackground="#d9a300")
            warning_message.configure(bg="#fff3cd", fg="#664d03")
        if not warning_frame.winfo_manager():
            warning_frame.pack(fill="x", padx=12, pady=(0, 4), after=state_label)
        if is_new_warning and level != "info":
            try:
                import winsound

                winsound.MessageBeep(winsound.MB_ICONWARNING)
            except (ImportError, OSError, RuntimeError):
                try:
                    root.bell()
                except tk.TclError:
                    pass

    send_button = ttk.Button(
        root,
        text=(
            "Chỉ nhận số · gửi đã khóa"
            if youtube_test
            else "Bật/Tắt điền số (F8)"
            if tiktok_web
            else "Bật/Tắt gửi (F8)"
        ),
        command=lambda: threading.Thread(target=toggle, daemon=True).start(),
    )
    send_button.pack(fill="x", padx=16, pady=4)
    if youtube_test:
        send_button.configure(state="disabled")

    sender_ready = threading.Event()
    tiktok_prepare_lock = threading.Lock()
    tiktok_preparing = False
    prepare_button = None
    if tiktok_web:
        prepare_button = ttk.Button(
            root,
            text="Kết nối tab TikTok đang nghe (chỉ kiểm tra)",
            command=lambda: prepare_tiktok_sender(),
        )
        prepare_button.pack(fill="x", padx=16, pady=(4, 2))
        ttk.Label(
            root,
            text=(
                "Mở TikTok Live trong trình duyệt, bấm extension và bắt đầu thu tab. "
                "App nhận dạng số cuối câu trên đúng tab đó. Mặc định chọn tự gửi "
                "bằng Enter sau khi kết nối; bỏ chọn nếu chỉ muốn điền số. Dòng Nghe được chỉ đổi sau khi "
                "VAD chốt câu; bấm F8 hoặc kết nối tab không dừng nhận dạng. "
                "Chỉ ASR final mới được xử lý. "
                "TikTok tắt giải mã partial lặp lại để giảm nghẽn audio; "
                "đoạn nói liên tục quá 12 giây chỉ được xem trước, không gửi. "
                "Ô nhập phải khớp duy nhất. F8 bật/tắt; F10 dừng khẩn. "
                "Thời gian trên app chưa tính lúc VAD đợi im lặng hoặc lúc TikTok phân phối comment."
            ),
            wraplength=640,
            justify="left",
        ).pack(fill="x", padx=16, pady=(0, 4))

    dry = tk.BooleanVar(value=config.run.dry_run)

    def set_dry_run():
        requested = dry.get()
        if controller.armed.is_set():
            controller.disarm()
        if requested and tiktok_web and submit_live.get():
            submit_live.set(False)
            tiktok_sender.submit_enabled = False
            pipeline.draft_only = True
            send_button.configure(text="Bật/Tắt điền số (F8)")
            count_label.set(
                f"Lượt điền: {totals['sent']} | Bỏ qua: {sum(totals['skipped'].values())}"
            )
        if tiktok_web:
            if requested:
                replacement = NullSender()
                pipeline.sender = replacement
                controller.sender = replacement
                config.run.dry_run = True
            elif not sender_ready.is_set():
                dry.set(True)
                messagebox.showinfo(
                    "Chưa kết nối tab",
                    "Hãy bắt đầu capture từ extension và kiểm tra tab TikTok trước. App vẫn disarmed cho tới khi bạn nhấn F8.",
                    parent=root,
                )
                return
            else:
                pipeline.sender = tiktok_sender
                controller.sender = tiktok_sender
                config.run.dry_run = False
        elif requested:
            replacement = NullSender()
            pipeline.sender = replacement
            controller.sender = replacement
            config.run.dry_run = True
        elif isinstance(pipeline.sender, NullSender):
            try:
                replacement = _make_sender(config)
                pipeline.sender = replacement
                controller.sender = replacement
                config.run.dry_run = False
            except Exception as exc:
                dry.set(True)
                messagebox.showerror("Không thể tắt chạy thử", str(exc), parent=root)
                return
        else:
            config.run.dry_run = False
        if controller.armed.is_set():
            state.set(
                "CHẠY THỬ — KHÔNG GỬI COMMENT"
                if config.run.dry_run and tiktok_web
                else "CHẠY THỬ — KHÔNG GỬI THẬT"
                if config.run.dry_run
                else "ĐANG BẬT GỬI COMMENT"
                if tiktok_web and submit_live.get()
                else "ĐANG BẬT ĐIỀN SỐ"
                if tiktok_web
                else "ĐANG BẬT GỬI"
            )
        elif tiktok_web:
            state.set(
                (
                    "TAB SẴN SÀNG — NHẤN F8 ĐỂ GỬI COMMENT"
                    if submit_live.get()
                    else "TAB SẴN SÀNG — NHẤN F8 ĐỂ ĐIỀN SỐ"
                )
                if sender_ready.is_set() and not config.run.dry_run
                else "NUMBERTYPER — CHẠY THỬ · GỬI ĐÃ KHÓA"
            )
        add_log("Chạy thử: " + ("bật" if config.run.dry_run else "tắt"))

    dry_check = ttk.Checkbutton(
        root,
        text=(
            "Chạy thử — không gửi comment thật"
            if tiktok_web
            else "Chạy thử — không gửi thật"
        ),
        variable=dry,
        command=set_dry_run,
    )
    dry_check.pack(anchor="w", padx=18)
    if youtube_test:
        dry_check.configure(state="disabled")

    submit_mode_check = None
    if tiktok_web:
        submit_mode_check = ttk.Checkbutton(
            root,
            text="Tự gửi comment bằng Enter sau khi nhận số cuối câu",
            variable=submit_live,
            command=lambda: set_tiktok_submit_mode(),
            state="disabled",
        )
        submit_mode_check.pack(anchor="w", padx=18)

    vars_by_key = {}
    if youtube_test:
        settings = ttk.LabelFrame(root, text="Chế độ số — bộ lọc giá đã tắt")
        settings.pack(fill="x", padx=12, pady=8)
        ttk.Label(
            settings,
            text=(
                "Hiển thị số parser trích được, kể cả số nhỏ và số sau từ ‘số’; "
                "không gắn đơn vị tiền."
            ),
            wraplength=600,
        ).pack(anchor="w", padx=8, pady=6)
    else:
        settings = ttk.LabelFrame(
            root,
            text=(
                "Chế độ số — không áp dụng ngưỡng giá"
                if tiktok_web
                else "Phạm vi giá bằng đồng — áp dụng ngay, không ghi vào tệp"
            ),
        )
        settings.pack(fill="x", padx=12, pady=8)
        if tiktok_web:
            ttk.Label(
                settings,
                text=(
                    "Xử lý số cuối câu, kể cả số nhỏ như 9; không gắn đơn vị tiền. "
                    "Cooldown và giới hạn lượt vẫn áp dụng."
                ),
                wraplength=600,
            ).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=6)
            fields = [
                ("Cooldown cùng số (giây)", "cooldown_same_s", float),
                ("Cooldown mọi số (giây)", "cooldown_any_s", float),
                ("Tối đa thao tác mỗi phút", "max_sends_per_min", int),
            ]
            field_start_row = 1
        else:
            fields = [
                ("Giá nhỏ nhất (₫)", "min_value", int),
                ("Giá lớn nhất (₫)", "max_value", int),
                ("Cooldown cùng giá (giây)", "cooldown_same_s", float),
                ("Cooldown mọi giá (giây)", "cooldown_any_s", float),
                ("Tối đa gửi mỗi phút", "max_sends_per_min", int),
            ]
            field_start_row = 0
        for row, (label, key, cast) in enumerate(fields):
            ttk.Label(settings, text=label).grid(
                row=field_start_row + row, column=0, sticky="w", padx=8, pady=3
            )
            variable = tk.StringVar(value=str(getattr(config.decision, key)))
            vars_by_key[key] = (variable, cast)
            entry = ttk.Entry(settings, textvariable=variable, width=14)
            entry.grid(row=field_start_row + row, column=1, sticky="e", padx=8, pady=3)
            entry.bind("<Return>", lambda _event, k=key: update_setting(k))
            entry.bind("<FocusOut>", lambda _event, k=key: update_setting(k))
        settings.columnconfigure(0, weight=1)

    status_frame = ttk.LabelFrame(root, text="Trạng thái nhận dạng")
    status_frame.pack(fill="x", padx=12, pady=4)
    candidate_label = (
        "Số trích được" if youtube_test or tiktok_web else "Giá trích được (₫)"
    )
    if youtube_test:
        visible_rows = [
            ("Nghe được (đã chốt)", recognized),
            ("Đang nghe (tạm thời)", interim),
            ("Số tạm · từ ASR chưa chốt", provisional_candidate),
            (candidate_label + " · từ câu đã chốt", candidate),
            ("ASR: audio chunk → kết quả (ms)", asr_chunk_delay),
        ]
        visible_rows.append(("Audio tab", audio_status))
        visible_rows.append(("Mức tín hiệu tab", audio_level))
    else:
        visible_rows = [
            ("Nghe được (câu đã chốt)" if tiktok_web else "Nghe được", recognized),
            (candidate_label, candidate),
            (
                "Số gần nhất" if tiktok_web else "Đã gửi gần nhất",
                latest_sent,
            ),
            (
                "Chunk đóng VAD → thao tác (ms)"
                if tiktok_web
                else "Độ trễ gần nhất (ms)",
                latency,
            ),
        ]
        if tiktok_web:
            visible_rows.extend(
                [
                    ("Trạng thái ASR", asr_status),
                    ("Audio tab", audio_status),
                    ("Mức tín hiệu tab", audio_level),
                ]
            )
    for row, (label, variable) in enumerate(visible_rows):
        ttk.Label(status_frame, text=label + ":").grid(
            row=row, column=0, sticky="nw", padx=8, pady=3
        )
        ttk.Label(status_frame, textvariable=variable, wraplength=470).grid(
            row=row, column=1, sticky="w", padx=8, pady=3
        )
    status_frame.columnconfigure(1, weight=1)

    count_label = tk.StringVar(
        value=(
            "Gửi tin nhắn: đã khóa"
            if youtube_test
            else "Lượt điền: 0 | Bỏ qua: 0"
            if tiktok_web
            else "Đã gửi: 0 | Bỏ qua: 0"
        )
    )
    ttk.Label(root, textvariable=count_label).pack(anchor="w", padx=16, pady=4)
    comparison_window = None
    if asr_compare:
        from pricetyper.ui.asr_comparison import ASRComparisonWindow

        comparison_window = ASRComparisonWindow(
            root, comparison_session, whisper_model_name=whisper_model
        )
        ttk.Button(
            root,
            text="Benchmark audio gốc/khử nhiễu · Vosk / Whisper / Zipformer",
            command=comparison_window.show,
        ).pack(fill="x", padx=16, pady=4)
    if not youtube_test:
        ttk.Button(root, text="Dừng khẩn (F10)", command=controller.panic).pack(
            fill="x", padx=16, pady=4
        )
    log_view = tk.Text(root, height=10, state="disabled", wrap="word")
    log_view.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def add_log(message):
        log_view.configure(state="normal")
        log_view.insert("end", message + "\n")
        line_count = int(log_view.index("end-1c").split(".")[0])
        if line_count > 200:
            log_view.delete("1.0", f"{line_count - 200}.0")
        log_view.see("end")
        log_view.configure(state="disabled")

    def set_tiktok_submit_mode():
        if not tiktok_web or tiktok_sender is None:
            return
        requested = submit_live.get()
        if controller.armed.is_set():
            submit_live.set(not requested)
            messagebox.showinfo(
                "Hãy tắt trước",
                "Chỉ đổi chế độ gửi khi app đang disarmed. Nhấn F8 để tắt rồi thử lại.",
                parent=root,
            )
            return
        if requested and (not sender_ready.is_set() or config.run.dry_run):
            submit_live.set(False)
            messagebox.showinfo(
                "Tab chưa sẵn sàng",
                "Hãy kết nối và kiểm tra ô nhập TikTok trước khi bật gửi comment.",
                parent=root,
            )
            return
        tiktok_sender.submit_enabled = requested
        pipeline.draft_only = not requested
        send_button.configure(
            text=(
                "Bật/Tắt gửi comment bằng Enter (F8)"
                if requested
                else "Bật/Tắt điền số (F8)"
            )
        )
        count_label.set(
            f"{'Lệnh gửi Enter' if requested else 'Lượt điền'}: {totals['sent']} | "
            f"Bỏ qua: {sum(totals['skipped'].values())}"
        )
        if sender_ready.is_set() and not config.run.dry_run:
            state.set(
                "TAB SẴN SÀNG — NHẤN F8 ĐỂ GỬI COMMENT"
                if requested
                else "TAB SẴN SÀNG — NHẤN F8 ĐỂ ĐIỀN SỐ"
            )
        add_log(
            "Đã bật gửi comment bằng Enter; việc comment xuất hiện chưa được xác nhận."
            if requested
            else "Đã chọn chế độ chỉ điền số, không gửi comment."
        )

    def update_setting(key):
        variable, cast = vars_by_key[key]
        try:
            value = cast(variable.get())
            if key in {"min_value", "max_value"} and value < 1:
                raise ValueError("Giá trị phải lớn hơn hoặc bằng 1")
            if key == "max_value" and value > 999_999_999:
                raise ValueError("Giá tối đa là 999.999.999 ₫")
            if key.startswith("cooldown") and value < 0:
                raise ValueError("Cooldown không được âm")
            if key == "max_sends_per_min" and not 1 <= value <= 60:
                raise ValueError("Giới hạn phải từ 1 đến 60")
            proposed_min = value if key == "min_value" else config.decision.min_value
            proposed_max = value if key == "max_value" else config.decision.max_value
            if proposed_min > proposed_max:
                raise ValueError("Giá nhỏ nhất phải nhỏ hơn hoặc bằng giá lớn nhất")
            pipeline.update_q.put({key: value})
            add_log(f"Đã áp dụng {key}={value}")
        except ValueError as exc:
            variable.set(str(getattr(config.decision, key)))
            add_log(f"Giá trị không hợp lệ: {exc}")

    def toggle():
        if tiktok_web and not config.run.dry_run and not sender_ready.is_set():
            root.after(
                0,
                lambda: add_log(
                    "Chưa sẵn sàng: hãy kết nối extension với tab TikTok Live trước."
                ),
            )
            return
        try:
            controller.toggle()
        except Exception as exc:
            pipeline.ui_q.put(
                {
                    "kind": "error",
                    "message": (
                        f"{'Không thể bật gửi comment' if submit_live.get() else 'Không thể bật điền số'}: {exc}"
                        if tiktok_web
                        else f"Không thể bật gửi: {exc}"
                    ),
                }
            )

    def prepare_tiktok_sender():
        nonlocal tiktok_preparing
        if not tiktok_web or tiktok_sender is None:
            return
        with tiktok_prepare_lock:
            if tiktok_preparing or sender_ready.is_set():
                return
            tiktok_preparing = True
        if controller.armed.is_set():
            controller.disarm()
        config.run.dry_run = False
        dry.set(False)
        pipeline.sender = tiktok_sender
        controller.sender = tiktok_sender
        prepare_button.configure(state="disabled", text="Đang kiểm tra tab và ô nhập…")
        state.set("ĐANG KIỂM TRA TAB — CHƯA ĐIỀN")
        add_log("Đã rời chạy thử; kiểm tra kết nối và ô nhập trong tab đang capture.")

        def prepare_worker():
            try:
                tiktok_sender.prepare()
            except Exception as exc:
                root.after(0, preparation_failed, str(exc))
            else:
                sender_ready.set()
                root.after(0, preparation_succeeded)

        threading.Thread(
            target=prepare_worker, name="tiktok-sender-prepare", daemon=True
        ).start()

    def preparation_failed(error):
        nonlocal tiktok_preparing
        with tiktok_prepare_lock:
            tiktok_preparing = False
        config.run.dry_run = True
        dry.set(True)
        submit_live.set(False)
        if tiktok_sender is not None:
            tiktok_sender.submit_enabled = False
        pipeline.draft_only = True
        if submit_mode_check is not None:
            submit_mode_check.configure(state="disabled")
        send_button.configure(text="Bật/Tắt điền số (F8)")
        replacement = NullSender()
        pipeline.sender = replacement
        controller.sender = replacement
        prepare_button.configure(
            state="normal", text="Kết nối tab TikTok đang nghe (chỉ kiểm tra)"
        )
        state.set("NUMBERTYPER — CHẠY THỬ · GỬI ĐÃ KHÓA")
        add_log(
            (
                "Không thể chuẩn bị thao tác điền: "
                if tiktok_web
                else "Không thể chuẩn bị sender: "
            )
            + error
        )
        messagebox.showerror("Không thể kết nối tab TikTok", error, parent=root)

    def preparation_succeeded():
        nonlocal tiktok_preparing
        with tiktok_prepare_lock:
            tiktok_preparing = False
        prepare_button.configure(
            state="disabled", text="Tab đã kết nối · thao tác vẫn tắt"
        )
        if submit_mode_check is not None:
            submit_mode_check.configure(state="normal")
            set_tiktok_submit_mode()
        else:
            state.set("TAB SẴN SÀNG — NHẤN F8 ĐỂ ĐIỀN SỐ")
        add_log("Tab TikTok Live và ô nhập đã sẵn sàng; app vẫn disarmed cho tới F8.")

    def on_state(new_state):
        pipeline.ui_q.put({"kind": "state", "state": new_state.value})

    controller.subscribe(on_state)
    keyboard_module = None
    if not youtube_test:
        try:
            keyboard_module = register(
                controller, config.run.hotkeys["toggle"], config.run.hotkeys["panic"]
            )
        except Exception as exc:
            add_log(f"Không thể đăng ký hotkey: {exc}")

    last_overflow_count = 0
    had_bridge_connection = False
    was_bridge_connected = False

    def poll():
        nonlocal last_overflow_count, had_bridge_connection, was_bridge_connected
        if tab_capture_mode:
            session = source.session
            bridge_connected = source.connected and session is not None
            audio_status.set(
                (
                    f"Bridge đã kết nối · {session['browser']} · audio + hành động số"
                    if tiktok_web
                    else f"Bridge đã kết nối · {session['browser']}"
                )
                if bridge_connected
                else "Đang chờ extension kết nối…"
            )
            if bridge_connected and had_bridge_connection and not was_bridge_connected:
                show_health_warning(
                    "bridge_reconnected",
                    "Audio tab đã kết nối lại. App vẫn disarm; hãy kiểm tra số nhận dạng trước khi bật lại.",
                    level="info",
                )
            elif was_bridge_connected and not bridge_connected:
                pipeline.report_audio_gap(
                    reason="browser_bridge_disconnected",
                    event="audio_gap",
                    message=(
                        "Mất kết nối audio tab. App đã tắt thao tác và không còn nhận "
                        "audio; hãy kết nối lại extension rồi kiểm tra trạng thái."
                    ),
                )
            if bridge_connected:
                had_bridge_connection = True
            was_bridge_connected = bridge_connected
            if source.overflow_count > last_overflow_count:
                dropped = source.overflow_count - last_overflow_count
                pipeline.report_audio_gap(
                    reason="browser_bridge_queue_full",
                    dropped_chunks=dropped,
                    message=(
                        f"Bridge quá tải: đã bỏ {dropped} chunk audio cũ. "
                        "App đã reset nhận dạng và tắt thao tác để tránh dùng câu bị đứt."
                    ),
                )
                last_overflow_count = source.overflow_count
            if (
                tiktok_web
                and sender_ready.is_set()
                and not source.tiktok_live_connected
            ):
                controller.disarm()
                sender_ready.clear()
                config.run.dry_run = True
                dry.set(True)
                replacement = NullSender()
                pipeline.sender = replacement
                controller.sender = replacement
                prepare_button.configure(
                    state="normal", text="Kết nối tab TikTok đang nghe (chỉ kiểm tra)"
                )
                submit_live.set(False)
                tiktok_sender.submit_enabled = False
                pipeline.draft_only = True
                if submit_mode_check is not None:
                    submit_mode_check.configure(state="disabled")
                send_button.configure(text="Bật/Tắt điền số (F8)")
                state.set("NUMBERTYPER — TAB NGẮT · GỬI ĐÃ KHÓA")
                add_log(
                    "Tab đã ngắt hoặc đổi phiên; đã disarm, tắt gửi và khóa thao tác."
                )
        try:
            while True:
                item = pipeline.ui_q.get_nowait()
                kind = item["kind"]
                if kind == "asr":
                    if tiktok_web:
                        asr_status_state["last_event_ns"] = time.monotonic_ns()
                        if warning_code["value"] == "asr_stalled":
                            clear_health_warning()
                            add_log(
                                "ASR đã có kết quả trở lại; thao tác vẫn disarm, hãy kiểm tra số trước khi bật lại."
                            )
                        asr_status_state["stall_warning"] = False
                        asr_status.set(
                            "Bản xem trước · chưa dùng để điền/gửi"
                            if item["event_kind"] == "partial"
                            else "Đã chốt câu · có thể trích số"
                        )
                    if youtube_test:
                        recognition_display.on_asr(item["event_kind"], item["text"])
                        recognized.set(recognition_display.final_text)
                        interim.set(recognition_display.partial_text)
                    else:
                        recognized.set(item["text"][:80] or "—")
                elif kind == "audio_level" and tab_capture_mode:
                    audio_level.set(format_audio_level(item["rms"]))
                    if (
                        tiktok_web
                        and not asr_status_state["stall_warning"]
                        and (
                            time.monotonic_ns() - asr_status_state["last_event_ns"]
                            >= 1_500_000_000
                        )
                    ):
                        asr_status.set(
                            "Tab có tín hiệu · Zipformer chờ VAD chốt câu; không hiện từng từ"
                            if item["rms"] >= 10
                            else "Đang nhận audio tab · tín hiệu hiện rất thấp"
                        )
                elif kind == "asr_activity" and tiktok_web:
                    active = bool(item["active"])
                    asr_status_state["speech_active"] = active
                    asr_status_state["speech_started_ns"] = (
                        time.monotonic_ns() if active else None
                    )
                    if active and not asr_status_state["stall_warning"]:
                        asr_status.set(
                            "Có lời nói · Zipformer đang chờ kết quả/chốt câu"
                        )
                elif kind == "audio_overflow":
                    add_log(item["message"])
                    show_health_warning("audio_gap", item["message"])
                elif kind == "health_warning":
                    add_log(item["message"])
                    show_health_warning(
                        item["code"], item["message"], item.get("level", "warning")
                    )
                elif kind == "health_recovered":
                    add_log(item["message"])
                    if warning_code["value"] == item["code"]:
                        clear_health_warning()
                elif kind == "parse":
                    if youtube_test:
                        recognition_display.on_candidate(
                            item["event_kind"], item["candidate"]
                        )
                        provisional = recognition_display.provisional_candidate
                        provisional_candidate.set(
                            provisional if provisional.isdecimal() else "—"
                        )
                        value = recognition_display.candidate
                        candidate.set(value if value.isdecimal() else "—")
                        asr_chunk_delay.set(
                            f"{item['asr_chunk_delay_ms']:.1f} ms · chưa gồm chờ chốt"
                        )
                    else:
                        candidate.set(
                            (
                                str(item["candidate"])
                                if tiktok_web
                                else format_vnd(item["candidate"])
                            )
                            if item["candidate"] is not None
                            else "—"
                        )
                elif kind == "state":
                    if item["state"] == "STOPPED":
                        state.set("LỖI — PIPELINE ĐÃ DỪNG")
                    elif youtube_test:
                        state.set("NHẬN DIỆN SỐ — KHÔNG GỬI")
                    elif item["state"] == "ARMED":
                        state.set(
                            "CHẠY THỬ — KHÔNG GỬI COMMENT"
                            if config.run.dry_run and tiktok_web
                            else "CHẠY THỬ — KHÔNG GỬI THẬT"
                            if config.run.dry_run
                            else "ĐANG BẬT GỬI COMMENT"
                            if tiktok_web and submit_live.get()
                            else "ĐANG BẬT ĐIỀN SỐ"
                            if tiktok_web
                            else "ĐANG BẬT GỬI"
                        )
                    else:
                        state.set(
                            (
                                "TAB SẴN SÀNG — NHẤN F8 ĐỂ GỬI COMMENT"
                                if submit_live.get()
                                else "TAB SẴN SÀNG — NHẤN F8 ĐỂ ĐIỀN SỐ"
                            )
                            if tiktok_web
                            and sender_ready.is_set()
                            and not config.run.dry_run
                            else "NUMBERTYPER — CHẠY THỬ · GỬI ĐÃ KHÓA"
                            if tiktok_web
                            else "ĐANG NGHE — KHÔNG GỬI"
                        )
                    add_log("Trạng thái: " + item["state"])
                elif kind == "decision":
                    if item["action"] == "skip":
                        reason = item["reason"]
                        totals["skipped"][reason] = totals["skipped"].get(reason, 0) + 1
                        add_log(f"Bỏ qua {item['value']}: {reason}")
                elif kind in {"send", "draft", "preview"}:
                    if item["ok"]:
                        totals["sent"] += 1
                        unverified = _is_unverified_send_error(item.get("error"))
                        action = (
                            "điền"
                            if kind == "draft"
                            else "xem trước"
                            if kind == "preview"
                            else "Enter đã phát; chưa xác minh comment"
                            if unverified
                            else "gửi"
                        )
                        latest_sent.set(
                            f"{item['value']} · {action} · "
                            f"{datetime.now().strftime('%H:%M:%S')}"
                        )
                        audio_latency = item["lat_audio_to_end_ms"]
                        send_latency = item["lat_send_ms"]
                        latency.set(
                            f"{audio_latency:.1f} ms sau chunk VAD · "
                            f"{action} {send_latency:.1f} ms"
                            if tiktok_web
                            else f"{audio_latency:.1f} ms tổng · {action} {send_latency:.1f} ms"
                        )
                        if unverified:
                            add_log(
                                f"Đã phát Enter cho số {item['value']}; "
                                "chưa xác minh comment xuất hiện."
                            )
                    else:
                        add_log(
                            f"{'Điền' if kind == 'draft' else 'Xem trước' if kind == 'preview' else 'Gửi'} "
                            f"lỗi {item['value']}: {item.get('error') or 'không có chi tiết'}"
                        )
                elif kind == "error":
                    add_log("Lỗi pipeline: " + item["message"])
                    show_health_warning(
                        "worker_error",
                        "Có lỗi khi xử lý/gửi: "
                        + item["message"]
                        + " Kiểm tra app trước khi bật lại.",
                        level="error",
                    )
                elif kind == "cancelled":
                    add_log(
                        f"{'Hủy điền' if tiktok_web else 'Hủy gửi'} "
                        f"{item['value']}: {item['reason']}"
                    )
                if youtube_test:
                    count_label.set("Gửi tin nhắn: đã khóa")
                else:
                    skipped_total = sum(totals["skipped"].values())
                    details = ", ".join(
                        f"{reason}: {count}"
                        for reason, count in totals["skipped"].items()
                    )
                    count_label.set(
                        f"{('Lệnh gửi Enter' if submit_live.get() else 'Lượt điền') if tiktok_web else 'Đã gửi'}: {totals['sent']} | Bỏ qua: {skipped_total}"
                        + (f" ({details})" if details else "")
                    )
        except queue.Empty:
            pass
        if tiktok_web and asr_status_state["speech_active"]:
            now_ns = time.monotonic_ns()
            last_progress_ns = max(
                asr_status_state["speech_started_ns"] or 0,
                asr_status_state["last_event_ns"],
            )
            if (
                not asr_status_state["stall_warning"]
                and last_progress_ns
                and now_ns - last_progress_ns >= 15_000_000_000
            ):
                asr_status_state["stall_warning"] = True
                controller.disarm()
                message = (
                    "VAD vẫn nhận lời nói nhưng ASR chưa cập nhật trong 15 giây. "
                    "Thao tác đã tắt; kiểm tra audio/tab và khởi động lại nếu cần."
                )
                logger.log("asr_stalled", seconds=15, disarmed=True)
                add_log(message)
                asr_status.set("ASR chậm/không phản hồi · đã tắt thao tác")
                show_health_warning("asr_stalled", message, level="error")

    def poll_safely():
        try:
            poll()
        except Exception as exc:  # noqa: BLE001 - keep GUI refresh alive on bad UI events
            controller.disarm()
            logger.log(
                "ui_poll_error",
                error_type=type(exc).__name__,
                message=str(exc),
            )
            try:
                add_log(f"Lỗi cập nhật giao diện: {type(exc).__name__}: {exc}")
                show_health_warning(
                    "ui_poll_error",
                    "Giao diện gặp lỗi khi cập nhật trạng thái. NumberTyper đã tự "
                    "tắt điền/gửi; hãy kiểm tra trước khi bật lại.",
                    level="error",
                )
            except tk.TclError:
                pass
        try:
            if root.winfo_exists():
                root.after(poll_interval_ms, poll_safely)
        except tk.TclError:
            pass

    thread = threading.Thread(target=pipeline.run, name="pipeline", daemon=True)
    thread.start()

    def close_window():
        controller.disarm()
        controller.stop_event.set()
        try:
            source.stop()
        except Exception:
            pass
        if comparison_session is not None:
            comparison_session.close()
        if keyboard_module is not None:
            keyboard_module.unhook_all_hotkeys()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close_window)
    root.after(poll_interval_ms, poll_safely)
    if config.run.start_armed:
        root.after(0, lambda: threading.Thread(target=toggle, daemon=True).start())
    root.mainloop()
    thread.join(timeout=3)
    try:
        controller.sender.close()
    except Exception:
        pass
    if tiktok_sender is not None and tiktok_sender is not controller.sender:
        try:
            tiktok_sender.close()
        except Exception:
            pass
    return 0
