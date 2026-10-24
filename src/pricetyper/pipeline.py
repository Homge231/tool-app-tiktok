from __future__ import annotations

import queue
import threading
import time
import traceback

from pricetyper.controller import State
from pricetyper.decision.decider import Decider, DeciderCfg
from pricetyper.parsing.gate import GateCfg, gate
from pricetyper.parsing.vi_number import parse_all
from pricetyper.types import AsrEvent


class PipelineError(RuntimeError):
    pass


class Pipeline:
    def __init__(
        self,
        source,
        asr,
        sender,
        config,
        controller,
        logger,
        audio_observer=None,
        log_transcript_text=True,
        candidate_scope="price",
        send_final_only=False,
        draft_only=False,
        candidate_range=None,
    ):
        if candidate_scope not in {"number", "price"}:
            raise ValueError("candidate_scope must be 'number' or 'price'")
        self.source, self.asr, self.sender = source, asr, sender
        self.config, self.controller, self.logger = config, controller, logger
        self.audio_observer = audio_observer
        self.log_transcript_text = log_transcript_text
        self.candidate_scope = candidate_scope
        self.candidate_range = candidate_range
        self.send_final_only = send_final_only
        self.draft_only = draft_only
        self.audio_q = queue.Queue(maxsize=config.audio.queue_max_chunks)
        self.event_q = queue.Queue()
        self.send_q = queue.Queue()
        self.ui_q = queue.Queue()
        self.update_q = queue.Queue()
        self._event_stop = object()
        d, p = config.decision, config.parser
        gate_cfg = GateCfg(
            d.min_value,
            d.max_value,
            tuple(d.exclude_prev),
            tuple(d.exclude_next),
            d.countdown_filter,
            d.gate_mode,
            tuple(d.anchor_before),
            tuple(d.anchor_after),
        )
        decider_cfg = DeciderCfg(
            d.hold_complete_ms,
            d.hold_open_ms,
            d.cooldown_same_s,
            d.cooldown_any_s,
            d.max_sends_per_min,
            p.shorthand,
            tuple(p.k_tokens),
        )
        self.decider = Decider(
            gate_cfg,
            decider_cfg,
            armed=controller.armed.is_set(),
            candidate_scope=candidate_scope,
            draft_only=draft_only,
            candidate_range=candidate_range,
        )
        self._threads = []
        self._audio_origin = None
        self._last_audio_meter_ns = 0
        self._failures = []
        self._silent_since_ns = None
        self._silence_reported = False
        self._audio_generation = 0
        self._audio_generation_lock = threading.Lock()
        self._last_gap_warning_ns: dict[str, int] = {}

    def set_draft_only(self, draft_only: bool) -> None:
        self.draft_only = draft_only
        self.decider.draft_only = draft_only

    def _enqueue_audio(self, item):
        with self._audio_generation_lock:
            self.audio_q.put_nowait((*item, self._audio_generation))

    def report_audio_gap(
        self,
        *,
        reason: str,
        message: str,
        dropped_chunks: int = 0,
        event: str = "audio_overflow",
    ):
        queued_chunks = 0
        with self._audio_generation_lock:
            while True:
                try:
                    self.audio_q.get_nowait()
                    queued_chunks += 1
                except queue.Empty:
                    break
            self._audio_generation += 1
            now_ns = time.monotonic_ns()
            last_warning_ns = self._last_gap_warning_ns.get(reason, 0)
            emit_warning = last_warning_ns == 0 or (
                now_ns - last_warning_ns >= 5_000_000_000
            )
            if emit_warning:
                self._last_gap_warning_ns[reason] = now_ns
        self.logger.log(
            event,
            reason=reason,
            policy="clear_stale_reset_asr_disarm",
            dropped_chunks=dropped_chunks,
            cleared_pipeline_chunks=queued_chunks,
        )
        self.controller.disarm()
        if emit_warning:
            self.ui_q.put(
                {
                    "kind": "health_warning",
                    "code": "audio_gap",
                    "level": "warning",
                    "message": message,
                }
            )

    def _put_audio(self, item):
        try:
            self._enqueue_audio(item)
        except queue.Full:
            self.report_audio_gap(
                reason="asr_queue_full",
                message=(
                    "Audio bị mất do ASR xử lý chậm. App đã xóa dữ liệu cũ, reset nhận dạng "
                    "và tắt thao tác. Kiểm tra trạng thái trước khi bật lại."
                ),
            )
            self._enqueue_audio(item)

    def _audio_loop(self):
        started = False
        try:
            self.source.start()
            started = True
            while not self.controller.stop_event.is_set():
                item = self.source.read()
                if item is None:
                    break
                if self._audio_origin is None:
                    self._audio_origin = item[1]
                    self.logger.log("audio_start", t_audio_ns=self._audio_origin)
                import numpy as np

                samples = np.frombuffer(item[0], dtype=np.int16)
                rms = (
                    float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
                    if samples.size
                    else 0.0
                )
                if (
                    self.config.audio.source == "browser_tab"
                    and item[1] - self._last_audio_meter_ns >= 200_000_000
                ):
                    self.ui_q.put({"kind": "audio_level", "rms": rms})
                    self._last_audio_meter_ns = item[1]
                if rms < 10:
                    self._silent_since_ns = self._silent_since_ns or item[1]
                    if (
                        not self._silence_reported
                        and item[1] - self._silent_since_ns >= 30_000_000_000
                    ):
                        self.logger.log("audio_silent", duration_s=30)
                        self._silence_reported = True
                        self.ui_q.put(
                            {
                                "kind": "health_warning",
                                "code": "silent_audio",
                                "level": "warning",
                                "message": (
                                    "Không có tín hiệu audio trong 30 giây. Kiểm tra video, "
                                    "tab đang thu và trạng thái extension."
                                ),
                            }
                        )
                else:
                    if self._silence_reported:
                        self.ui_q.put(
                            {
                                "kind": "health_recovered",
                                "code": "silent_audio",
                                "message": "Đã nhận lại tín hiệu audio.",
                            }
                        )
                    self._silent_since_ns = None
                    self._silence_reported = False
                if self.audio_observer is not None:
                    self.audio_observer.feed_audio(item[0], item[1])
                self._put_audio(item)
        finally:
            try:
                if started:
                    self.source.stop()
            finally:
                try:
                    self.audio_q.put_nowait(None)
                except queue.Full:
                    try:
                        self.audio_q.get_nowait()
                    except queue.Empty:
                        pass
                    self.audio_q.put_nowait(None)

    def _asr_loop(self):
        last_audio_ns = 0
        audio_generation = 0
        suppress_next_final = False
        last_speech_active = None
        while not self.controller.stop_event.is_set():
            try:
                item = self.audio_q.get(timeout=0.1)
            except queue.Empty:
                continue
            if item is None:
                if getattr(self.asr, "finish_on_stop", False):
                    for final in self.asr.finish(last_audio_ns):
                        if not final.text:
                            continue
                        if suppress_next_final:
                            final = AsrEvent(
                                "partial", final.text, final.t_ns, final.t_audio_ns
                            )
                            suppress_next_final = False
                        self.event_q.put(final)
                        fields = (
                            {"text": final.text} if self.log_transcript_text else {}
                        )
                        self.logger.log("asr_" + final.kind, **fields)
                        self.ui_q.put(
                            {
                                "kind": "asr",
                                "text": final.text,
                                "event_kind": final.kind,
                            }
                        )
                self.event_q.put(self._event_stop)
                return
            if len(item) == 3:
                pcm, audio_ns, generation = item
            else:
                pcm, audio_ns = item
                generation = audio_generation
            if generation != audio_generation:
                self.asr.reset()
                audio_generation = generation
                suppress_next_final = True
            last_audio_ns = audio_ns
            events = self.asr.feed(pcm, audio_ns)
            speech_active = getattr(self.asr, "speech_active", None)
            if speech_active is not None and speech_active != last_speech_active:
                self.ui_q.put(
                    {"kind": "asr_activity", "active": bool(speech_active)}
                )
                last_speech_active = speech_active
            for event in events:
                if suppress_next_final and event.kind == "final":
                    event = AsrEvent(
                        "partial", event.text, event.t_ns, event.t_audio_ns
                    )
                    suppress_next_final = False
                self.event_q.put(event)
                fields = {"text": event.text} if self.log_transcript_text else {}
                self.logger.log("asr_" + event.kind, **fields)
                self.ui_q.put(
                    {"kind": "asr", "text": event.text, "event_kind": event.kind}
                )

    def _decide_loop(self):
        origin = time.perf_counter_ns()
        while not self.controller.stop_event.is_set():
            while True:
                try:
                    changes = self.update_q.get_nowait()
                except queue.Empty:
                    break
                for key, value in changes.items():
                    if key in {"min_value", "max_value", "countdown_filter"}:
                        setattr(self.decider.gate_cfg, key, value)
                        setattr(self.config.decision, key, value)
                    elif key in {"cooldown_same_s", "cooldown_any_s", "max_per_min"}:
                        setattr(self.decider.cfg, key, value)
                        config_key = (
                            "max_sends_per_min" if key == "max_per_min" else key
                        )
                        setattr(self.config.decision, config_key, value)
            self.decider.armed = self.controller.armed.is_set()
            try:
                event = self.event_q.get(timeout=0.01)
            except queue.Empty:
                event = False
            now_ns = time.perf_counter_ns()
            t_ms = (now_ns - origin) // 1_000_000
            results = []
            if event is not False and event is not self._event_stop:
                if not self.send_final_only or event.kind == "final":
                    spans = self.decider.on_event(
                        event.kind, event.text, t_ms, event.t_audio_ns
                    )
                    results.extend(spans)
                parsed = parse_all(
                    event.text,
                    self.config.parser.shorthand,
                    self.config.parser.k_tokens,
                )
                passed = gate(event.text, parsed, self.decider.gate_cfg)
                displayed = (
                    parse_all(
                        event.text,
                        self.config.parser.shorthand,
                        self.config.parser.k_tokens,
                        split_count_sequence=True,
                    )
                    if self.candidate_scope == "number"
                    else passed
                )
                candidate_span = displayed[-1] if displayed else None
                if candidate_span and self.candidate_range is not None:
                    minimum, maximum = self.candidate_range
                    if not minimum <= candidate_span.value <= maximum:
                        candidate_span = None
                parse_fields = {
                    "spans": [
                        {
                            "value": s.value,
                            "kind": s.kind,
                            "unit": s.unit,
                            "closed": s.closed,
                            "extendable": s.extendable,
                        }
                        for s in parsed
                    ],
                    "passed": [s.value for s in passed],
                    "candidate_scope": self.candidate_scope,
                    "displayed": [s.value for s in displayed],
                }
                if self.log_transcript_text:
                    parse_fields["text"] = event.text
                self.logger.log("parse", **parse_fields)
                self.ui_q.put(
                    {
                        "kind": "parse",
                        "event_kind": event.kind,
                        "candidate": candidate_span.value if candidate_span else None,
                        "asr_chunk_delay_ms": max(
                            0.0, (event.t_ns - event.t_audio_ns) / 1e6
                        ),
                    }
                )
            results.extend(self.decider.tick(t_ms))
            for decision in results:
                self.logger.log(
                    "decision",
                    value=decision.value,
                    action=decision.action,
                    reason=decision.reason,
                    t_audio_ns=decision.t_audio,
                )
                self.ui_q.put(
                    {
                        "kind": "decision",
                        "value": decision.value,
                        "action": decision.action,
                        "reason": decision.reason,
                    }
                )
                if decision.action == "send":
                    text = self.config.output.template.format(value=decision.value)
                    self.send_q.put((decision.value, text, decision.t_audio))
            if event is self._event_stop:
                self.send_q.put(None)
                return

    def _send_loop(self):
        failures = 0
        while True:
            command = self.send_q.get()
            if command is None:
                return
            value, text, audio_ns = command
            if not self.controller.armed.is_set():
                self.logger.log(
                    "send_cancelled",
                    value=value,
                    reason="disarmed_at_send",
                    t_audio_ns=audio_ns,
                )
                self.ui_q.put(
                    {"kind": "cancelled", "value": value, "reason": "disarmed_at_send"}
                )
                continue
            try:
                if self.config.run.dry_run:
                    from pricetyper.senders.null_sender import NullSender

                    result = NullSender().send(text)
                else:
                    result = self.sender.send(text)
                if result.ok:
                    failures = 0
                else:
                    failures += 1
                action_kind = (
                    "preview"
                    if self.draft_only and self.config.run.dry_run
                    else "draft"
                    if self.draft_only
                    else "send"
                )
                if result.error and result.error.startswith("send_unverified:"):
                    self.logger.log(
                        "send_unverified", value=value, message=result.error
                    )
                self.logger.log(
                    action_kind,
                    value=value,
                    text=text,
                    ok=result.ok,
                    lat_audio_to_end_ms=(result.t_end_ns - audio_ns) / 1e6,
                    lat_send_ms=(result.t_end_ns - result.t_start_ns) / 1e6,
                    error=result.error,
                )
                self.ui_q.put(
                    {
                        "kind": action_kind,
                        "value": value,
                        "ok": result.ok,
                        "lat_audio_to_end_ms": (result.t_end_ns - audio_ns) / 1e6,
                        "lat_send_ms": (result.t_end_ns - result.t_start_ns) / 1e6,
                        "error": result.error,
                    }
                )
            except Exception as exc:
                failures += 1
                from pricetyper.senders.desktop_sender import SenderFailSafeError

                if isinstance(exc, SenderFailSafeError):
                    self.logger.log("failsafe", message=str(exc))
                    self.controller.disarm()
                    failures = 0
                    continue
                failure_kind = "draft_failed" if self.draft_only else "send_failed"
                self.logger.log(failure_kind, code=failure_kind, message=str(exc))
                self.ui_q.put(
                    {
                        "kind": "error",
                        "message": (
                            f"Điền số thất bại: {exc}"
                            if self.draft_only
                            else f"Gửi thất bại: {exc}"
                        ),
                    }
                )
            if failures >= 3:
                self.controller.disarm()
                failures = 0

    def run(self):
        def guarded(name, target):
            try:
                target()
            except BaseException as exc:
                details = traceback.format_exc()
                self._failures.append((name, exc))
                self.logger.log(
                    "error",
                    code="exception",
                    message=f"{name}: {exc}",
                    traceback=details,
                )
                self.ui_q.put(
                    {
                        "kind": "health_warning",
                        "code": "pipeline_error",
                        "level": "error",
                        "message": (
                            f"Pipeline {name} đã dừng do lỗi: {exc}. "
                            "NumberTyper không còn xử lý audio đáng tin cậy; hãy dừng và khởi động lại app."
                        ),
                    }
                )
                self.controller._set_state(State.STOPPED, f"exception:{name}")
                self.controller.stop_event.set()
                self.ui_q.put({"kind": "error", "message": f"{name}: {exc}"})

        self._threads = [
            threading.Thread(
                target=guarded,
                args=("audio", self._audio_loop),
                name="audio",
                daemon=True,
            ),
            threading.Thread(
                target=guarded, args=("asr", self._asr_loop), name="asr", daemon=True
            ),
            threading.Thread(
                target=guarded,
                args=("decide", self._decide_loop),
                name="decide",
                daemon=True,
            ),
            threading.Thread(
                target=guarded,
                args=("sender", self._send_loop),
                name="sender",
                daemon=True,
            ),
        ]
        for thread in self._threads:
            thread.start()
        try:
            self._threads[0].join()
            self._threads[1].join()
            self._threads[2].join()
        except KeyboardInterrupt:
            self.controller.disarm()
            self.controller.stop_event.set()
            for thread in self._threads[:3]:
                thread.join(timeout=2)
            self.send_q.put(None)
            self._threads[3].join(timeout=2)
            self.sender.close()
            raise
        self.send_q.put(None)
        self._threads[3].join()
        self.sender.close()
        if self._failures:
            name, error = self._failures[0]
            raise PipelineError(f"{name} thread failed: {error}") from error
