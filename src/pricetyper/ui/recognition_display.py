from dataclasses import dataclass


@dataclass
class RecognitionDisplay:
    """Keep unstable partial ASR output separate from finalized text and values."""

    final_text: str = "—"
    partial_text: str = "—"
    provisional_candidate: str = "—"
    candidate: str = "—"

    def on_asr(self, kind: str, text: str) -> None:
        display_text = text[:80] or "—"
        if kind == "partial":
            self.partial_text = display_text
        elif kind == "final":
            self.final_text = display_text
            self.partial_text = "—"
        else:
            raise ValueError(f"Unknown ASR event kind: {kind}")

    def on_candidate(self, kind: str, candidate: int | None) -> None:
        if kind == "partial":
            self.provisional_candidate = (
                str(candidate) if candidate is not None else "—"
            )
        elif kind == "final":
            self.candidate = str(candidate) if candidate is not None else "—"
            self.provisional_candidate = "—"
        else:
            raise ValueError(f"Unknown ASR event kind: {kind}")
