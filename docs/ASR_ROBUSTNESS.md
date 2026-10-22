# PriceTyper ASR robustness plan

## User requirement

The listening path must recognize spoken Vietnamese numbers amid music and background noise, across regional accents and several voices during a chaotic livestream. The current priority is **number extraction**, not deciding whether each number is a sale price. If the video itself plays a translated or dubbed audio track, the app transcribes the audio it receives.

The YouTube prototype uses Zipformer-VI as its primary local recognizer, with Silero VAD to segment speech; it periodically re-decodes an active segment for provisional partial text and finalizes it after a pause. TikTok disables periodic partial re-decodes to reduce ASR load and preserve live audio processing. If an active segment never closes, the engine flushes and resets VAD at 12 seconds; that forced piece is preview-only and never eligible for sending. Vosk remains a benchmark baseline. The number-first GUI shows the latest raw parser value without the price gate, separates provisional values from finalized values, and reports ASR processing after the triggering audio chunk; that number excludes endpointing and is not end-of-speech-to-visible-result latency. Earlier user testing identified [YouTube video IYH-W2ZK6kk](https://www.youtube.com/watch?v=IYH-W2ZK6kk) and showed a qualitative failure in the Vosk path, including `một` being recognized as `mộ` or `mã`. This evidence motivated a Zipformer trial; it does not prove Zipformer has higher number accuracy. There is still no timestamped ground-truth corpus sufficient to calculate WER or exact-number accuracy, and no robustness requirement is yet met.

## Same-segment local benchmark prototype

An optional YouTube-only comparison window compares two copies of the same selected-tab PCM segment: raw and DPDFNet-enhanced. Each copy is processed by the three core lanes (Vosk, faster-whisper, and Vietnamese Zipformer-VI 30M INT8) plus an experimental Vosk finite-phrase grammar lane. The user marks a segment of up to 20 seconds and enters the exact reference phrase, acoustic-condition label, and accent region. Audio is retained in memory only and cleared after comparison or discard. Benchmark counts and latency samples remain in RAM for the current app session; they are not persisted. The mode forces `NullSender` and does not inspect the YouTube page.

Whisper configuration: faster-whisper 1.2.1; multilingual `small` model by default; CPU/int8; `language="vi"`; `task="transcribe"`; beam size 5; VAD enabled to suppress silence-only output. Zipformer is the offline 30M INT8 Vietnamese model distributed by sherpa-onnx. Its default runtime path uses Silero VAD and re-decodes the current segment for interim output; endpoint latency depends on the silence threshold. DPDFNet baseline is the 16 kHz speech-enhancement model from sherpa-onnx. faster-whisper remains optional and is installed with `.[robust-asr]`; `sherpa-onnx` is a regular dependency because Zipformer is now primary. `scripts/download_robust_asr_models.py` retrieves model weights into ignored local `models/`. Whisper weights use the local Hugging Face cache. Captured audio remains local and is never uploaded.

For every model and audio branch, the UI reports transcript, extracted values, WER/CER, exact match, expected labels missed, extra false candidates, and processing latency. Number-only scoring is the default and includes all supported parsed numbers without the price gate; price scoring is a secondary scope that applies the configured VND gate. The session summary reports exact-number count, misses, false candidates, and nearest-rank P50/P95 latency per condition, pipeline, and scoring scope. Load times are separate. A P50/P95 estimate from one segment is not meaningful; collect multiple labeled segments. These are segment-processing benchmarks after capture is stopped, not live end-to-end latency or send latency. Consensus latency measures only the three core ASR outputs plus enhancement where used; the experimental number grammar does not participate in consensus.

The strict agreement preview is still price-specific: it only exposes candidate prices when all six results (three engines across two audio branches) produce the same ordered price list. It abstains on disagreement and on segments manually tagged as overlapping. Agreement is only a conservative prototype heuristic and is not calibrated confidence; overlap labeling is manual because an automatic overlap detector has not been implemented. No sender is enabled.

Implementation smoke check in this workspace: sherpa-onnx 1.13.8 installed under Python 3.14.5, and the official Zipformer-VI INT8 and DPDFNet baseline weights are in the ignored `models/` directory. The full comparison session processed one second of synthetic silence. First-use model loads took Whisper 3,554 ms, Zipformer 2,444 ms, DPDFNet 125 ms, and Vosk 764 ms. With models loaded, the six sequential branch/engine processing times were raw Vosk 559 ms, raw Whisper 327 ms, raw Zipformer 41 ms, enhanced Vosk 146 ms, enhanced Whisper 107 ms, and enhanced Zipformer 133 ms. Zipformer emitted `ĐÚNG`; no price-gate candidate was produced and the strict price preview had no candidate. Its one-sample strict processing time was 1,105 ms; P50/P95 from a single silence sample are not meaningful and do not establish the <1 s target. This verifies local integration only, not Vietnamese number accuracy, music/noise robustness, or livestream latency. Synthetic tests cover branch behavior, number miss/false counts, session P50/P95 accumulation, and disagreement/overlap abstention. Manual labeled YouTube comparison is still required.

## Key distinctions

1. **Audio level and speech activity:** RMS and VAD distinguish silence from probable speech. VAD does not remove music or separate speakers.
2. **Speech enhancement:** noise suppression can reduce some background noise. It can also damage syllables or tones; compare it against raw PCM on the same labeled clips.
3. **Speech/music and speaker separation:** source-separation models attempt to produce separate signals from a mixture. This is different from noise suppression, can add latency/artifacts, and must be tested on Vietnamese livestream audio before selection.
4. **ASR:** an offline multilingual model may transcribe different accents/noise better than the current baseline, but a published benchmark is not a guarantee for this use case.
5. **Diarization and overlap:** diarization estimates which speaker spoke when; overlap detection marks simultaneous speech. Neither alone reconstructs clean speech for each person. Try source separation only for detected overlap; if the amount remains ambiguous, emit no price candidate.

## P0.1 evaluation design

Use short, labeled utterances from YouTube tabs selected and captured by the user. Do not download video/audio, save captured tab audio, or send it to a cloud service. Keep any user-provided local benchmark clips outside version control and delete them after evaluation unless the user explicitly wants to retain them.

Cover these dimensions separately and in combinations:

- Northern, Central, and Southern Vietnamese speakers; different voices and speaking rates.
- Clear single-speaker speech; moderate music; moderate environmental noise; music plus noise.
- Two or more simultaneous speakers, including numbers spoken during overlap and just before/after overlap.
- Numbers spoken as words and common sales phrasing, with ground-truth transcript and intended numeric values. Number accuracy is the primary score; intended price is optional secondary ground truth.
- Audio with no target number, unrelated numbers, lyrics, and conversation to measure false number extraction.

Compare the primary Zipformer-VI path, Vosk small baseline, and offline multilingual Whisper on the same audio segments. The additional number-constrained Vosk lane is only an experiment in restricting the decoder vocabulary; it is not a separately trained number-recognition model. A/B test raw PCM against the current DPDFNet speech-enhancement candidate; evaluate source separation and automatic overlap detection separately before considering them for a later milestone. Do not assume a pipeline component is useful until number-level metrics improve.

Record aggregate results by condition:

- Transcript WER/CER.
- Exact-number accuracy and missed-number rate.
- False number candidates per hour of audio without target numbers.
- Overlap detection precision/recall and exact-number accuracy on overlap clips.
- Audio-to-candidate P50/P95 latency and process RAM on the target Windows PC.

Provisional design targets (not yet verified): at least 95% exact-number accuracy on clear single-speaker speech; at least 90% on single-speaker speech with moderate music/noise; no candidate for unresolved overlapping/low-confidence speech; and no more than one false number candidate per 30 minutes of audio without target numbers. Keep the existing latency and memory budgets in `docs/SPEC.md`; any model or separation path that exceeds them must be reported as a tradeoff, not silently accepted. Do not enable any real sender based on this prototype.

## Implementation order

1. Keep the tab RMS meter and partial/final distinction so connection, silence, and unstable text are visible.
2. Use the comparison window to capture labeled same-tab segments and build a baseline report for Zipformer/Vosk/Whisper.
3. Benchmark number-level accuracy and speech enhancement against raw PCM; keep Zipformer as primary only if labeled results support the choice.
4. Add overlap detection and evaluate source separation separately; abstain when overlapping prices cannot be isolated reliably.
5. Update acceptance evidence and only then decide which model fits the packaged Windows app.

## Feasibility check: number-constrained Vosk — 2026-10-21

A one-off experiment tested whether a narrow Vosk grammar could act as a faster number-focused recognizer without training a new acoustic model. It used the existing `vosk-model-small-vn-0.4` and a manually constructed 622-phrase grammar covering common readings from 1–20, `nghìn`, and `rồi`, plus `[unk]`. The grammar is incomplete and is not a production number grammar.

The input was recording offsets 00:06–00:08 from the user-provided screen recording `Học Con Số Dễ Quá P2 - Số Hàng Nghìn...mp4`. The user-labeled numbers were `[2000, 3000]`; a second voice saying “rồi, rồi” was also reported. The ASR rows were:

| Engine | Transcript | Parsed numbers | Warm-model time |
|---|---|---:|---:|
| Vosk unrestricted baseline | `rồi` | none | 1,244 ms |
| Vosk with 622-phrase number grammar | `rồi` | none | 37 ms |
| Zipformer-VI | `RỒI BA MẸ` | `[3]` | not measured correctly in this exploratory run |

The constrained Vosk result missed both labeled numbers (0/1 exact segment). The times include recognizer creation and decoding, exclude model loading, come from one short segment, and are not P50/P95 or live latency. This is evidence that a narrow decoding grammar can reduce work in this specific experiment, but it did not preserve number accuracy and is not suitable for the app or a live sender. The grammar was not a trained number model and did not cover arbitrary numbers or seller sentences.

No source audio was written by the experiment; it was decoded and processed in memory. The app now exposes the expanded grammar as an optional comparison lane only; Zipformer remains the configured primary engine, and no production decision/sender path uses the grammar. This does not count toward P0.1 acceptance. A custom streaming number model still needs a diverse, labeled training/evaluation corpus. The current repository rule prohibits persisting captured tab audio without an explicit user change to that privacy requirement; do not start dataset collection or training until that is resolved.

Model availability check on 2026-10-21: the sherpa-onnx catalog documents a Vietnamese offline Zipformer model, while its online/streaming transducer catalog did not list a Vietnamese model. This is a catalog observation, not proof that no third-party Vietnamese streaming model exists. The Vosk API exposes dynamic phrase grammars, but this experiment shows that restricting the output space alone does not guarantee number recall.

### Gipformer 1.5 and true-streaming Zipformer experiment — 2026-10-22

The optional benchmark now includes two local-only candidates while retaining the current Zipformer-VI 30M INT8 + Silero VAD path as the app core:

- **Gipformer 1.5 68M RNNT INT8** is an offline transducer. Its official inference example uses sherpa-onnx; the model card publishes benchmark results across Vietnamese speech datasets, but those are publisher-reported WER values and are not livestream number-accuracy measurements. The weights are MIT-licensed.
- **Zipformer-30M-RNNT-Streaming-6000h, chunk 16** is a genuine online transducer that can emit changing partial text while audio chunks arrive. On the evaluation sets listed in its model card, the streaming variant has higher (worse) WER than its offline sibling; this reinforces the need to compare latency and accuracy separately. Its license is CC-BY-NC-ND-4.0, so this repository downloads it only to the ignored local `models/` directory for evaluation. Do not modify, bundle, or redistribute these weights.

Download the two benchmark candidates explicitly (neither is downloaded by the app installer):

```powershell
.\.venv\Scripts\python.exe scripts\download_asr_experiments.py --gipformer --streaming-zipformer
```

Run the benchmark against a user-provided local video/audio file; PyAV decodes only the selected audio interval to in-memory mono 16 kHz samples and does not create an intermediate WAV:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[asr-benchmark]"
.\.venv\Scripts\python.exe scripts\benchmark_asr_experiments.py `
  --media "C:\path\to\labeled-video.mp4" --start 7 --duration 7 `
  --numbers "3000,4000,5000,6000" --realtime
```

If the exact time the target number finishes is known within the selected clip, add `--number-end-ms N`. With `--realtime`, the script then reports when the streaming model first emits that target after the labeled number end. This is local ASR + parser latency only; it excludes VAD endpoint delay, browser capture, extension transport, UI scheduling, sender action, and TikTok/network delivery. Audio is not uploaded or written to disk. The script never creates a sender.

Exploratory run record on the two screen-capture videos the user had supplied (2026-10-22):

| Input interval | Current offline Zipformer-VI | Gipformer 1.5 INT8 | Streaming Zipformer chunk-16 |
|---|---|---|---|
| Edge capture 00:07–00:14, real-time feeding (second run) | `BA NGHÌN BỐN NGHÌN RỒI NĂM LIỀN SÁU NGHÌN`; parsed `[3000, 4000, 5, 6000]`; 151 ms | `BA NGÀN BỐN TRĂM RỒI NGON LIỀN SÁU NGÀN`; parsed `[6000]`; 179 ms | `BA MẸ NGỦ LUÔN RỒI`; parsed `[3]`; decode total 388 ms, per-call P50/P95/max 18/21/22 ms, RTF 0.055. First partial was at audio offset 1.12 s: `BA`, which the number parser immediately interpreted as `[3]`; the model did not produce the complete spoken sequence. |
| Edge capture 00:00–00:07 | `RỒI`; no number; 121 ms | `RỒI RỒI`; no number; 159 ms | `RỒI`; no number; decode total 349 ms, RTF 0.050; first partial at audio offset 5.28 s. |

The first interval was paced as real-time audio; the second was decoded as fast as the CPU allowed. Neither segment has a verified ground-truth transcript aligned to the screen-capture offset. An earlier note labeled a source-video interval 00:00–00:07 as `[1000, 2000, 3000, 4000]`, but the screen recording's first seven seconds transcribe only as “rồi”; these are different time origins and the label cannot be applied to this capture. Therefore **no exact-number accuracy score is valid for these runs**. The 00:07–00:14 outputs show Gipformer extracted one value and streaming Zipformer produced a plausible but different numeric token; without a verified transcript, neither is evidence of accuracy. One short clip is insufficient to select a new production engine or claim a latency target.

Across the two runs, model initialization ranged from about 0.8–1.45 s for current Zipformer, 0.97–1.17 s for Gipformer, and 1.2–1.46 s for streaming Zipformer on this workstation. Warm inference time excludes this one-time load. The streaming model's first partial is not necessarily a number; in this sample a partial word became a numeric candidate before the model could settle. Chunk decode time is not number-end-to-candidate latency. Add correctly aligned end-of-number labels and repeat across clean, noisy, accent, and overlap samples before deciding whether to change the core.

Benchmark code added: `src/pricetyper/asr/experimental_engines.py`, `scripts/download_asr_experiments.py`, and `scripts/benchmark_asr_experiments.py`. Candidate model files remain ignored under `models/`.

### Benchmark-only integration — 2026-10-21

The ASR comparison window now has a fourth lane, `Vosk số`, implemented with Vosk's phrase-grammar constructor and the existing Vietnamese Vosk acoustic model. It enumerates 1,341 phrases built from common 1–20 readings, contiguous counting sequences, `nghìn`, and the connector `rồi`, with `[unk]`. Raw and DPDFNet-enhanced audio are both scored. The session shares one loaded Vosk acoustic model between the unrestricted and grammar recognizers to avoid loading a duplicate model. The lane is visibly marked experimental and is excluded from branch and strict consensus so it cannot alter the prior three-model preview. It returns only phrases in its finite grammar and may ignore a seller sentence outside that vocabulary; it is not an independently trained number-only model.

The same user-provided 00:06–00:08 recording segment was decoded and evaluated in memory again. Label: `[2000, 3000]`; condition: overlapping speech, with the second voice reported to say “rồi, rồi”. An initial integration measurement below used the earlier 622-phrase grammar; the final 1,341-phrase grammar was then re-run on the same segment. Model and recognizer initialization occurred before inference timing; audio was not saved.

| Lane | Transcript | Parsed numbers | Exact | Inference |
|---|---|---:|---:|---:|
| Vosk baseline | `rồi` | none | No; missed 2 | 1295.9 ms |
| Vosk number grammar (1,341 phrases) | `rồi` | none | No; missed 2 | 31.0 ms |
| Zipformer-VI | `RỒI BA MẸ` | `3` | No; missed 2, one false candidate | 44.2 ms |

This single overlap segment shows the final grammar lane was faster for this run but did not detect either number. It cannot establish a speed or accuracy advantage on other speech. The labels for overlapping speakers are incomplete, so do not calculate WER/CER or treat the recognition of `3` as a reliable false-alarm rate. More clean and noisy labeled segments are required. The app tests cover grammar construction, recognizer configuration, benchmark scoring, and proof that grammar output does not enter consensus; they do not pass ASR accuracy acceptance.

## References

- [OpenAI Whisper introduction](https://openai.com/index/whisper/): multilingual ASR and reported robustness to accents/background noise; not a guarantee for Vietnamese livestreams.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper): CTranslate2 implementation, with CPU int8 support; project access checked 2026-10-19.
- [OpenAI Whisper transcription implementation](https://github.com/openai/whisper/blob/main/whisper/transcribe.py): distinguishes speech transcription from translation; project access checked 2026-10-19.
- [Vosk model list](https://alphacephei.com/vosk/models): published Vietnamese Vivos WER; this is not a livestream benchmark.
- [Vosk Python API](https://github.com/alphacep/vosk-api/blob/master/python/vosk/__init__.py) and [official grammar example](https://github.com/alphacep/vosk-api/blob/master/python/example/test_words.py): dynamic word/phrase grammar API; model support and recognition quality must be checked for the selected model.
- [WebRTC Audio Processing Module](https://webrtc.googlesource.com/src/+/refs/heads/main/modules/audio_processing/g3doc/audio_processing_module.md): includes noise suppression, AGC, and echo cancellation.
- [SpeechBrain speech separation and enhancement](https://speechbrain.readthedocs.io/en/stable/tutorials/basics/what-can-i-do-with-speechbrain.html): candidate methods to benchmark, not a preselected production dependency.
- [pyannote.audio](https://github.com/pyannote/pyannote-audio): speaker diarization, voice activity, speaker changes, and overlapped-speech detection components.
- [sherpa-onnx Zipformer-VI models](https://k2-fsa.github.io/sherpa/onnx/pretrained_models/offline-transducer/zipformer-transducer-models.html): official Vietnamese offline transducer model instructions; publisher training hours do not predict livestream price accuracy.
- [sherpa-onnx online transducer catalog](https://k2-fsa.github.io/sherpa/onnx/pretrained_models/online-transducer/index.html): model availability catalog checked 2026-10-21; a missing Vietnamese entry is only a catalog observation.
- [sherpa-onnx DPDFNet](https://k2-fsa.github.io/sherpa/onnx/speech-enhancement/dpdfnet.html): offline and online speech enhancement with 16 kHz variants; enhancement does not separate speakers.
