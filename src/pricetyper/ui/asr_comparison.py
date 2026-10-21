from __future__ import annotations

import queue
import tkinter as tk
from tkinter import messagebox, ttk

from pricetyper.asr.comparison import parse_reference_prices
from pricetyper.ui.formatting import format_vnd

CONDITIONS = {
    "Nói sạch, một giọng": "clean",
    "Có nhạc hoặc tiếng ồn": "music_noise",
    "Chồng lấp giọng — luôn abstain": "overlap",
    "Chưa phân loại": "unknown",
}
ACCENTS = {
    "Chưa rõ": "unknown",
    "Miền Bắc": "north",
    "Miền Trung": "central",
    "Miền Nam": "south",
}
SCORING_SCOPES = {
    "Số được nói (bỏ qua bộ lọc giá)": "number",
    "Giá qua bộ lọc cấu hình": "price",
}
ENGINES = ("vosk", "vosk_number", "whisper", "zipformer")


class ASRComparisonWindow:
    def __init__(self, parent, session, whisper_model_name="small"):
        self.session = session
        self.whisper_model_name = whisper_model_name
        self.window = tk.Toplevel(parent)
        self.window.title("PriceTyper — Benchmark ASR tiếng Việt local")
        self.window.geometry("1400x900")
        self.window.minsize(1050, 720)
        self.status = tk.StringVar(
            value="Mở video, bắt đầu capture tab, rồi chọn đoạn cần so sánh."
        )
        self.reference = tk.StringVar()
        self.expected_prices = tk.StringVar()
        self.scoring_scope = tk.StringVar(value=next(iter(SCORING_SCOPES)))
        self.condition = tk.StringVar(value=next(iter(CONDITIONS)))
        self.accent = tk.StringVar(value=next(iter(ACCENTS)))
        self.consensus = tk.StringVar(value="Chưa có kết quả so sánh.")
        self.summary = tk.StringVar(value="Benchmark phiên hiện tại chưa có mẫu.")
        self.start_button = None
        self.compare_button = None
        self.discard_button = None
        self.engine_values: dict[str, dict[str, dict[str, tk.StringVar]]] = {}

        ttk.Label(
            self.window,
            text=(
                "So sánh cùng một đoạn audio tab: audio gốc và DPDFNet đã khử nhiễu, "
                "mỗi nhánh chạy Vosk, Vosk số thử nghiệm, Whisper và Zipformer-VI."
            ),
            font=("Segoe UI", 11, "bold"),
            wraplength=1050,
        ).pack(anchor="w", padx=14, pady=(12, 3))
        ttk.Label(
            self.window,
            text=(
                "Tối đa 20 giây audio được giữ trong RAM rồi xóa sau so sánh. "
                "ASR/khử nhiễu chạy local; model tải về một lần. DPDFNet giảm nhiễu, "
                "không tách nhạc hay tách người nói. Đây là benchmark theo đoạn, "
                "chưa phải pipeline gửi realtime. Overlap hiện do người dùng gắn nhãn; "
                "nhánh Vosk số chỉ giới hạn cụm phổ biến 1–20 và cách nói nghìn, "
                "nên có thể bỏ sót lời ngoài ngữ pháp. Nhánh này không tham gia preview "
                "đồng thuận. Preview nghiêm ngặt cần 6 kết quả của 3 model gốc × 2 nhánh; "
                "đây không phải confidence đã hiệu chuẩn."
            ),
            wraplength=1050,
        ).pack(anchor="w", padx=14, pady=(0, 8))

        controls = ttk.LabelFrame(self.window, text="Đoạn có nhãn chuẩn")
        controls.pack(fill="x", padx=12, pady=4)
        ttk.Label(controls, text="Transcript chuẩn (mọi lời nghe được):").grid(
            row=0, column=0, sticky="w", padx=8, pady=5
        )
        ttk.Entry(controls, textvariable=self.reference).grid(
            row=0, column=1, columnspan=3, sticky="ew", padx=8, pady=5
        )
        ttk.Label(controls, text="Nhãn chuẩn (số nguyên):").grid(
            row=1, column=0, sticky="w", padx=8, pady=5
        )
        ttk.Entry(controls, textvariable=self.expected_prices).grid(
            row=1, column=1, columnspan=3, sticky="ew", padx=8, pady=5
        )
        ttk.Label(
            controls,
            text=(
                'Nhiều nhãn ngăn bằng ; (ví dụ 140; 110). Không có số: nhập '
                '"không có". Chế độ số bỏ qua bộ lọc giá; chế độ giá áp dụng bộ lọc.'
            ),
        ).grid(row=2, column=1, columnspan=3, sticky="w", padx=8, pady=(0, 4))
        ttk.Label(controls, text="Điều kiện âm thanh:").grid(
            row=3, column=0, sticky="w", padx=8, pady=5
        )
        self.condition_box = ttk.Combobox(
            controls,
            textvariable=self.condition,
            values=tuple(CONDITIONS),
            state="readonly",
            width=32,
        )
        self.condition_box.grid(row=3, column=1, sticky="w", padx=8, pady=5)
        ttk.Label(controls, text="Giọng vùng:").grid(
            row=3, column=2, sticky="w", padx=8, pady=5
        )
        self.accent_box = ttk.Combobox(
            controls,
            textvariable=self.accent,
            values=tuple(ACCENTS),
            state="readonly",
            width=18,
        )
        self.accent_box.grid(row=3, column=3, sticky="w", padx=8, pady=5)
        ttk.Label(controls, text="Phạm vi chấm:").grid(
            row=4, column=0, sticky="w", padx=8, pady=5
        )
        self.scoring_scope_box = ttk.Combobox(
            controls,
            textvariable=self.scoring_scope,
            values=tuple(SCORING_SCOPES),
            state="readonly",
            width=32,
        )
        self.scoring_scope_box.grid(
            row=4, column=1, columnspan=3, sticky="ew", padx=8, pady=5
        )
        self.start_button = ttk.Button(
            controls, text="Bắt đầu đoạn", command=self._start
        )
        self.start_button.grid(row=5, column=1, sticky="ew", padx=8, pady=5)
        self.compare_button = ttk.Button(
            controls, text="Dừng & so sánh", command=self._compare, state="disabled"
        )
        self.compare_button.grid(row=5, column=2, sticky="ew", padx=8, pady=5)
        self.discard_button = ttk.Button(
            controls, text="Bỏ đoạn", command=self._discard, state="disabled"
        )
        self.discard_button.grid(row=5, column=3, sticky="ew", padx=8, pady=5)
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(2, weight=1)
        controls.columnconfigure(3, weight=1)

        ttk.Label(self.window, textvariable=self.status, wraplength=1050).pack(
            anchor="w", padx=14, pady=5
        )
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=12, pady=4)
        self._add_branch_tab(notebook, "raw", "Audio gốc")
        self._add_branch_tab(notebook, "denoised", "DPDFNet · đã khử nhiễu")

        ttk.Label(
            self.window,
            textvariable=self.consensus,
            wraplength=1050,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=14, pady=(4, 2))
        ttk.Label(
            self.window,
            textvariable=self.summary,
            wraplength=1050,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(2, 8))

        self.window.protocol("WM_DELETE_WINDOW", self.window.withdraw)
        self.window.after(100, self._poll)
        self.window.withdraw()

    def _add_branch_tab(self, notebook, branch: str, title: str) -> None:
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=title)
        branch_values = {}
        for column, engine in enumerate(ENGINES):
            title_text = {
                "vosk": "Vosk · baseline",
                "vosk_number": "Vosk số · ngữ pháp thử 1–20/nghìn",
                "whisper": f"Whisper · {self.whisper_model_name} / CPU int8",
                "zipformer": "Zipformer-VI · INT8 CPU",
            }[engine]
            frame = ttk.LabelFrame(tab, text=title_text)
            frame.grid(row=0, column=column, sticky="nsew", padx=4, pady=6)
            fields = (
                ("Transcript", "text"),
                ("Số/giá trích được", "prices"),
                ("Khớp nhãn", "exact"),
                ("Bỏ sót", "missed"),
                ("Số/giá thừa hoặc nhầm", "false"),
                ("ASR + tăng cường", "latency"),
                ("WER / CER", "error_rates"),
            )
            values = {}
            for row, (label, field) in enumerate(fields):
                value = tk.StringVar(value="—")
                values[field] = value
                ttk.Label(frame, text=label + ":").grid(
                    row=row, column=0, sticky="nw", padx=6, pady=4
                )
                ttk.Label(
                    frame,
                    textvariable=value,
                    wraplength=290,
                    justify="left",
                ).grid(row=row, column=1, sticky="nw", padx=6, pady=4)
            frame.columnconfigure(1, weight=1)
            tab.columnconfigure(column, weight=1, uniform="engine")
            branch_values[engine] = values
        tab.rowconfigure(0, weight=1)
        self.engine_values[branch] = branch_values

    def show(self) -> None:
        self.window.deiconify()
        self.window.lift()

    def _start(self) -> None:
        try:
            self.session.start_segment()
        except RuntimeError as exc:
            messagebox.showerror("Không thể bắt đầu đoạn", str(exc), parent=self.window)

    def _compare(self) -> None:
        try:
            condition = CONDITIONS[self.condition.get()]
            accent = ACCENTS[self.accent.get()]
            expected_prices = parse_reference_prices(self.expected_prices.get())
            seconds = self.session.stop_and_compare(
                self.reference.get(),
                expected_prices,
                condition,
                accent,
                SCORING_SCOPES[self.scoring_scope.get()],
            )
            self.status.set(
                f"Đã chốt {seconds:.2f} giây. Đang nạp/chạy các model local…"
            )
            self._set_controls("working")
        except (RuntimeError, ValueError) as exc:
            messagebox.showerror("Không thể so sánh", str(exc), parent=self.window)

    def _discard(self) -> None:
        self.session.discard_segment()
        self._set_controls("idle")

    def _set_controls(self, state: str) -> None:
        if state == "recording":
            self.start_button.configure(state="disabled")
            self.compare_button.configure(state="normal", text="Dừng & so sánh")
            self.discard_button.configure(state="normal")
        elif state == "ready":
            self.start_button.configure(state="disabled")
            self.compare_button.configure(state="normal", text="So sánh đoạn này")
            self.discard_button.configure(state="normal")
        elif state == "working":
            self.start_button.configure(state="disabled")
            self.compare_button.configure(state="disabled")
            self.discard_button.configure(state="disabled")
        else:
            self.start_button.configure(state="normal")
            self.compare_button.configure(state="disabled", text="Dừng & so sánh")
            self.discard_button.configure(state="disabled")

    @staticmethod
    def _percent(value) -> str:
        return "—" if value is None else f"{value * 100:.1f}%"

    @staticmethod
    def _values(values: list[int], scoring_scope: str) -> str:
        if not values:
            return "—"
        if scoring_scope == "number":
            return ", ".join(f"{value:,}".replace(",", ".") for value in values)
        return ", ".join(format_vnd(value) for value in values)

    def _show_result(self, result: dict) -> None:
        scoring_scope = result["scoring_scope"]
        for branch, engines in result["engines"].items():
            for engine, row in engines.items():
                values = self.engine_values[branch][engine]
                values["text"].set(row["text"] or "—")
                values["prices"].set(self._values(row["prices"], scoring_scope))
                values["exact"].set("Đúng" if row["price_exact"] else "Sai")
                values["missed"].set(str(row["missed_prices"]))
                values["false"].set(str(row["false_candidates"]))
                values["latency"].set(
                    f"{row['processing_ms']:.0f} ms "
                    f"(ASR {row['inference_ms']:.0f} + tăng cường {row['enhancement_ms']:.0f})"
                )
                values["error_rates"].set(
                    f"{self._percent(row['wer'])} / {self._percent(row['cer'])}"
                )

        strict = result["consensus"]["strict"]
        strict_price = self._values(strict["prices"], scoring_scope)
        decisions = [
            f"Preview nghiêm ngặt: {strict_price} — {strict['reason']}"
        ]
        for branch, title in (("raw", "Gốc"), ("denoised", "DPDFNet")):
            decision = result["consensus"][branch]
            prices = self._values(decision["prices"], scoring_scope)
            decisions.append(f"{title}: {prices} — {decision['reason']}")
        self.consensus.set(
            "Đồng thuận (chỉ preview; sender vẫn khóa): " + " | ".join(decisions)
        )

        heading = (
            f"Benchmark nhóm {result['benchmark_group']} · "
            "lũy kế trong phiên (audio không lưu):"
        )
        lines = [heading]
        for key, summary in sorted(result["benchmark_summary"].items()):
            exact_rate = summary["exact"] / summary["segments"]
            exact = (
                f"{summary['exact']}/{summary['segments']} exact "
                f"({exact_rate:.0%})"
            )
            p50 = "—" if summary["p50_ms"] is None else f"{summary['p50_ms']:.0f} ms"
            p95 = "—" if summary["p95_ms"] is None else f"{summary['p95_ms']:.0f} ms"
            lines.append(
                f"{key}: {exact}, bỏ sót {summary['missed']}, số/giá thừa "
                f"{summary['false']}, P50/P95 {p50}/{p95}"
            )
        self.summary.set("\n".join(lines))
        models = result["model_load_ms"]
        reference_prices = self._values(result["reference_prices"], scoring_scope)
        if not result["reference_prices"]:
            reference_prices = (
                "không có số" if scoring_scope == "number" else "không có giá"
            )
        scope_label = "số" if scoring_scope == "number" else "giá"
        self.status.set(
            f"Đoạn {result['duration_s']:.2f}s · nạp/khởi tạo (ms): "
            f"Whisper {models['whisper']:.0f}, Zipformer {models['zipformer']:.0f}, "
            f"DPDFNet {models['denoiser']:.0f}, Vosk dùng chung {models['vosk']:.0f}, "
            f"tạo ngữ pháp {models['vosk_number']:.0f} · "
            f"{scope_label} chuẩn: {reference_prices} · "
            "audio đã xóa khỏi RAM."
        )
        self._set_controls("idle")

    def _poll(self) -> None:
        while True:
            try:
                item = self.session.events.get_nowait()
            except queue.Empty:
                break
            if item["kind"] == "comparison_status":
                self.status.set(item["message"])
                self._set_controls(item["state"])
            elif item["kind"] == "comparison_result":
                self._show_result(item["result"])
            elif item["kind"] == "comparison_error":
                self.status.set(item["message"])
                self._set_controls("idle")
        if self.window.winfo_exists():
            self.window.after(100, self._poll)
