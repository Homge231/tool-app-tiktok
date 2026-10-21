# PriceTyper — công nghệ và mã nguồn hiện tại

Cập nhật: 21/10/2026

Tài liệu này mô tả những gì đang có trong workspace: prototype nhận dạng số trên YouTube, lát cắt M8 TikTok Web dùng extension Chromium, và bộ cài Windows preview. Đây chưa phải bản phát hành công khai hoặc đã nghiệm thu browser.

## Luồng xử lý

```text
Tab YouTube hoặc TikTok Live do người dùng chọn
  → extension Chromium (Manifest V3, tabCapture)
  → AudioWorklet / PCM mono 16 kHz, PCM16, từng khung 40 ms
  → WebSocket chỉ nghe trên 127.0.0.1:8765
  → Python: nhận audio trong bộ nhớ
  → nhánh audio gốc và nhánh thử khử nhiễu DPDFNet
  → Silero VAD → Zipformer-VI (primary) / Vosk / faster-whisper (benchmarks)
  → TikTok number scope: phân tích số tiếng Việt, bỏ qua ngưỡng lọc giá
  → giao diện Tkinter tách candidate tạm từ partial khỏi final
TikTok final candidate
  → cùng WebSocket extension bridge → kiểm tra tab ID/host/path/input → dispatch action trong tab đã capture
```

Extension chỉ capture tab người dùng chọn và không đọc lịch sử chat/bình luận. TikTok mặc định chỉ điền số final; người dùng có thể bật tùy chọn Enter khi disarmed, rồi F8 mới cho phép thao tác. Acknowledgement Enter chỉ xác nhận event được dispatch, chưa chứng minh comment đã xuất hiện. Chế độ so sánh giữ tối đa 20 giây audio của một đoạn trong RAM rồi xóa; audio không gửi cloud hoặc ghi file.

## Công nghệ

| Phần | Công nghệ đang dùng | Vai trò / giới hạn hiện tại |
|---|---|---|
| Ứng dụng | Python 3.12 trở lên; `tkinter`/`ttk`; PyInstaller | GUI desktop Windows có bản dựng one-directory và bộ cài NSIS per-user; chưa phát hành công khai. |
| Capture và action trình duyệt | Chromium Extension Manifest V3, `chrome.tabCapture`, `chrome.scripting`, offscreen document, AudioWorklet | Capture âm thanh và dispatch fill/optional Enter trong tab người dùng chọn. Chrome/Edge/Cốc Cốc chưa được nghiệm thu lại với build này. Firefox, Safari và mobile chưa hỗ trợ. |
| Audio/action bridge | WebSocket `websockets`, loopback `127.0.0.1:8765`, NumPy | Chuyển PCM mono 16 kHz, signed PCM16 từng khung 40 ms; TikTok action acknowledgement quay lại cùng kết nối. |
| ASR chính | `sherpa-onnx==1.13.8`, Zipformer-VI 30M INT8 + Silero VAD | Chạy local. Model ASR là offline; VAD chốt câu khi có khoảng nghỉ, partial phải giải mã lại đoạn đang nói. Độ chính xác trên livestream chưa được chấp nhận. |
| ASR baseline | Vosk `0.3.45` và model tiếng Việt `vosk-model-small-vn-0.4` | Chỉ dùng làm đối chứng trong benchmark hoặc khi chọn `asr.engine: vosk`; không còn là mặc định. |
| ASR đối chứng | faster-whisper `1.2.1`, model đa ngôn ngữ `small` mặc định, CPU `int8` | Nhận dạng offline; có thể đổi model `base`, `small`, `medium`; thời gian suy luận có thể vượt mục tiêu realtime tùy máy. |
| Thử khử nhiễu | DPDFNet baseline qua sherpa-onnx, 16 kHz | So sánh nhánh audio đã enhancement với audio gốc. Đây là thử nghiệm khử nhiễu, không phải tách nhạc/giọng hay tách nhiều người nói; có thể làm méo âm tiết. |
| Trích giá | Bộ lọc ngữ cảnh và parser tiếng Việt trong `src/pricetyper/parsing/` | Giá trần hiểu là đồng; `nghìn`/`ngàn`/`k` nhân 1.000. Candidate không đồng nghĩa với giá đã được xác minh đúng. |
| Đánh giá | WER/CER, khớp giá chính xác, giá bỏ sót, candidate thừa, thời gian xử lý và P50/P95 theo phiên | Benchmark dùng câu chuẩn do người dùng nhập. Cần nhiều đoạn có nhãn; một mẫu không chứng minh độ chính xác hoặc độ trễ realtime. |
| Kiểm thử | pytest, Ruff, Node test cho popup extension | Có unit/regression tests; browser capture và độ chính xác trên video thật vẫn cần kiểm tra thủ công. |

Trong cửa sổ so sánh, cùng một đoạn được chạy qua ba ASR trên cả audio gốc lẫn audio DPDFNet. Preview nghiêm ngặt chỉ hiện danh sách candidate khi cả sáu kết quả đồng ý; nếu bất đồng hoặc người dùng đánh dấu chồng lấp, prototype abstain. Đây là heuristic bảo thủ, không phải confidence đã hiệu chuẩn. GUI chính có thể hiện giá tạm từ ASR partial nhưng tách nó khỏi giá cuối; chỉ số `chunk → ASR event` đo độ trễ xử lý sau khi bridge nhận một chunk, không tính chờ chốt câu và không đại diện cho thời gian bình luận xuất hiện trên live.

## Những gì prototype chưa làm

- Chế độ YouTube test không mở TikTok, không đọc chat và không gửi tin nhắn; GUI khóa sender bằng `NullSender`. TikTok Web prototype thao tác trên tab Live đã capture, nhưng browser support và action thực tế chưa được kiểm tra.
- Chưa chạy trên Android/mobile.
- Chưa có diarization, phát hiện chồng lấp tự động, hay source separation để tách từng người nói.
- Chưa xác nhận độ chính xác giá hoặc mục tiêu dưới một giây trên video/livestream thật. ASR 100% không được đảm bảo.
- Candidate từ ASR partial chỉ là dự đoán dao động để quan sát phản ứng sớm; không thay candidate cuối và không được tính là giá đã xác minh.
- Installer personal preview đã có, nhưng extension chưa lên cửa hàng, chưa có chữ ký nhà phát hành, chưa kiểm tra trên tài khoản Windows sạch và chưa nghiệm thu TikTok/browser. Đây chưa phải bản phát hành cho người dùng phổ thông.

Các sender module cũ có trong source tree vì nền tảng kỹ thuật của dự án, nhưng không được kích hoạt trong chế độ thử YouTube. Cấu hình mẫu để trống sender; không bật gửi khi chạy prototype.

## Cài đặt và chạy chế độ so sánh local

Yêu cầu Windows 10/11, Python 3.12 và trình duyệt Chromium để thử TikTok Web. Từ thư mục đã giải nén source:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,robust-asr]"
Copy-Item config.example.yaml config.yaml
```

Tải Zipformer-VI, Silero VAD và DPDFNet vào thư mục `models/` bằng:

```powershell
.\.venv\Scripts\python.exe scripts\download_robust_asr_models.py
```

Sau đó chạy:

```powershell
.\run-youtube-test.ps1 -AsrCompare
```

Lệnh trên cần thêm model Vosk để benchmark baseline; tải `vosk-model-small-vn-0.4` từ [trang model chính thức](https://alphacephei.com/vosk/models) vào `models/vosk-model-small-vn-0.4`. Chỉ chạy YouTube test mặc định thì không cần model Vosk.

Nạp thư mục `browser_extension/` tại trang Extensions ở chế độ developer trong trình duyệt tương ứng, mở tab YouTube hoặc TikTok Live cần thử, rồi dùng popup extension để bắt đầu capture. Xem `docs/PROTOTYPE_YOUTUBE.md` và `docs/PROTOTYPE_TIKTOK_WEB.md` để biết workflow riêng cho từng chế độ. Chỉ capture tab mà bạn có quyền sử dụng.

## Các file mã nguồn chính

- `src/pricetyper/audio/browser_tab.py`: WebSocket bridge nhận audio từ extension.
- `src/pricetyper/senders/browser_extension_sender.py`: probe và dispatch action qua cùng phiên extension/tab.
- `browser_extension/`: manifest, popup, service worker, offscreen capture và AudioWorklet.
- `src/pricetyper/asr/`: engine chọn theo cấu hình, Zipformer/VAD, Vosk baseline, so sánh ASR và DPDFNet enhancement.
- `src/pricetyper/asr/zipformer_engine.py`: adapter Zipformer-VI offline, phân đoạn bởi Silero VAD và partial re-decode.
- `src/pricetyper/parsing/`: nhận biết ngữ cảnh giá và số tiếng Việt.
- `src/pricetyper/ui/asr_comparison.py`, `src/pricetyper/ui/gui.py`: cửa sổ benchmark và GUI nhận dạng.
- `scripts/download_robust_asr_models.py`: tải weights Zipformer-VI, Silero VAD và DPDFNet vào `models/`.
- `tests/`: kiểm thử parser, bridge, GUI logic, ASR comparison và extension.

## Tài liệu kỹ thuật tham khảo

- [Đặc tả dự án](SPEC.md)
- [Quy trình prototype YouTube](PROTOTYPE_YOUTUBE.md)
- [Kế hoạch độ bền ASR và các giới hạn](ASR_ROBUSTNESS.md)
- [Trạng thái triển khai và bằng chứng kiểm tra](IMPLEMENTATION_STATUS.md)
- [Zipformer-VI chính thức của sherpa-onnx](https://k2-fsa.github.io/sherpa/onnx/pretrained_models/offline-transducer/zipformer-transducer-models.html)
- [DPDFNet speech enhancement chính thức của sherpa-onnx](https://k2-fsa.github.io/sherpa/onnx/speech-enhancement/dpdfnet.html)
