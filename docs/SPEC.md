PriceTyper — Đặc tả kỹ thuật và hướng dẫn Antigravity
Phiên bản 1.0 · 19/10/2026 · Ngôn ngữ: tiếng Việt · Đối tượng đọc: lập trình viên và AI agent (Antigravity)
0. Quy ước
Tài liệu có hai phần. Phần A (§1–§12) đặc tả tool PriceTyper. Phần B (§13–§19) hướng dẫn dùng Antigravity để xây dựng tool theo Phần A. Toàn bộ tài liệu được xuất sang Markdown và lưu thành docs/SPEC.md trong dự án (§16).
Nhãn xác minh dùng xuyên suốt:
Nhãn
Ý nghĩa
ĐÃ XÁC MINH
Đối chiếu trực tiếp với tài liệu hoặc mã nguồn chính thức; nguồn ghi kèm hoặc ở §19.
ĐÃ KIỂM THỬ
Mã tham chiếu trong tài liệu đã chạy trong môi trường kiểm thử (Python 3.12) và qua toàn bộ test nêu kèm.
THIẾT KẾ
Quyết định thiết kế của tool, không phải sự kiện bên ngoài. Giá trị số là điểm khởi đầu, cần hiệu chỉnh bằng dữ liệu thật.
Không đủ dữ liệu để xác minh
Không có nguồn hoặc phép thử để khẳng định. Cách tự xác minh nằm ở §11.
PHẢI = bắt buộc; NÊN = khuyến nghị; CÓ THỂ = tùy chọn. FR-xx = yêu cầu chức năng; NFR-xx = yêu cầu phi chức năng; U-xx = mục chưa xác minh (§11). Ngày đối chiếu nguồn: 2026-10-19.
1. Mục tiêu và phạm vi
1.1 Mục tiêu
Mục tiêu cuối là ứng dụng Windows cài đặt được, có shortcut và không yêu cầu người dùng cài Python hoặc chạy PowerShell. Lõi hiện vẫn có thể viết bằng Python.

Prototype có hai chế độ tách biệt. `gui --youtube-test` nhận dạng số trên YouTube, dùng Zipformer-VI offline và chỉ hiển thị transcript/số; chế độ này luôn khóa sender. `gui --tiktok-web` là thử nghiệm Windows dùng extension Chromium: nhận audio tab TikTok Live do người dùng chọn, chạy ASR/parser số cục bộ và xử lý số cuối ở kết quả ASR final. Mặc định app chỉ điền `@<số>` vào ô nhập trống; tùy chọn gửi comment bằng một phím Enter tắt sẵn và chỉ bật được sau khi kiểm tra tab. Chế độ TikTok mặc định dry-run/disarmed; cần rời dry-run và nhấn F8 để thao tác. Enter được phát không chứng minh comment đã xuất hiện. Độ chính xác, tương thích browser và độ trễ đầu-cuối chưa được nghiệm thu. Xem `docs/PROTOTYPE_TIKTOK_WEB.md` và `docs/IMPLEMENTATION_STATUS.md`.

Yêu cầu sản phẩm tiếp theo là dùng được trên nhiều trình duyệt desktop, không hard-code Edge hoặc giả định người dùng cài Chrome. M8 đang triển khai lát cắt đầu bằng extension Chromium; các browser/OS chỉ được công bố sau khi adapter bắt đúng audio tab và thao tác được trong chính tab đó qua kiểm tra thực tế. Nếu thiếu API audio tab thì báo không hỗ trợ, không fallback sang microphone/system loopback. Xem ma trận và bằng chứng tại `docs/BROWSER_COMPATIBILITY.md`.
1.2 Kịch bản chuẩn
1. Với kiểm tra nhận dạng, người dùng chạy `pricetyper gui --youtube-test`; chế độ này chỉ hiển thị số và luôn khóa sender.
2. Với TikTok Web prototype, người dùng chạy `pricetyper gui --tiktok-web`, mở TikTok Live trong trình duyệt Chromium, rồi chủ động bấm extension để capture tab. App không mở browser/profile thứ hai. Xem `docs/PROTOTYPE_TIKTOK_WEB.md`.
3. TikTok mode bắt đầu dry-run/disarmed và ở chế độ số, không áp ngưỡng/lọc giá. Nút kết nối kiểm tra tab và ô nhập nhìn thấy được, rời dry-run nhưng vẫn chưa arm. Mặc định, F8 bật/tắt việc điền `@<số>`; tùy chọn gửi phải được bật khi disarmed rồi F8 mới arm. Chỉ ASR final được phép tạo quyết định; partial chỉ hiển thị. Số nhận dạng trên giao diện vẫn hiển thị dạng thuần; comment trong ô chat có tiền tố `@`. Khi bật gửi, app phát một synthetic DOM `KeyboardEvent` Enter duy nhất sau khi điền và không thử lại. Sự kiện này không phải phím bấm native (`isTrusted` là false), TikTok có thể bỏ qua; acknowledgement không xác nhận comment xuất hiện. F10 dừng khẩn.
4. YouTube mode không tạo sender thật, không mở TikTok và không gửi tin. TikTok mode không đọc danh sách bình luận/chat; `discover` chỉ đọc thuộc tính của ô nhập đang hiển thị.
1.3 Trong phạm vi v1
• YouTube number prototype: capture đúng tab qua extension; ASR/parser cục bộ; hiển thị số thuần, luôn NullSender.
• TikTok Web prototype (M8 đang triển khai, chưa nghiệm thu): Windows + extension Chromium, capture audio cục bộ và xử lý số cuối của ASR final trong cùng tab TikTok Live đã chọn. Number mode bỏ qua price gate nên có thể chọn số nhỏ; mặc định chỉ điền `@<số>` vào input trống (số nhận dạng vẫn hiển thị dạng thuần trong app). Người dùng có thể bật rõ ràng tùy chọn gửi bằng Enter; vẫn cần rời dry-run và nhấn F8. Không gửi từ partial, không thử lại, không xác nhận được comment xuất hiện. Mục tiêu người dùng là dưới 1 giây từ âm cuối đến lúc comment xuất hiện, nhưng phần xử lý local và việc TikTok phân phối comment là hai khoảng khác nhau; không thể bảo đảm thời gian phân phối phía TikTok. P95 local đến lúc phát Enter cần được đo từ audio có nhãn. Exact-number accuracy phải đánh giá riêng, không đánh đổi độ đúng để đạt tốc độ. Browser, độ chính xác và latency chưa được chấp nhận.
• Không dùng livestream thật làm fixture kiểm thử tự động; việc nhận dạng/audio chưa được chấp nhận phải được ghi riêng trong status.
• Bản phát hành mục tiêu: ứng dụng Windows cài đặt được, có shortcut/uninstaller và đóng gói runtime; chưa thuộc prototype.
• Android/scrcpy là hướng riêng ở giai đoạn sau.
1.4 Ngoài phạm vi v1
• iOS: không có đường thu âm thanh và điều khiển đã xác minh (U11).
• Giá có “triệu” (ví dụ “một triệu hai”) và dải “nghìn + số” (ví dụ “một nghìn hai trăm”): bị bỏ qua, không gửi.
• Từ lóng chỉ tiền (ví dụ “lít”, “xị”): không hỗ trợ.
• Nhiều tài khoản, nhiều phiên đồng thời.
• Né phát hiện hoặc né giới hạn của nền tảng; tự thanh toán; tự điền địa chỉ.
• Đọc hoặc thu thập chat, bình luận, dữ liệu của người khác.
• macOS và Linux: không thuộc tiêu chí nghiệm thu. README gói keyboard nêu Linux cần quyền root (ĐÃ XÁC MINH).
• Tự động chọn biến thể/mua hàng, thanh toán và phát hành bản cài đặt.
1.5 Ma trận nền tảng
Nền tảng đích
Thu âm thanh
Gửi chat
Trạng thái
YouTube trên Windows (prototype)
Chrome tabCapture của tab người dùng chọn
Không có
Phạm vi hiện tại: nhận dạng/parser בלבד
TikTok Live trên Chromium/Windows (M8 prototype)
Extension tabCapture của tab TikTok Live người dùng chọn
Action extension trong cùng tab; chỉ sau khi rời dry-run và F8
Code ban đầu có; chưa kiểm tra browser/action thực tế, chưa chấp nhận
App Android ≥ 11
scrcpy rồi loopback PC
desktop trên cửa sổ scrcpy; dự phòng adb
Tích hợp tương lai
App Android ≤ 10
scrcpy không thu được âm thanh (ĐÃ XÁC MINH)
—
Ngoài v1
App hoặc giả lập trên PC
loopback
desktop
Trong v1
iOS
—
—
Ngoài v1
1.6 Giới hạn và rủi ro đã biết
• Độ trễ bằng 0 không khả thi. Tool chỉ phản ứng sau khi âm thanh đã phát ra trên máy. Độ trễ truyền của luồng TikTok không kiểm soát được. Tool chỉ tối thiểu hóa độ trễ phía xử lý (thu, nhận dạng, quyết định, gửi); cách đo ở §9.3.
• Giả định tích hợp: theo chỉ dẫn hiện tại, milestone này giả định cách tương tác được phép; đây không phải kết luận pháp lý hay xác nhận điều khoản áp dụng. Không triển khai né phát hiện, né giới hạn hoặc mua hàng tự động.
• Chất lượng nhận dạng. WER của model Vosk tiếng Việt là 15,70 trên bộ Vivos (ĐÃ XÁC MINH, alphacephei.com/vosk/models). WER trên âm thanh livestream có nhạc nền và nhiều người nói: Không đủ dữ liệu để xác minh (U5).
• Vosk small hiện là baseline prototype, chưa đáp ứng acceptance cho livestream. Nhạc, tiếng ồn, ba vùng giọng Việt và giọng nói chồng lấp phải được đánh giá riêng ở P0.1; không tuyên bố lọc/nhận dạng hoàn hảo. Tool nhận dạng ngôn ngữ thực sự phát trong tab, không làm dịch thuật.
• Gửi sai là mất lượt. Parser ưu tiên chính xác hơn độ phủ: mơ hồ thì không gửi (§6.4).
1.7 Khác biệt so với prototype v0 (tin nhắn trước)
Hạng mục
v0
v1
Lý do
pyautogui.PAUSE
không đặt; mặc định 0,1 giây (ĐÃ XÁC MINH trong mã pyautogui 0.9.54)
đặt 0
v0 gọi 3 lệnh mỗi lần gửi (click, typewrite, press), cộng dồn khoảng 0,3 giây trễ
Lấy mẫu
resample bằng scipy từng khối 100 ms
yêu cầu soundcard thu thẳng 16000 Hz mono; mã soundcard 0.4.6 khởi tạo luồng WASAPI với cờ resample và remix (ĐÃ XÁC MINH)
bỏ phụ thuộc scipy và nhiễu ở biên khối
Parser
“một trăm hai” = 102
mặc định 120 (cách nói rút gọn)
quy ước nói giá (THIẾT KẾ); công tắc parser.shorthand
Ổn định kết quả
đếm số khối liên tiếp giống nhau
3 tầng: closed, complete, open
từ kết thúc (“nha”, “k”) cho phép gửi ngay
Lọc
chỉ khoảng giá
thêm loại ngữ cảnh, lọc đếm ngược, 2 mức cooldown, giới hạn mỗi phút
giảm gửi nhầm
Python
không ghi
≥ 3.12
numpy 2.5.4 (bản mới nhất) yêu cầu ≥ 3.12 (ĐÃ XÁC MINH trên PyPI)
2. Yêu cầu
2.1 Yêu cầu chức năng
Mã
Yêu cầu
Tiêu chí nghiệm thu
FR-01
Chuẩn hóa âm thanh của tab video người dùng chọn thành 16000 Hz mono int16
YouTube prototype hiển thị ASR/parser output từ đúng tab; thay đổi âm lượng output không làm thay đổi PCM đầu vào ASR
FR-02
Zipformer-VI nhận dạng local trên đoạn do Silero VAD phân đoạn; phát partial định kỳ và final khi chốt câu
replay WAV mẫu: nhận dạng Zipformer; final được phát sau khi VAD kết thúc hoặc flush đoạn cuối; partial được gắn nhãn riêng
FR-03
Trích giá trị số tiếng Việt theo ngữ pháp §6.4; YouTube number mode hiển thị số thô không qua gate giá
Test parser gồm `SỐ CHÍN` → 9; number preview tách dãy đếm `một hai ba... chín` thành từng số, giữ số cuối làm candidate, và vẫn bỏ qua ngưỡng/ngữ cảnh giá
FR-04
Lọc theo khoảng giá, ngữ cảnh, đếm ngược
15/15 vector §6.5 qua
FR-05
Quyết định gửi theo tầng giữ, cooldown, giới hạn mỗi phút
bảng vết §6.5 tái lập đúng 5 dòng
FR-06
Gửi số vào ô chat bằng sender đã chọn, đúng 1 lần mỗi lệnh
test trang giả: window.__sent bằng ['199']
FR-07
Bật hoặc tắt bất kỳ lúc nào bằng hotkey, nút GUI, lệnh CLI; nhận dạng luôn chạy
sau khi tắt không còn lệnh gửi nào được thực thi; bật lại không khởi động lại nhận dạng. Sau lần điền thành công, chỉ báo ASR/mức audio vẫn tiếp tục cập nhật và F8 vẫn disarm được; lỗi cập nhật giao diện đơn lẻ không được làm dừng vòng poll.
FR-08
Phím dừng khẩn
tiến trình thoát mã 130; sender được đóng
FR-09
Chế độ dry_run: chạy toàn bộ trừ bước gửi
sender không bị gọi; log vẫn có decision
FR-10
Replay tệp WAV qua cùng pipeline
pricetyper replay chạy offline
FR-11
Log JSONL theo §6.8
mọi quyết định có đúng 1 dòng decision
FR-12
Công cụ record, calibrate, discover, latency
mỗi lệnh có trong pricetyper --help
FR-13
GUI Tkinter theo §7.2
checklist §7.2 đạt
FR-14
YouTube test-only mode bắt audio tab do người dùng chủ động chọn, chạy nhận dạng/trích số và khóa mọi sender thật
Test `--youtube-test` dùng NullSender, hiển thị số không qua gate giá, không mở TikTok, không gửi chat; kiểm tra thủ công với URL video đã ghi
FR-15
Bản phát hành cuối có installer và shortcut Windows; người dùng không cần Python/PowerShell. Trang cuối bộ cài có lựa chọn mở trợ lý thiết lập extension; bản preview local vẫn yêu cầu người dùng xác nhận nạp extension thủ công.
Kiểm tra trên máy Windows sạch: cài, mở shortcut, trợ lý extension, gỡ cài đặt; milestone sau prototype
FR-16
Nhận dạng lời nói tiếng Việt khi có nhạc/ồn, nhiều accent vùng miền và nhiều người nói
P0.1 phải benchmark có nhãn trên audio single-speaker sạch, speech + music/noise, ba vùng giọng Bắc/Trung/Nam và đoạn chồng lấp; ưu tiên exact-number accuracy, số bỏ sót/thừa, WER/CER, P50/P95 latency và RAM. Giá qua gate là phép đo phụ. Phân đoạn chồng lấp/không chắc không được đoán số; chỉ đạt khi có kết quả benchmark tái lập, không chỉ qua unit test.
2.2 Yêu cầu phi chức năng
Mã
Yêu cầu
Nhãn
NFR-01
Mục tiêu người dùng: P95 dưới 1 giây từ âm cuối của số tới lúc comment xuất hiện. Ứng dụng chỉ có thể tối ưu/đo thời gian local đến lúc điền hoặc phát Enter; không kiểm soát hoặc xác nhận độ trễ mạng/phân phối comment của TikTok. Không gửi/điền partial hoặc giảm độ chắc chắn chỉ để đạt tốc độ. Chỉ số GUI hiện tại bắt đầu ở chunk đóng VAD, chưa tính VAD chờ im lặng và không phải end-to-end.
THIẾT KẾ; chưa nghiệm thu; cần benchmark audio có nhãn và quan sát thủ công theo §9.3
NFR-02
Parser, gate và decider ≤ 5 ms mỗi sự kiện
THIẾT KẾ
NFR-03
RAM tiến trình ≤ 1 GB với model nhỏ
THIẾT KẾ; alphacephei nêu model nhỏ cần khoảng 300 MB khi chạy (nhận định chung cho model nhỏ)
NFR-04
Không gửi dữ liệu ra mạng, trừ lưu lượng của trình duyệt hoặc ADB do người dùng khởi tạo
THIẾT KẾ
NFR-05
Python ≥ 3.12; Windows 10/11
THIẾT KẾ
NFR-06
Một luồng sender; lệnh gửi thực thi tuần tự, không thử lại
THIẾT KẾ
NFR-07
run.start_armed mặc định false
THIẾT KẾ
3. Kiến trúc
3.1 Luồng dữ liệu
AudioSource --audio_q--> AsrEngine --event_q--> [Parser > Gate > Decider] --send_q--> Sender --> ô chat
loopback / wav           Zipformer + VAD          ^        |
PCM int16 16 kHz         AsrEvent                |        +--> Logger (JSONL)
                                       armed (threading.Event) <-- Controller <-- hotkey / GUI / CLI
3.2 Luồng (thread) và hàng đợi
Thread
Việc
Quy tắc
main
GUI Tk (mainloop) hoặc vòng chờ CLI
Tk PHẢI chạy ở thread chính
audio
đọc nguồn âm thanh vào audio_q
queue.Queue(maxsize=audio.queue_max_chunks); nếu đầy thì xóa audio tồn, tăng generation, disarm, reset ASR ở consumer, giữ chunk mới nhất và log/audio cảnh báo. Final đầu sau khoảng trống được hạ thành partial, không gửi.
asr
audio_q qua engine được chọn vào event_q
Zipformer/VAD hoặc Vosk tùy `asr.engine`; mỗi engine chỉ dùng trong thread ASR
decide
event_q.get(timeout=0.01); mỗi vòng gọi Decider.tick()
chu kỳ tick 10 ms để nhả lệnh đang giữ
sender
send_q vào sender.send()
toàn bộ đối tượng Playwright PHẢI tạo và dùng trong thread này (THIẾT KẾ: API đồng bộ của Playwright gắn với thread tạo ra nó)
hotkey
thư viện keyboard
callback chỉ gọi controller.toggle() hoặc controller.panic()
3.3 Trạng thái điều khiển
Trạng thái
Nhận dạng
Gửi
Chuyển trạng thái
LISTENING (mặc định)
chạy
không
toggle sang ARMED
ARMED
chạy
có
toggle sang LISTENING; 3 lần send_failed liên tiếp sang LISTENING
STOPPED
dừng
không
kết thúc tiến trình
armed là threading.Event. Được kiểm tra hai lần: trong Decider._decide và ngay trước sender.send() trong thread sender.
3.4 Kiểu dữ liệu và giao diện (src/pricetyper/types.py)
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class AsrEvent:
    kind: Literal['partial', 'final']
    text: str
    t_ns: int          # time.perf_counter_ns() lúc tạo sự kiện
    t_audio_ns: int    # perf_counter_ns lúc khối âm thanh gây ra sự kiện được thu xong


@dataclass(frozen=True)
class SendCommand:
    value: int
    text: str          # sau khi áp output.template
    t_audio_ns: int    # lấy từ sự kiện làm đổi text lần cuối trước khi nhả
    t_decided_ns: int


@dataclass(frozen=True)
class SendResult:
    ok: bool
    t_start_ns: int
    t_end_ns: int
    error: str | None = None


class AudioSource(Protocol):
    def start(self) -> None: ...
    def read(self) -> tuple[bytes, int] | None: ...   # (pcm int16, t_audio_ns); None = hết nguồn (wav)
    def stop(self) -> None: ...


class AsrEngine(Protocol):
    def feed(self, pcm: bytes, t_audio_ns: int) -> list[AsrEvent]: ...
    def reset(self) -> None: ...


class Sender(Protocol):
    name: str
    def prepare(self) -> None: ...        # raise SenderPrepareError nếu chưa sẵn sàng
    def send(self, text: str) -> SendResult: ...
    def close(self) -> None: ...
3.5 Ngân sách độ trễ
Đoạn
Nội dung
Mục tiêu
L0
độ trễ luồng TikTok và phát âm thanh
không kiểm soát được
L1
thu âm: khối chunk_ms cộng chu kỳ thiết bị; soundcard mặc định blocksize = deviceperiod[0] × samplerate (ĐÃ XÁC MINH trong mã nguồn)
khoảng chunk_ms cộng 1 chu kỳ thiết bị (THIẾT KẾ)
L2
nhận dạng: từ khối âm thanh chứa từ cuối đến lúc partial có con số
P50 ≤ 400 ms (THIẾT KẾ; Không đủ dữ liệu để xác minh, U6)
L3
parser, gate, decider
≤ 5 ms (THIẾT KẾ)
L4
thời gian giữ theo tầng
0 / 120 / 350 ms (THIẾT KẾ)
L5
sender
playwright ≤ 50 ms; desktop ≤ 30 ms với PAUSE = 0; adb: Không đủ dữ liệu để xác minh (U14)
4. Cấu trúc dự án
pricetyper/
├─ AGENTS.md                         # §15
├─ README.md
├─ pyproject.toml                    # §10
├─ config.example.yaml               # mẫu; sao chép thành config.yaml
├─ config.yaml                       # cấu hình gốc (không commit)
├─ config.local.yaml                 # ghi đè do calibrate và discover sinh ra (không commit)
├─ .agents/
│  ├─ rules/{parser.md, senders.md}  # §15
│  └─ skills/pricetyper-milestone/SKILL.md
├─ docs/SPEC.md                      # tài liệu này, xuất Markdown
├─ src/pricetyper/
│  ├─ __init__.py  __main__.py  cli.py  config.py  types.py
│  ├─ pipeline.py  controller.py  logging_utils.py
│  ├─ audio/{__init__.py, loopback.py, wav_source.py}
│  ├─ asr/{factory.py, zipformer_engine.py, vosk_engine.py, comparison.py}
│  ├─ parsing/{__init__.py, vi_number.py, gate.py}
│  ├─ decision/{__init__.py, decider.py}
│  ├─ senders/{__init__.py, playwright_sender.py, desktop_sender.py, adb_sender.py, null_sender.py}
│  ├─ ui/{__init__.py, gui.py, hotkeys.py}
│  └─ tools/{record.py, calibrate.py, discover.py, latency.py}
├─ tests/
│  ├─ test_vi_number.py  test_gate.py  test_decider.py  test_config.py
│  ├─ test_senders_fake_page.py  test_cli.py
│  ├─ fixtures/fake_live.html
│  └─ data/                          # WAV tự thu (không commit)
├─ models/                           # model Zipformer/VAD/Vosk (không commit)
├─ logs/                             # log JSONL (không commit)
└─ .pw-profile/                      # profile Chrome của Playwright (không commit)
.gitignore PHẢI chứa: models/, logs/, .pw-profile/, config.yaml, config.local.yaml, tests/data/, .venv/.
5. Cấu hình
Thứ tự tải: giá trị mặc định trong config.py, rồi config.yaml, rồi config.local.yaml (gộp sâu, tệp sau ghi đè). Công cụ calibrate và discover chỉ ghi config.local.yaml. Kiểm tra bằng pydantic v2 với extra='forbid'; lỗi thì in danh sách lỗi và thoát mã 2.
version: 1
mode: web                  # web | android_scrcpy | desktop_app | android_adb
run:
  start_armed: false
  dry_run: false
  log_dir: logs
  log_level: INFO          # DEBUG | INFO | WARNING | ERROR
  hotkeys: {toggle: f8, calibrate: f9, panic: f10}
audio:
  source: browser_tab      # browser_tab | loopback | wav; youtube-test ép browser_tab
  device: default          # default | chuỗi con (không phân biệt hoa thường) của tên loa
  wav_path: null
  wav_speed: 1.0           # 1.0 = thời gian thực; 0 = nhanh nhất có thể
  sample_rate: 16000
  chunk_ms: 40             # 20..200
  queue_max_chunks: 50     # 1..500
asr:
  engine: zipformer       # zipformer | vosk; mặc định Zipformer-VI local
  model_path: models/vosk-model-small-vn-0.4
  zipformer_model_dir: models/sherpa-onnx-zipformer-vi-30M-int8-2026-02-09
  vad_model_path: models/silero_vad.onnx
  words: false             # KaldiRecognizer.SetWords
  max_alternatives: 0
parser:
  shorthand: true          # 'một trăm hai' = 120; false = 102
  k_tokens: [k, ca, ka]
decision:
  min_value: 1000             # mặc định loại số dưới 1.000₫ khỏi candidate giá
  max_value: 2000000
  gate_mode: any_number    # any_number | anchored
  anchor_before: [giá, chỉ, chốt, lấy, còn, bán]
  anchor_after: [k, ca, ka, nghìn, ngàn, đồng]
  exclude_prev: [size, số, ngày, tháng, lúc, giờ, mã, cỡ]
  exclude_next: [cái, chiếc, người, bạn, kg, cm, mét, tuổi, giờ, phút, giây, ngày, tháng, tiếng, phần, lần]
  countdown_filter: true
  hold_complete_ms: 120
  hold_open_ms: 350
  cooldown_same_s: 10.0
  cooldown_any_s: 1.5
  max_sends_per_min: 10
output:
  template: '{value}'      # ví dụ '{value}k'
  send_mode: enter         # enter | click_button
sender:
  type: playwright         # playwright | desktop | adb
  playwright:
    user_data_dir: .pw-profile
    channel: chrome
    attach: launch         # launch | cdp
    cdp_url: http://127.0.0.1:9222
    live_url: ''
    url_pattern: '**/@*/live*'
    chat_input_selectors: []   # điền bằng pricetyper discover
    send_button_selector: ''
    focus_each_time: false
    verify_after_send: false
  desktop:
    chat_xy: null          # [x, y]; điền bằng pricetyper calibrate
    send_xy: null
    click_each_time: true
  adb:
    adb_path: adb
    serial: ''
    chat_xy: null
    send_xy: null
    send_keyevent: 66
Quy tắc kiểm tra (THIẾT KẾ):
Khóa
Điều kiện
audio.chunk_ms
20 ≤ x ≤ 200
audio.sample_rate
PHẢI bằng 16000
decision.min_value, decision.max_value
1 ≤ min ≤ max ≤ 999999999 (đơn vị đồng); mặc định min = 1000
decision.hold_*_ms
≥ 0
decision.cooldown_*_s
≥ 0
decision.max_sends_per_min
1 ≤ x ≤ 60
mode và sender.type
web đi với playwright hoặc desktop; android_scrcpy và desktop_app đi với desktop; android_adb đi với adb
trước khi vào ARMED
playwright: chat_input_selectors không rỗng; desktop: chat_xy khác null; adb: chat_xy khác null và thiết bị ở trạng thái device
output.template
PHẢI chứa {value}; kết quả sau khi thay chỉ gồm ký tự ASCII
6. Đặc tả module
6.1 Thu âm thanh PC: audio/loopback.py
Lớp LoopbackSource cài đặt AudioSource (§3.4).
Mục
Đặc tả
Nhãn
Thư viện
soundcard ≥ 0.4.6 (bản 0.4.6 phát hành 2026-04-12)
ĐÃ XÁC MINH trên PyPI
Chọn thiết bị
audio.device = default: dùng soundcard.default_speaker(). Giá trị khác: duyệt soundcard.all_speakers(), lấy loa đầu tiên có tên chứa chuỗi cấu hình (không phân biệt hoa thường). Mở loopback bằng soundcard.get_microphone(id=<tên loa>, include_loopback=True)
Chữ ký get_microphone(id, include_loopback=False): ĐÃ XÁC MINH trong mã nguồn
Mở luồng
mic.recorder(samplerate=16000, channels=1)
Chữ ký recorder(samplerate, channels=None, blocksize=None, exclusive_mode=False): ĐÃ XÁC MINH
Đọc
rec.record(numframes=sample_rate * chunk_ms // 1000): 640 mẫu với 40 ms; kết quả float32 dạng (N, 1)
THIẾT KẾ
Chuyển đổi
np.clip(x[:, 0], -1, 1) * 32767, ép np.int16, rồi .tobytes()
THIẾT KẾ
Dấu thời gian
t_audio_ns = time.perf_counter_ns() ngay sau khi record trả về
THIẾT KẾ
Lấy mẫu
Windows tự đổi sang 16000 Hz mono: mã soundcard 0.4.6 khởi tạo luồng WASAPI chia sẻ với các cờ resample và remix, cộng cờ loopback
ĐÃ XÁC MINH trong mediafoundation.py; chạy được trên mọi thiết bị: Không đủ dữ liệu để xác minh (U10)
Lỗi tốc độ mẫu
khởi tạo thất bại ở 16000 Hz thì ném ERR_AUDIO_RATE
THIẾT KẾ
Im lặng
RMS int16 dưới 10 liên tục 30 giây thì log audio_silent mức WARNING
THIẾT KẾ
WavSource (audio/wav_source.py): đọc WAV PCM 16-bit mono 16000 Hz bằng module wave, cắt khối chunk_ms, phát với tốc độ audio.wav_speed (1.0 = chờ đúng thời lượng khối; 0 = không chờ). t_audio_ns là thời điểm khối được trả ra. Sai định dạng WAV thì ném ERR_WAV_FORMAT.

6.1.1 Thu âm thanh video YouTube: audio/browser_tab.py và `browser_extension/`
• Extension dùng Chrome `tabCapture` theo user gesture để bắt audio của tab đang hoạt động; không dùng microphone hoặc system-wide loopback. Nguồn API: Chrome `tabCapture` reference (§19.1).
• Extension chuyển PCM mono int16 16 kHz qua WebSocket loopback `127.0.0.1`; Python BrowserTabSource đưa các chunk vào AudioSource pipeline. Queue có giới hạn; không ghi raw audio xuống đĩa.
• Extension định tuyến bản nghe tới audio output riêng để người dùng vẫn nghe video. ASR chỉ nhận PCM trước đường output, nên volume/mute thiết bị đầu ra không được dùng làm ngưỡng nhận dạng.
• Extension chỉ bắt tab người dùng bấm chọn và phải có nút Stop rõ ràng. Prototype chỉ cho phép YouTube; URL tab phải khớp allowlist `youtube.com`/`youtu.be` trước khi nhận stream.
• Nếu Chrome yêu cầu cấp quyền kết nối loopback/local network, người dùng chủ động cấp; lỗi kết nối phải hiện rõ trong GUI. Việc giao tiếp WebSocket phải được thử trên phiên bản Chrome thực tế, không suy đoán là tương thích mọi bản.
6.2 Thu âm thanh Android: scrcpy
Đã xác minh (tài liệu doc/audio.md của scrcpy, đọc 2026-10-19):
• Chuyển tiếp âm thanh hỗ trợ Android 11 trở lên và bật mặc định.
• Android 12 trở lên: chạy ngay. Android 11: màn hình PHẢI mở khóa khi khởi động scrcpy. Android 10 trở xuống: không thu được, scrcpy tự tắt âm thanh.
• Nguồn mặc định output: chuyển tiếp toàn bộ âm thanh đầu ra và tắt phát trên thiết bị. --audio-source=playback thu phần phát của ứng dụng (ứng dụng có thể từ chối bị thu).
• --require-audio buộc scrcpy báo lỗi nếu không thu được âm thanh; --no-audio tắt âm thanh; --audio-buffer=<ms> chỉnh bộ đệm.
Quy trình (THIẾT KẾ):
1. Bật USB debugging trên thiết bị. adb devices PHẢI hiện thiết bị ở trạng thái device.
2. Chạy scrcpy --require-audio. Cửa sổ scrcpy hiện trên PC; âm thanh phát ra loa PC.
3. Mở TikTok Live trên điện thoại. Giữ cửa sổ scrcpy hiển thị đầy đủ, không di chuyển, không thu nhỏ.
4. Đặt mode: android_scrcpy, audio.source: loopback, sender.type: desktop. Chạy pricetyper calibrate để lấy tọa độ ô chat (và nút gửi) trong cửa sổ scrcpy.
5. Tắt âm các ứng dụng khác trên PC: loopback thu toàn bộ âm thanh hệ thống.
Chưa xác minh: chế độ bàn phím mặc định của scrcpy có đưa được chữ số vào ô chat của app TikTok không (U4); phím ENTER có gửi tin trong app không (U3). Phương án thử khi chữ số không vào: --keyboard=uhid (tùy chọn này có trong README scrcpy, ĐÃ XÁC MINH sự tồn tại; hiệu quả với TikTok: U4).
6.3 Nhận dạng giọng nói: asr/factory.py, asr/zipformer_engine.py, asr/vosk_engine.py
Engine mặc định: Zipformer-VI 30M INT8 của sherpa-onnx chạy local, cùng Silero VAD để tìm vùng lời nói. Audio đầu vào là mono PCM float32 16 kHz cho VAD; mỗi cửa sổ 512 mẫu được đưa vào VAD. Ở chế độ thường và YouTube, khi đang nói engine có thể giải mã lại vùng hiện tại mỗi 400 ms sau ít nhất 450 ms speech; khi VAD chốt sau 250 ms im lặng, engine phát final. TikTok tắt các lần giải mã partial lặp để giảm tải ASR và ưu tiên xử lý audio liên tục. VAD đặt `max_speech_duration=12s`, nhưng đây chỉ là cơ chế tăng ngưỡng để khuyến khích tách đoạn, không phải giới hạn cứng; nếu speech vẫn mở, app flush/reset ở mốc 12s. Kết quả của lần cắt cưỡng bức chỉ là `partial` để xem trước, không thể tạo thao tác gửi; chỉ VAD final mới được gửi. Zipformer là offline model, nên partial là lần decode lại toàn bộ đoạn hiện tại; đây là điểm đánh đổi CPU/độ trễ và không phải streaming transducer. `asr.engine: vosk` giữ adapter cũ để benchmark hoặc chọn thủ công.

Chi tiết baseline Vosk:
Đã xác minh:
• vosk 0.3.45 phát hành 2022-12-14 và vẫn là bản mới nhất trên PyPI ngày 2026-10-19 (yêu cầu Python ≥ 3).
• KaldiRecognizer (kiểm bằng dir() trên bản 0.3.45) có: AcceptWaveform, PartialResult, Result, FinalResult, Reset, SetWords, SetPartialWords, SetMaxAlternatives, SetGrammar, SetSpkModel, SetNLSML, SrtResult. Không có SetEndpointerMode: Python không chỉnh được thời điểm chốt final; final đến theo cấu hình mặc định của model.
• Model tiếng Việt (alphacephei.com/vosk/models): vosk-model-small-vn-0.4 (32M, WER 15,70 trên Vivos, Apache 2.0, model nhẹ); vosk-model-vn-0.4 (78M, WER 15,70 trên Vivos, Apache 2.0, model lớn hơn dành cho máy chủ). Benchmark Vosk dùng model nhỏ làm baseline. So sánh độ trễ và độ chính xác thực tế giữa hai model: Không đủ dữ liệu để xác minh (U6).
Quy tắc (THIẾT KẾ):
1. Khởi tạo: SetLogLevel(-1); rec = KaldiRecognizer(Model(model_path), 16000); rec.SetWords(asr.words); rec.SetMaxAlternatives(asr.max_alternatives).
2. feed(pcm, t_audio_ns): nếu rec.AcceptWaveform(pcm) trả về true thì lấy json.loads(rec.Result())['text'] và phát AsrEvent('final', ...). Ngược lại lấy json.loads(rec.PartialResult())['partial'] và chỉ phát AsrEvent('partial', ...) khi chuỗi khác rỗng và khác lần phát trước.
3. final có text rỗng vẫn được phát để Decider đặt lại trạng thái phát ngôn.
4. Thiếu thư mục model: ERR_MODEL, thoát mã 4, in đường dẫn mong đợi.
5. Model xuất số bằng chữ hay bằng chữ số: Không đủ dữ liệu để xác minh (U5). Parser xử lý cả hai dạng.
6. Robustness và giới hạn (P0.1):
• Voice activity detection (VAD) chỉ xác định vùng có thể có lời nói; speech enhancement/noise suppression cố giảm nhiễu nhưng không đảm bảo loại nhạc hoặc tách nhiều người.
• Speaker diarization/overlap detection ước lượng ai nói khi nào và đánh dấu đoạn chồng lấp; diarization không tự tạo một luồng audio sạch cho từng người.
• Có thể benchmark nhánh tăng cường giọng nói, tách nguồn và ASR đa ngôn ngữ offline. Mọi nhánh phải so với raw PCM bằng exact-number accuracy và tỷ lệ số trích thừa; giá qua gate là chỉ số phụ. Không chọn model chỉ theo WER công bố trên bộ dữ liệu khác.
• ASR nhận dạng transcript, không dịch. Giọng được lồng tiếng/dịch sẵn trong video vẫn được xem là âm thanh nguồn và sẽ được chép lại theo ngôn ngữ phát ra.
• Khi overlap detector đánh dấu chồng lấp hoặc các hypothesis không đồng thuận, hiển thị “không chắc/không có số”; không suy đoán giá trị.

Thử nghiệm so sánh P0.1 (benchmark không thay engine của app):
• Cài `.[robust-asr]`, chạy `scripts/download_robust_asr_models.py`, rồi dùng `gui --youtube-test --asr-compare`. Cửa sổ so sánh cùng một đoạn tab PCM tối đa 20 giây qua hai nhánh audio gốc/DPDFNet và ba engine chính: Vosk, faster-whisper, Zipformer-VI 30M INT8. Có thêm một lane Vosk dùng ngữ pháp số hẹp (các cách đọc phổ biến 1–20/nghìn và dãy đếm liên tiếp) để thử nghiệm; lane này không tham gia đồng thuận, không thay engine mặc định và có thể bỏ sót mọi câu ngoài danh sách cụm.
• DPDFNet baseline chạy ở 16 kHz. Đây là speech enhancement/noise suppression, không phải tách nhạc hoặc tách người nói; chỉ chọn nhánh đã tăng cường nếu benchmark giá cho thấy nó tốt hơn.
• Người dùng nhập transcript đầy đủ để tính WER/CER và nhập nhãn số/giá chuẩn độc lập (các số cách nhau bằng dấu `;`, hoặc `không có` nếu đoạn không có số). Không suy ra nhãn chuẩn bằng parser đang được benchmark. Chế độ chấm `Số được nói` (mặc định) so sánh mọi giá trị số parser trích được và bỏ qua toàn bộ gate giá; chế độ `Giá qua bộ lọc` áp dụng gate giá đang cấu hình. Chọn điều kiện âm thanh (sạch, nhạc/ồn, chồng lấp) cùng vùng giọng (Bắc/Trung/Nam/chưa rõ). Kết quả có WER/CER, số/giá trích, exact, bỏ sót/thừa và thời gian xử lý. Benchmark trong RAM tính exact, bỏ sót, candidate thừa và P50/P95 theo nhóm vùng/điều kiện/phạm vi chấm cho các đoạn trong phiên; audio không lưu và benchmark mất khi đóng app. Chế độ chấm benchmark không làm thay đổi gate giá của ứng dụng.
• Preview nghiêm ngặt chỉ có candidate nếu cả sáu kết quả (ba model trên hai nhánh) đồng thuận. Đây là phép thử abstain sơ bộ, không phải confidence đã hiệu chuẩn. Nhãn chồng lấp do người thử chọn sẽ luôn abstain; chưa có overlap detector tự động. Đây là so sánh theo đoạn sau khi dừng capture, không phải pipeline realtime và vẫn ép `NullSender`.
• Whisper dùng model multilingual `small` mặc định, CPU/int8, `language="vi"`, `task="transcribe"`, cùng VAD tích hợp. Lần đầu có thể tải weights ASR/enhancement về máy; audio không được tải lên mạng.

Tham chiếu đã kiểm tra ngày 2026-10-19: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) là triển khai Whisper dùng CTranslate2, hỗ trợ compute type CPU/int8; [mã Whisper chính thức](https://github.com/openai/whisper/blob/main/whisper/transcribe.py) tách `transcribe` khỏi `translate`. [Zipformer-VI 30M INT8 của sherpa-onnx](https://k2-fsa.github.io/sherpa/onnx/pretrained_models/offline-transducer/zipformer-transducer-models.html) được công bố huấn luyện với khoảng 6.000 giờ tiếng Việt; đó không phải benchmark cho livestream. [DPDFNet trong sherpa-onnx](https://k2-fsa.github.io/sherpa/onnx/speech-enhancement/dpdfnet.html) hỗ trợ enhancement offline/streaming và model 16 kHz.
6.4 Bộ phân tích số tiếng Việt: parsing/vi_number.py
Mục tiêu: nhận chuỗi text từ ASR, trả về danh sách NumberSpan theo thứ tự xuất hiện. `value` là giá trị số thuần: số không có hậu tố giữ nguyên (`9` → `9`; `100.000` → `100000`); hậu tố `nghìn`, `ngàn` hoặc `k` nhân giá trị lên 1.000 (`300 nghìn` → `300000`). YouTube number mode hiển thị trực tiếp các giá trị này, không gắn đơn vị tiền và không áp gate giá. Khi dùng trong đường xử lý giá riêng, giá trị được hiểu là đồng theo quy ước hiện tại.
Chuẩn hóa: NFC, chữ thường; dấu chấm/dấu phẩy phân nhóm hàng nghìn trong chữ số Ả Rập được bỏ trước khi tách token; các dấu câu khác đổi thành khoảng trắng.
Từ vựng:
Nhóm
Từ
Giá trị hoặc vai trò
Chữ số đứng đầu (LEAD)
một, hai, ba, bốn, năm, sáu, bảy, bẩy, tám, chín
1 đến 9
Chữ số chỉ ở hàng đơn vị (ONES_ONLY)
mốt, tư, lăm, nhăm
1, 4, 5, 5
Số không
không
0; không đứng đầu
Mười
mười
10
Hàng chục
mươi, chục
nhân 10
Hàng trăm
trăm
nhân 100
Rưỡi
rưỡi
cộng 50 sau “trăm”
Số 0 ở hàng chục
linh, lẻ
đứng trước chữ số hàng đơn vị
Nghìn
nghìn, ngàn
đánh dấu unit và nhân giá trị lên 1.000
Hậu tố k
k, ca, ka (cấu hình parser.k_tokens)
đánh dấu unit và nhân giá trị lên 1.000; cách ASR ghi chữ “k” thực tế: U15
Chữ số Ả Rập
1 đến 12 chữ số, có thể nhóm ba chữ số bằng dấu chấm hoặc dấu phẩy, tùy chọn hậu tố k
giá trị là số nguyên; hậu tố k nhân 1.000
Quy tắc đọc. Tại token đầu của mỗi span lấy quy tắc đầu tiên khớp:
1. Chữ số Ả Rập: giá trị là số đó sau khi bỏ dấu nhóm hàng nghìn; hậu tố k dính liền đặt unit và nhân 1.000.
2. LEAD đứng trước “trăm”: giá trị = chữ số × 100 + phần sau “trăm”. Phần sau “trăm” lấy quy tắc đầu khớp: (a) “rưỡi” cộng 50; (b) “linh” hoặc “lẻ” cộng chữ số khác không đứng sau (“linh” đứng lẻ loi không bị tiêu thụ); (c) “mười” cộng 10, kèm chữ số hàng đơn vị nếu có; (d) LEAD từ 2 trở lên rồi “mươi” hoặc “chục” cộng chữ số × 10, kèm chữ số hàng đơn vị nếu có; (e) hai chữ số liền nhau (chữ số đầu là LEAD hoặc “không”) cộng chữ số đầu × 10 + chữ số sau; (f) một chữ số LEAD đứng một mình: shorthand = true cộng chữ số × 10 (`một trăm bốn` = 140), shorthand = false cộng chữ số (104); (g) `mốt` sau “trăm”: shorthand = true cộng 10 (`một trăm mốt` = 110), shorthand = false cộng 1 (101); (h) không có gì: cộng 0.
3. “mười” kèm chữ số hàng đơn vị tùy chọn: 10 đến 19.
4. LEAD từ 2 trở lên rồi “mươi” hoặc “chục”, kèm chữ số hàng đơn vị tùy chọn: 20 đến 99.
5. Chuỗi chữ số: LEAD đầu tiên, theo sau tối đa 3 chữ số bất kỳ (kể cả ONES_ONLY và “không”); dừng trước chữ số đứng ngay trước “trăm”, “mươi” hoặc “chục”. Từ 2 chữ số trở lên thì kind = digits.
6. “trăm” đứng đầu hoặc sau lời đệm không phải số được hiểu là 100 + phần sau theo quy tắc 2; ví dụ shorthand=true: `trăm bốn` = 140, `trăm mốt` = 110. Không áp dụng khi trước “trăm” là một token số hoặc từ “phần”, để không tách nhầm chuỗi số/“phần trăm”.
7. Sau lõi số: token thuộc k_tokens đặt unit và nhân giá trị 1.000; token “nghìn” hoặc “ngàn” cũng đặt unit và nhân giá trị 1.000. Nếu sau đơn vị là một số khác có đơn vị riêng (ví dụ `hai nghìn ba nghìn`), chốt span hiện tại và tiếp tục parse span kế tiếp. Nếu sau đơn vị là số không có đơn vị riêng (ví dụ `một nghìn hai trăm`), bỏ cả dải số ghép vì cách đọc hàng nghìn + phần dư chưa được hỗ trợ.
8. Chuỗi chữ số cho phép đọc lần lượt như digit-by-digit: `một bốn không` = 140, `một một không` = 110. Các cách đọc rút gọn phụ thuộc vùng/ngữ cảnh; benchmark phải nhập nhãn số/giá chuẩn độc lập, không suy ra nhãn bằng parser.
9. Riêng YouTube number preview, `parse_all(..., split_count_sequence=True)` tách dãy đếm tăng dần bắt đầu bằng `một` thành từng span: `một hai ba bốn năm sáu bảy tám chín` → `[1, 2, 3, 4, 5, 6, 7, 8, 9]`. Dãy phải có ít nhất hai từ liên tiếp đúng thứ tự và không được nối tiếp bởi một từ/số khác; nếu không khớp, dùng quy tắc mặc định. Tùy chọn này không áp dụng cho price parser, do đó các ví dụ digit-by-digit tại quy tắc 8 vẫn giữ nguyên.
Trường của NumberSpan:
Trường
Ý nghĩa
value
số nguyên sau chuẩn hóa đơn vị; chỉ được diễn giải là đồng trong đường xử lý giá riêng
start, end
chỉ số token, nửa mở từ start đến end
kind
positional, digits hoặc arabic
unit
có hậu tố k, ca, ka, nghìn hoặc ngàn
closed
unit đúng, hoặc còn token đứng sau span
extendable
chỉ xét khi closed sai: thêm một từ số có thể kéo dài span. Kiểm bằng cách thử nối lần lượt chín, mươi, trăm, mười, rưỡi, linh; chuỗi chữ số từ 3 chữ số trở lên và số Ả Rập coi như hoàn chỉnh
digits
chuỗi chữ số khi kind = digits
Mã tham chiếu src/pricetyper/parsing/vi_number.py (ĐÃ KIỂM THỬ: 53/53 ca bên dưới qua, pytest trên Python 3.14.5):
from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass

LEAD = {'một': 1, 'hai': 2, 'ba': 3, 'bốn': 4, 'năm': 5, 'sáu': 6, 'bảy': 7, 'bẩy': 7, 'tám': 8, 'chín': 9}
ONES_ONLY = {'mốt': 1, 'tư': 4, 'lăm': 5, 'nhăm': 5}
DIGIT_ANY = {**LEAD, **ONES_ONLY, 'không': 0}
TEEN, HUND, HALF = 'mười', 'trăm', 'rưỡi'
TENS = frozenset({'mươi', 'chục'})
ZCONN = frozenset({'linh', 'lẻ'})
THOUSAND = frozenset({'nghìn', 'ngàn'})
DEFAULT_K = frozenset({'k', 'ca', 'ka'})
NUMWORDS = frozenset(DIGIT_ANY) | {TEEN, HUND, HALF} | TENS | ZCONN | THOUSAND
ARABIC = re.compile(r'^([0-9]{1,12})(k?)$')
GROUPED_ARABIC = re.compile(r'(?<!\d)(\d{1,3}(?:[.,]\d{3})+)(k?)(?!\d)')
MAX_DIGITS = 4
DIGITS_EXTENDABLE_BELOW = 3   # chuỗi >= 3 chữ số coi là hoàn chỉnh
PROBES = ('chín', 'mươi', 'trăm', 'mười', 'rưỡi', 'linh')


@dataclass(frozen=True)
class NumberSpan:
    value: int
    start: int          # chỉ số token đầu
    end: int            # chỉ số token cuối + 1
    kind: str           # 'positional' | 'digits' | 'arabic'
    unit: bool          # có hậu tố k/ca/ka/nghìn/ngàn
    closed: bool        # unit hoặc có token đứng sau span
    extendable: bool    # chỉ có nghĩa khi closed == False
    digits: str         # chuỗi chữ số khi kind == 'digits'


def tokenize(text: str) -> list[str]:
    t = unicodedata.normalize('NFC', text.lower())
    t = GROUPED_ARABIC.sub(lambda m: m.group(1).replace('.', '').replace(',', '') + m.group(2), t)
    return ''.join(c if (c.isalnum() or c.isspace()) else ' ' for c in t).split()


def _is_num(tok: str) -> bool:
    return tok in NUMWORDS or bool(ARABIC.match(tok))


def _d(t, k):
    return DIGIT_ANY[t[k]] if k < len(t) and t[k] in DIGIT_ANY else None


def _after_hundred(t, j, shorthand):
    n = len(t)
    if j >= n:
        return 0, j
    w = t[j]
    if w == HALF:
        return 50, j + 1
    if w == 'mốt':
        return (10 if shorthand else 1), j + 1
    if w in ZCONN:
        d = _d(t, j + 1)
        return (d, j + 2) if d else (0, j)          # 'linh' lẻ loi: không tiêu thụ
    if w == TEEN:
        v, k = 10, j + 1
        d = _d(t, k)
        if d:
            v, k = v + d, k + 1
        return v, k
    if w in LEAD and LEAD[w] >= 2 and j + 1 < n and t[j + 1] in TENS:
        v, k = LEAD[w] * 10, j + 2
        d = _d(t, k)
        if d:
            v, k = v + d, k + 1
        return v, k
    if w in LEAD or w == 'không':
        d1, d2 = DIGIT_ANY[w], _d(t, j + 1)
        if d2 is not None:
            return d1 * 10 + d2, j + 2               # hai chữ số liền nhau
        if w in LEAD:
            return (d1 * 10 if shorthand else d1), j + 1
    return 0, j


def _read_core(t, i, shorthand):
    n, a = len(t), t[i]
    m = ARABIC.match(a)
    if m:
        value = int(m.group(1))
        has_k = bool(m.group(2))
        return value * 1000 if has_k else value, i + 1, 'arabic', m.group(1), has_k
    if a in LEAD and i + 1 < n and t[i + 1] == HUND:
        v, j = _after_hundred(t, i + 2, shorthand)
        return LEAD[a] * 100 + v, j, 'positional', '', False
    if a == HUND and (i == 0 or (not _is_num(t[i - 1]) and t[i - 1] != 'phần')):
        v, j = _after_hundred(t, i + 1, shorthand)
        return 100 + v, j, 'positional', '', False
    if a == TEEN:
        v, j = 10, i + 1
        d = _d(t, j)
        if d:
            v, j = v + d, j + 1
        return v, j, 'positional', '', False
    if a in LEAD and LEAD[a] >= 2 and i + 1 < n and t[i + 1] in TENS:
        v, j = LEAD[a] * 10, i + 2
        d = _d(t, j)
        if d:
            v, j = v + d, j + 1
        return v, j, 'positional', '', False
    if a in LEAD:
        ds, j = [LEAD[a]], i + 1
        while j < n and t[j] in DIGIT_ANY and len(ds) < MAX_DIGITS:
            if j + 1 < n and (t[j + 1] == HUND or t[j + 1] in TENS):
                break
            ds.append(DIGIT_ANY[t[j]])
            j += 1
        s = ''.join(map(str, ds))
        return int(s), j, ('digits' if len(ds) > 1 else 'positional'), (s if len(ds) > 1 else ''), False
    return None


def _extendable(tokens, shorthand, kind, digits):
    if kind == 'arabic':
        return False
    if kind == 'digits' and len(digits) >= DIGITS_EXTENDABLE_BELOW:
        return False
    for w in PROBES:
        r = _read_core(tokens + [w], 0, shorthand)
        if r and r[1] == len(tokens) + 1:
            return True
    return False


def _read_count_sequence(tokens, index, k_tokens):
    if index >= len(tokens) or tokens[index] != 'một':
        return None
    spans, cursor, expected = [], index, 1
    while cursor < len(tokens) and LEAD.get(tokens[cursor]) == expected:
        spans.append(NumberSpan(expected, cursor, cursor + 1, 'positional', False, True, False, ''))
        cursor, expected = cursor + 1, expected + 1
    if len(spans) < 2 or (cursor < len(tokens) and (_is_num(tokens[cursor]) or tokens[cursor] in k_tokens)):
        return None
    return spans, cursor


def parse_all(text: str, shorthand: bool = True, k_tokens=DEFAULT_K, *, split_count_sequence: bool = False) -> list[NumberSpan]:
    t = tokenize(text)
    n, i, out = len(t), 0, []
    k_tokens = frozenset(k_tokens)
    while i < n:
        if split_count_sequence:
            sequence = _read_count_sequence(t, i, k_tokens)
            if sequence is not None:
                spans, i = sequence
                out.extend(spans)
                continue
        r = _read_core(t, i, shorthand)
        if r is None:
            i += 1
            continue
        value, j, kind, digits, unit = r
        if j < n and t[j] in k_tokens:
            value, unit, j = value * 1000, True, j + 1
        elif j < n and t[j] in THOUSAND:
            unit, j = True, j + 1
            if j < n and _is_num(t[j]):
                following = _read_core(t, j, shorthand)
                has_separate_unit = False
                if following:
                    following_end = following[1]
                    has_separate_unit = following[4] or (
                        following_end < n and t[following_end] in (THOUSAND | k_tokens)
                    )
                if not has_separate_unit:             # 'nghìn' + số dư không unit: chưa hỗ trợ
                    while j < n and _is_num(t[j]):
                        j += 1
                    i = j
                    continue
            value *= 1000
        closed = unit or j < n
        ext = (not closed) and _extendable(t[i:j], shorthand, kind, digits)
        out.append(NumberSpan(value, i, j, kind, unit, closed, ext, digits))
        i = j
    return out
Bộ test tests/test_vi_number.py (điều kiện qua tối thiểu; không đổi kỳ vọng nếu chưa đổi đặc tả):
import pytest
from pricetyper.parsing.vi_number import parse_all

F, T = False, True
# (văn bản, shorthand, [(value, unit, closed, extendable), ...])
CASES = [
    ('một trăm chín mươi chín', T, [(199, F, F, F)]),
    ('một trăm chín mươi chín nha', T, [(199, F, T, F)]),
    ('Một trăm chín mươi chín, nha!', T, [(199, F, T, F)]),
    ('chín chín ca', T, [(99000, T, T, F)]),
    ('chín mươi chín k', T, [(99000, T, T, F)]),
    ('hai trăm', T, [(200, F, F, T)]),
    ('hai trăm rưỡi', T, [(250, F, F, F)]),
    ('ba trăm năm', T, [(350, F, F, T)]),
    ('ba trăm năm', F, [(305, F, F, T)]),
    ('một trăm hai', T, [(120, F, F, T)]),
    ('một trăm hai', F, [(102, F, F, T)]),
    ('một trăm bốn', T, [(140, F, F, T)]),
    ('một bốn không', T, [(140, F, F, F)]),
    ('trăm bốn', T, [(140, F, F, T)]),
    ('một một không', T, [(110, F, F, F)]),
    ('trăm mốt', T, [(110, F, F, F)]),
    ('một trăm mốt', T, [(110, F, F, F)]),
    ('một trăm mốt', F, [(101, F, F, F)]),
    ('một trăm linh năm', T, [(105, F, F, F)]),
    ('một trăm lẻ năm', T, [(105, F, F, F)]),
    ('một trăm không năm', T, [(105, F, F, F)]),
    ('hai trăm linh', T, [(200, F, T, F)]),
    ('hai mươi', T, [(20, F, F, T)]),
    ('hai mươi lăm', T, [(25, F, F, F)]),
    ('hai lăm', T, [(25, F, F, T)]),
    ('hai mốt', T, [(21, F, F, T)]),
    ('mười lăm', T, [(15, F, F, F)]),
    ('mười', T, [(10, F, F, T)]),
    ('một hai chín', T, [(129, F, F, F)]),
    ('chín chín chín', T, [(999, F, F, F)]),
    ('199', T, [(199, F, F, F)]),
    ('199k', T, [(199000, T, T, F)]),
    ('199 k', T, [(199000, T, T, F)]),
    ('hai trăm nghìn', T, [(200000, T, T, F)]),
    ('hai nghìn ba nghìn', T, [(2000, T, T, F), (3000, T, T, F)]),
    ('hai nghìn, 3 nghìn', T, [(2000, T, T, F), (3000, T, T, F)]),
    ('một', T, [(1, F, F, T)]),
    ('100.000', T, [(100000, F, F, F)]),
    ('100.000 nghìn', T, [(100000000, T, T, F)]),
    ('300 nghìn', T, [(300000, T, T, F)]),
    ('một nghìn hai trăm', T, []),
    ('áo này giá một trăm chín mươi chín nghìn nha mọi người', T, [(199000, T, T, F)]),
    ('hai trăm năm mươi', T, [(250, F, F, T)]),
    ('một trăm mười lăm', T, [(115, F, F, F)]),
    ('một trăm hai mốt', T, [(121, F, F, F)]),
    ('hai trăm ba mươi lăm', T, [(235, F, F, F)]),
    ('một trăm hai ba', T, [(123, F, F, F)]),
    ('năm chục', T, [(50, F, F, T)]),
    ('một trăm phần trăm cotton', T, [(100, F, T, F)]),
    ('không trăm', T, []),
    ('áo này hai trăm rưỡi quần kia ba trăm', T, [(250, F, T, F), (300, F, F, T)]),
]


@pytest.mark.parametrize('text,shorthand,expected', CASES)
def test_parse(text, shorthand, expected):
    got = [(s.value, s.unit, s.closed, s.extendable) for s in parse_all(text, shorthand)]
    assert got == expected


def test_number_preview_splits_an_explicit_ascending_count_sequence():
    text = 'số chín và một hai ba bốn năm sáu bảy tám chín'
    assert [s.value for s in parse_all(text, split_count_sequence=True)] == [9, 1, 2, 3, 4, 5, 6, 7, 8, 9]
6.5 Bộ lọc (gate) và bộ quyết định (decider)
Hai mô-đun: parsing/gate.py (lọc span) và decision/decider.py (quyết định nhả lệnh gửi). GateCfg và DeciderCfg ánh xạ 1-1 sang khóa decision.* và parser.shorthand ở §5; mô hình pydantic DecisionConfig PHẢI cung cấp thuộc tính cùng tên. Mã tham chiếu tính thời gian bằng mili giây số nguyên; pipeline truyền t_ms = (t_ns - t0_ns) // 1_000_000.
Quy tắc gate (span bị loại ngay khi vi phạm một quy tắc):
1. value nằm ngoài khoảng từ min_value đến max_value. Mặc định min_value = 1000₫ để loại các số đếm nhỏ khỏi candidate giá; cấu hình vẫn có thể đổi ngưỡng này.
2. Token đứng ngay trước span thuộc exclude_prev, hoặc token đứng ngay sau span thuộc exclude_next.
3. countdown_filter bật, kind = digits và các chữ số tạo dãy tăng đều hoặc giảm đều 1 với độ dài từ 3 (ví dụ “ba hai một”, “một hai ba”).
Khi gate_mode = anchored (THIẾT KẾ; chưa có trong mã tham chiếu, test do agent viết) span chỉ qua gate nếu thỏa một trong ba điều kiện: unit đúng; một trong 2 token đứng ngay trước span thuộc anchor_before; token đứng ngay sau span thuộc anchor_after.
Quy tắc decider:
1. Price scope: ứng viên là span cuối cùng qua gate. Number scope (YouTube preview và TikTok Web) bỏ qua gate, tách dãy đếm tăng tường minh thành từng span và chọn số cuối cùng trong text của sự kiện; các span trước được coi là đã xử lý ở sự kiện trước (THIẾT KẾ).
2. Thời gian giữ: closed hoặc sự kiện final thì 0; extendable thì hold_open_ms; còn lại hold_complete_ms.
3. Lệnh đang chờ (pending) được đặt lại mỗi khi text hoặc value đổi; nhả khi now - t_change >= hold. Việc nhả được kiểm ở mỗi sự kiện và ở mỗi tick 10 ms.
4. Sau khi nhả (gửi hoặc bỏ qua), value vào handled đến khi có sự kiện final; trong thời gian đó cùng value không được xét lại.
5. Điều kiện gửi, kiểm theo thứ tự: cooldown_same (cùng giá trị trong cooldown_same_s), cooldown_any (bất kỳ lệnh gửi nào trong cooldown_any_s), rate_limit (đã đủ max_sends_per_min lệnh trong 60 giây), disarmed; qua hết thì send.
6. t_audio của quyết định lấy từ sự kiện làm đổi text lần cuối trước khi nhả.
7. Mỗi lần nhả tạo đúng 1 Decision và đúng 1 dòng log decision (§6.8).
Mã tham chiếu src/pricetyper/parsing/gate.py:
from __future__ import annotations
from dataclasses import dataclass
from pricetyper.parsing.vi_number import NumberSpan, tokenize


@dataclass
class GateCfg:
    min_value: int = 1000
    max_value: int = 2_000_000
    exclude_prev: tuple = ('size', 'số', 'ngày', 'tháng', 'lúc', 'giờ', 'mã', 'cỡ')
    exclude_next: tuple = ('cái', 'chiếc', 'người', 'bạn', 'kg', 'cm', 'mét', 'tuổi',
                           'giờ', 'phút', 'giây', 'ngày', 'tháng', 'tiếng', 'phần', 'lần')
    countdown_filter: bool = True


def monotonic_step1(digits: str) -> bool:
    if len(digits) < 3:
        return False
    d = [int(c) for c in digits]
    diffs = {b - a for a, b in zip(d, d[1:])}
    return diffs == {1} or diffs == {-1}


def gate(text: str, spans: list[NumberSpan], cfg: GateCfg) -> list[NumberSpan]:
    t, out = tokenize(text), []
    for s in spans:
        if not (cfg.min_value <= s.value <= cfg.max_value):
            continue
        prev = t[s.start - 1] if s.start > 0 else None
        nxt = t[s.end] if s.end < len(t) else None
        if prev in cfg.exclude_prev or nxt in cfg.exclude_next:
            continue
        if cfg.countdown_filter and s.kind == 'digits' and monotonic_step1(s.digits):
            continue
        out.append(s)
    return out
Mã tham chiếu src/pricetyper/decision/decider.py:
from __future__ import annotations
from dataclasses import dataclass
from pricetyper.parsing.vi_number import parse_all
from pricetyper.parsing.gate import GateCfg, gate


@dataclass
class DeciderCfg:
    hold_complete_ms: int = 120
    hold_open_ms: int = 350
    cooldown_same_s: float = 10.0
    cooldown_any_s: float = 1.5
    max_per_min: int = 10
    shorthand: bool = True


@dataclass
class Decision:
    t_ms: int
    value: int
    action: str         # 'send' | 'skip'
    reason: str         # 'ok' | 'cooldown_same' | 'cooldown_any' | 'rate_limit' | 'disarmed'
    t_audio: int = 0


@dataclass
class Pending:
    value: int
    text: str
    t_change: int
    hold: int
    t_audio: int


class Decider:
    def __init__(self, gate_cfg: GateCfg, cfg: DeciderCfg, armed: bool = False):
        self.gate_cfg, self.cfg, self.armed = gate_cfg, cfg, armed
        self.pending: Pending | None = None
        self.handled: set[int] = set()
        self.sent: list[tuple[int, int]] = []        # (t_ms, value)

    def _decide(self, p: Pending, t_ms: int) -> Decision:
        c, v = self.cfg, p.value

        def d(action: str, reason: str) -> Decision:
            return Decision(t_ms, v, action, reason, p.t_audio)

        if any(sv == v and t_ms - st < c.cooldown_same_s * 1000 for st, sv in self.sent):
            return d('skip', 'cooldown_same')
        if self.sent and t_ms - self.sent[-1][0] < c.cooldown_any_s * 1000:
            return d('skip', 'cooldown_any')
        if sum(1 for st, _ in self.sent if t_ms - st < 60000) >= c.max_per_min:
            return d('skip', 'rate_limit')
        if not self.armed:
            return d('skip', 'disarmed')
        self.sent.append((t_ms, v))
        return d('send', 'ok')

    def _release(self, t_ms: int) -> list[Decision]:
        p = self.pending
        if p and t_ms - p.t_change >= p.hold:
            self.pending = None
            self.handled.add(p.value)
            return [self._decide(p, t_ms)]
        return []

    def on_event(self, kind: str, text: str, t_ms: int, t_audio: int = 0) -> list[Decision]:
        c, out = self.cfg, []
        spans = gate(text, parse_all(text, c.shorthand), self.gate_cfg)
        cand = spans[-1] if spans else None
        final = kind == 'final'
        if cand is None or cand.value in self.handled:
            self.pending = None
        else:
            hold = 0 if (cand.closed or final) else (c.hold_open_ms if cand.extendable else c.hold_complete_ms)
            if self.pending is None or self.pending.value != cand.value or self.pending.text != text:
                self.pending = Pending(cand.value, text, t_ms, hold, t_audio)
            else:
                self.pending.hold = hold
            out += self._release(t_ms)
        if final:
            self.handled.clear()
            self.pending = None
        return out

    def tick(self, t_ms: int) -> list[Decision]:
        return self._release(t_ms)
Bảng vết (ĐÃ KIỂM THỬ: tick 10 ms, cấu hình mặc định, armed = true). Chuỗi sự kiện đầu vào:
t (ms)
kind
text
0
partial
áo này giá một
300
partial
áo này giá một trăm
500
partial
áo này giá một trăm chín
700
partial
áo này giá một trăm chín mươi
900
partial
áo này giá một trăm chín mươi chín
1000
partial
áo này giá một trăm chín mươi chín nha
1400
final
áo này giá một trăm chín mươi chín nha
3000
partial
quần này hai trăm rưỡi
4200
partial
size ba tám
5000
partial
ba hai một chốt
6000
partial
chín chín ca
6200
partial
chín chín ca nha ba trăm
6600
final
chín chín ca nha ba trăm
7200
partial
chín chín ca
Đầu ra bắt buộc (đúng 5 dòng):
t (ms)
Giá trị
Hành động
Lý do
1000
199
send
ok
3120
250
send
ok
6000
99
send
ok
6550
300
skip
cooldown_any
7200
99
skip
cooldown_same
Diễn giải: “một trăm” lúc 300 ms không được gửi vì text đổi lúc 500 ms trước khi đủ 350 ms giữ. 199 được nhả lúc 1000 ms nhờ từ “nha” đóng span (giữ 0), sớm hơn mốc 1020 ms nếu chỉ chờ hold_complete_ms. “size ba tám” và “ba hai một chốt” không tạo quyết định vì gate loại. Sự kiện final lúc 1400 ms không tạo thêm quyết định vì 199 đã nằm trong handled.
Bộ test tests/test_gate.py (ĐÃ KIỂM THỬ: 17/17 qua):
import pytest
from pricetyper.parsing.gate import GateCfg, gate
from pricetyper.parsing.vi_number import parse_all

VECTORS = [
    ('size ba tám', []),
    ('ba hai một chốt', []),
    ('một hai ba chốt', []),
    ('bốn năm sáu', []),
    ('ba hai chín', [329]),
    ('lúc hai mươi giờ', []),
    ('một trăm phần trăm cotton', []),
    ('hai cái một trăm chín mươi chín', [199]),
    ('chín chín ca', [99000]),
    ('một nghìn hai trăm', []),
    ('áo hai trăm rưỡi quần ba trăm', [250, 300]),
    ('còn năm cái', []),
    ('giá mười', [10]),
    ('giá chín', [9]),
    ('hai nghìn một trăm', []),
]


@pytest.mark.parametrize('text,expected', VECTORS)
def test_gate(text, expected):
    cfg = GateCfg(min_value=1)   # vector parser/gate tổng quát, không dùng ngưỡng giá mặc định
    assert [s.value for s in gate(text, parse_all(text), cfg)] == expected

def test_default_minimum_filters_values_below_1000_vnd():
    cfg = GateCfg()
    assert gate('giá 999', parse_all('giá 999'), cfg) == []
    assert [s.value for s in gate('giá 1.000', parse_all('giá 1.000'), cfg)] == [1000]

def test_configured_minimum_can_allow_lower_prices():
    cfg = GateCfg(min_value=1)
    assert [s.value for s in gate('giá 999', parse_all('giá 999'), cfg)] == [999]
Bộ test tests/test_decider.py (ĐÃ KIỂM THỬ: 2/2 qua):
from pricetyper.decision.decider import Decider, DeciderCfg
from pricetyper.parsing.gate import GateCfg

EVENTS = [
    (0, 'partial', 'áo này giá một'),
    (300, 'partial', 'áo này giá một trăm'),
    (500, 'partial', 'áo này giá một trăm chín'),
    (700, 'partial', 'áo này giá một trăm chín mươi'),
    (900, 'partial', 'áo này giá một trăm chín mươi chín'),
    (1000, 'partial', 'áo này giá một trăm chín mươi chín nha'),
    (1400, 'final', 'áo này giá một trăm chín mươi chín nha'),
    (3000, 'partial', 'quần này hai trăm rưỡi'),
    (4200, 'partial', 'size ba tám'),
    (5000, 'partial', 'ba hai một chốt'),
    (6000, 'partial', 'chín chín ca'),
    (6200, 'partial', 'chín chín ca nha ba trăm'),
    (6600, 'final', 'chín chín ca nha ba trăm'),
    (7200, 'partial', 'chín chín ca'),
]
EXPECTED = [
    (1000, 199, 'send', 'ok'),
    (3120, 250, 'send', 'ok'),
    (6000, 99000, 'send', 'ok'),
    (6550, 300, 'skip', 'cooldown_any'),
    (7200, 99000, 'skip', 'cooldown_same'),
]


def run(armed=True):
    d = Decider(GateCfg(min_value=1), DeciderCfg(), armed=armed)
    ev = {t: (k, x) for t, k, x in EVENTS}
    got = []
    for t in range(0, 8000, 10):
        out = d.on_event(ev[t][0], ev[t][1], t) if t in ev else []
        out += d.tick(t)
        got += [(x.t_ms, x.value, x.action, x.reason) for x in out]
    return got


def test_trace():
    assert run(armed=True) == EXPECTED


def test_disarmed_never_sends():
    assert all(a == 'skip' for _, _, a, _ in run(armed=False))
6.6 Sender
Quy tắc chung (THIẾT KẾ): text chỉ gồm ký tự ASCII; mỗi send ghi t_start_ns và t_end_ns bằng time.perf_counter_ns(); không thử lại khi lỗi (tránh gửi trùng); NullSender ghi nhận lệnh, trả SendResult(ok=True) ngay, dùng cho dry_run và đo độ trễ.
6.6.1 PlaywrightSender
Hạng mục
Đặc tả
Nhãn
Thư viện
playwright Python, API đồng bộ playwright.sync_api; bản dùng để kiểm tra API: 1.56.0
Chữ ký đã kiểm bằng introspection trên 1.56.0 (ĐÃ XÁC MINH): BrowserType.launch_persistent_context có tham số user_data_dir, channel, executable_path, args, ignore_default_args, headless, slow_mo, viewport, no_viewport; BrowserType.connect_over_cdp(endpoint_url, timeout, slow_mo); Keyboard có insert_text, press, type, down, up; Locator có fill, focus, press, click, evaluate, count, is_visible; Page có locator, get_by_role, get_by_placeholder, expose_function, wait_for_selector
prepare() khi attach = launch
Trong thread sender: sync_playwright().start(); p.chromium.launch_persistent_context(user_data_dir=<cấu hình>, channel=<cấu hình>, headless=False, no_viewport=True)
THIẾT KẾ
prepare() khi attach = cdp
p.chromium.connect_over_cdp(cdp_url); dùng browser.contexts[0]
THIẾT KẾ; điều kiện của Chrome: U12
Tìm trang
Duyệt context.pages, chọn trang đầu có URL khớp url_pattern. Không có và live_url không rỗng: context.new_page() rồi goto(live_url). Không có cả hai: chờ tối đa 120 giây để người dùng tự mở livestream
THIẾT KẾ; dạng URL: U2
Đăng nhập
Người dùng tự đăng nhập trong cửa sổ trình duyệt. Tool không đọc, không lưu thông tin đăng nhập; phiên nằm trong user_data_dir
THIẾT KẾ
Tìm ô chat
Thử lần lượt từng selector trong chat_input_selectors bằng page.wait_for_selector(sel, state='visible', timeout=30000). Selector đầu tiên thành công được giữ làm locator; không selector nào thành công thì ném SenderPrepareError
THIẾT KẾ; selector thật: U1
send(text)
(1) nếu focus_each_time hoặc chưa focus: locator.focus(); (2) page.keyboard.insert_text(text); (3) send_mode = enter: page.keyboard.press('Enter'); click_button: page.locator(send_button_selector).click(). t_start_ns ghi trước (1), t_end_ns ghi sau (3)
THIẾT KẾ
Kiểm tra sau gửi
Khi verify_after_send: sau 50 ms đọc locator.evaluate('e => (e.value !== undefined ? e.value : e.innerText)'); còn nội dung thì log send_unverified mức WARNING
THIẾT KẾ
6.6.2 DesktopSender
Hạng mục
Đặc tả
Nhãn
prepare()
pyautogui.PAUSE = 0; pyautogui.FAILSAFE = True; yêu cầu chat_xy khác null
PAUSE = 0.1 và FAILSAFE = True là mặc định trong pyautogui 0.9.54: ĐÃ XÁC MINH
send(text)
text.isascii() PHẢI đúng. (1) nếu click_each_time: pyautogui.click(x, y); (2) pyautogui.typewrite(text, interval=0); (3) send_mode = enter: pyautogui.press('enter'); click_button: pyautogui.click(send_x, send_y)
THIẾT KẾ
Hệ tọa độ
calibrate dùng pyautogui.position(), cùng hệ tọa độ với pyautogui.click. Mô-đun Windows của pyautogui gọi SetProcessDPIAware() khi nạp, nên tọa độ là điểm ảnh vật lý
ĐÃ XÁC MINH trong _pyautogui_win.py
FAILSAFE
Đưa chuột vào điểm failsafe (mặc định gồm góc trên-trái (0, 0)) làm pyautogui ném FailSafeException. Sender bắt lỗi, controller chuyển về LISTENING và log failsafe
FAILSAFE_POINTS chứa (0, 0): ĐÃ XÁC MINH
Cửa sổ đích
Người dùng giữ cửa sổ trình duyệt hoặc scrcpy ở tiền cảnh, không di chuyển, không đổi kích thước sau khi calibrate. Tool không kiểm tra
THIẾT KẾ
6.6.3 AdbSender (dự phòng cho Android)
Hạng mục
Đặc tả
Nhãn
prepare()
Chạy <adb_path> -s <serial> get-state; kết quả PHẢI là device. serial rỗng: dùng thiết bị duy nhất từ adb devices; nhiều thiết bị thì lỗi ERR_ADB_SERIAL
THIẾT KẾ
send(text)
Một lệnh subprocess.run([adb_path, '-s', serial, 'shell', 'input tap X Y; input text <số>; input keyevent <send_keyevent>'], timeout=3). Khi send_mode = click_button thay phần cuối bằng input tap SX SY. text chỉ gồm chữ số. Mã phím 66 là ENTER
THIẾT KẾ; độ trễ: U14
Tọa độ
chat_xy và send_xy là điểm ảnh của màn hình thiết bị. Cách lấy: tính năng Pointer location trong Tùy chọn nhà phát triển của Android (tên mục theo từng hãng: Không đủ dữ liệu để xác minh)
THIẾT KẾ
6.6.4 Trang giả tests/fixtures/fake_live.html
Trang cục bộ dùng để kiểm thử sender mà không chạm vào TikTok. Selector dùng trong test: [data-testid='chat-input']. Trang không thuộc dữ liệu đã xác minh về TikTok (THIẾT KẾ).
<!doctype html>
<meta charset='utf-8'>
<title>fake live</title>
<div id='chat-input' data-testid='chat-input' contenteditable='true'></div>
<button id='send'>Gửi</button>
<ul id='messages'></ul>
<script>
window.__sent = [];
const box = document.getElementById('chat-input');
function send() {
  const t = box.innerText.trim();
  if (!t) return;
  window.__sent.push(t);
  const li = document.createElement('li');
  li.textContent = t;
  document.getElementById('messages').appendChild(li);
  box.innerText = '';
}
box.addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); send(); }
});
document.getElementById('send').addEventListener('click', send);
</script>
6.7 Controller, hotkey và công cụ
6.7.1 controller.py
• API: state (LISTENING, ARMED hoặc STOPPED), toggle(), arm(), disarm(), panic(), subscribe(callback). Thread-safe bằng threading.Lock; armed là threading.Event.
• arm() chỉ thành công khi sender.prepare() đã thành công và các điều kiện “trước khi vào ARMED” ở §5 thỏa. Ngược lại giữ LISTENING và báo lỗi qua subscribe.
• panic(): (1) armed.clear(); (2) đặt stop_event; (3) sender.close() với giới hạn 1 giây; (4) ghi log state = STOPPED; (5) os._exit(130).
• Mỗi lần đổi trạng thái ghi một dòng log state.
6.7.2 ui/hotkeys.py
• Thư viện keyboard 0.13.5, phát hành 2020-03-23 và vẫn là bản mới nhất trên PyPI ngày 2026-10-19. README nêu hỗ trợ Windows và Linux (Linux cần sudo), macOS ở mức thử nghiệm (ĐÃ XÁC MINH).
• Đăng ký bằng keyboard.add_hotkey(key, callback) cho hotkeys.toggle và hotkeys.panic. Callback chỉ gọi controller.
• Có cần quyền quản trị trên Windows không: Không đủ dữ liệu để xác minh (U9).
• Xung đột phím với ứng dụng khác: người dùng đổi trong run.hotkeys.
6.7.3 Công cụ dòng lệnh
Lệnh
Đặc tả
record
Thu loopback ra WAV 16 kHz mono bằng LoopbackSource, ghi bằng module wave, in thời lượng thực tế.
calibrate
In hướng dẫn “Di chuột tới đích rồi nhấn F9”; keyboard.wait(hotkeys.calibrate); x, y = pyautogui.position(); in tọa độ và ghi sender.desktop.chat_xy (hoặc send_xy với --target send) vào config.local.yaml. Không chạy --target send thì dùng send_mode: enter.
discover
Mở Playwright như prepare() (không cần selector). Chờ người dùng đăng nhập, vào livestream và nhấn Enter ở console. Chạy JavaScript trên trang để liệt kê phần tử nhập liệu đang hiển thị: [contenteditable], textarea, input (trừ type=hidden). Mỗi phần tử in: số thứ tự, thẻ, id, placeholder, aria-label, data-e2e, role, hình chữ nhật, selector đề xuất. Thứ tự ưu tiên selector đề xuất: data-e2e, id, aria-label, placeholder, rồi tag[contenteditable]. Người dùng nhập số thứ tự (một hoặc nhiều, cách nhau dấu phẩy); tool kiểm mỗi selector khớp đúng 1 phần tử hiển thị rồi ghi chat_input_selectors vào config.local.yaml. Script chỉ đọc thuộc tính của phần tử nhập liệu, không đọc nội dung chat của người khác.
latency
Theo §9.3.
6.8 Log
• Tệp logs/session-YYYYMMDD-HHMMSS.jsonl, UTF-8, mỗi dòng một đối tượng JSON.
• Khóa chung: ts (ISO 8601 có múi giờ), t_ns (perf_counter_ns), ev.
ev
Khóa thêm
Mức
asr_partial, asr_final
text
DEBUG
parse
text, spans (danh sách {value, kind, unit, closed, extendable}), passed (danh sách value qua gate)
DEBUG
decision
value, action, reason, t_audio_ns
INFO
send
value, text, ok, lat_audio_to_end_ms, lat_send_ms, error
INFO
state
state, cause
INFO
audio_gap, audio_overflow, audio_silent, send_unverified, failsafe
chi tiết sự kiện
WARNING
error
code, message
ERROR
lat_audio_to_end_ms = (t_end_ns - t_audio_ns) / 1e6; lat_send_ms = (t_end_ns - t_start_ns) / 1e6. Log mức DEBUG chứa bản ghi lời người bán; log mức INFO không chứa lời nói. Log chỉ nằm cục bộ.
7. Giao diện
7.1 CLI
pricetyper run       [--config PATH] [--armed] [--dry-run]
pricetyper gui       [--config PATH] [--youtube-test] [--asr-compare] [--whisper-model base|small|medium]
pricetyper replay    --wav PATH [--config PATH] [--speed X] [--dry-run]
pricetyper record    --seconds N --out PATH [--device NAME]
pricetyper calibrate [--config PATH] [--target chat|send]
pricetyper discover  [--config PATH]
pricetyper latency   --wav PATH --truth PATH [--config PATH]
pricetyper latency   --bench-sender N [--config PATH]
run chạy không giao diện; điều khiển bằng hotkey và gõ lệnh trên console: on, off, status, quit. --armed đặt start_armed = true cho lần chạy đó.
Mã thoát: 0 bình thường; 2 cấu hình sai; 3 lỗi âm thanh; 4 thiếu model; 5 sender không sẵn sàng; 130 dừng khẩn hoặc Ctrl+C.
7.2 GUI Tkinter (ui/gui.py)
Tkinter thuộc thư viện chuẩn của Python (THIẾT KẾ: chọn Tkinter để không thêm phụ thuộc). Bố cục (THIẾT KẾ):
1. Nhãn trạng thái lớn: “ĐANG NGHE — KHÔNG GỬI” hoặc “ĐANG BẬT GỬI” (dùng chữ, không chỉ dùng màu).
2. Nút “Bật/Tắt gửi (F8)”.
3. Hộp đánh dấu “Chạy thử (dry-run)”.
4. Ô nhập: giá nhỏ nhất, giá lớn nhất, cooldown cùng giá (giây), cooldown mọi giá (giây), tối đa gửi mỗi phút. Thay đổi áp dụng ngay cho Decider và không ghi vào tệp.
5. Giao diện thường có nhãn “Nghe được”, “Số trích được”, “Đã gửi gần nhất” và “Độ trễ gần nhất”. YouTube number mode hiển thị transcript đã chốt tách khỏi partial; số tạm từ partial nằm ở dòng riêng, số cuối chỉ cập nhật từ final và được hiển thị dạng số thuần. TikTok number mode ghi rõ transcript “Nghe được” là câu đã chốt; trạng thái ASR riêng phải cho biết đang chờ VAD chốt câu khi audio còn vào, vì chế độ này tắt giải mã partial lặp lại để tránh nghẽn hàng đợi. Bấm F8 hoặc kết nối tab không dừng nhận dạng. YouTube và TikTok number mode không có ô min/max giá. TikTok có tùy chọn gửi Enter, mặc định tắt và chỉ đổi khi disarmed. Giao diện phải nói rõ thời gian bắt đầu từ chunk đóng VAD; số đó chưa gồm VAD chờ im lặng, độ dài câu hoặc độ trễ phân phối của TikTok. Prototype hiển thị trạng thái bridge và RMS PCM gần nhất. TikTok GUI cập nhật hàng đợi UI mỗi 10 ms; các chế độ khác poll mỗi 50 ms.
6. Bộ đếm: TikTok ghi riêng lượt điền hoặc số lần đã phát Enter; số lần phát Enter không đồng nghĩa comment đã được TikTok xác nhận.
7. Ô log chỉ đọc, giữ 200 dòng cuối.
8. Nút “Dừng khẩn (F10)”.
9. Banner cảnh báo dễ thấy và phát một tiếng báo hệ thống khi có cảnh báo mới (không phát lặp khi cùng cảnh báo còn hiển thị) khi mất kết nối tab, rơi audio, không có tín hiệu liên tục 30 giây, VAD phát hiện lời nói nhưng ASR không cập nhật trong 15 giây, hoặc thread pipeline lỗi. ASR stall và audio gap phải disarm; audio gap phải reset ASR. Cảnh báo không tự bật lại thao tác. Cảnh báo im lặng được gỡ khi tín hiệu trở lại; cảnh báo ASR stall được gỡ khi ASR có kết quả mới; các cảnh báo khác giữ đến khi người dùng ẩn hoặc khôi phục kết nối.
Luồng: pipeline đẩy sự kiện vào ui_q; GUI đọc bằng root.after(50, poll), riêng TikTok Web dùng 10 ms; không gọi Tk từ thread khác.
Checklist nghiệm thu GUI (thủ công):
1. Khởi động ở trạng thái “ĐANG NGHE — KHÔNG GỬI”.
2. F8 và nút đều đổi trạng thái; nhãn đổi theo trong 200 ms.
3. Ở trạng thái “ĐANG NGHE”, hô giá: “Số trích được” cập nhật, bộ đếm bỏ qua do disarmed tăng, không có tin nào được gửi.
4. Ở trạng thái “ĐANG BẬT GỬI” với trang giả: tin được gửi đúng giá trị, đúng 1 lần.
5. Hạ giá lớn nhất xuống dưới giá vừa hô: giá đó không được gửi.
6. Bật “Chạy thử”: không có tin nào được gửi dù ở ARMED.
7. F10 và nút “Dừng khẩn” đều thoát tiến trình với mã 130.
8. Đóng cửa sổ bằng nút X: tiến trình thoát với mã 0 trong 3 giây.
7.3 Hotkey mặc định
Khóa cấu hình
Phím
Tác dụng
hotkeys.toggle
F8
đổi LISTENING và ARMED
hotkeys.calibrate
F9
chốt tọa độ chuột (chỉ trong lệnh calibrate)
hotkeys.panic
F10
dừng khẩn, thoát mã 130
8. Xử lý lỗi
Mã hoặc sự kiện
Điều kiện
Hành vi
ERR_CONFIG
cấu hình không hợp lệ
in danh sách lỗi; thoát 2
ERR_MODEL
thiếu thư mục model
in đường dẫn mong đợi; thoát 4
ERR_AUDIO_DEVICE
không tìm thấy loa hoặc loopback
in danh sách loa; thoát 3
ERR_AUDIO_RATE
không khởi tạo được luồng 16000 Hz
in thông báo; thoát 3 (U10)
ERR_WAV_FORMAT
WAV không phải PCM 16-bit mono 16000 Hz
thoát 3
ERR_ADB_SERIAL
có nhiều hơn một thiết bị adb mà serial rỗng
thoát 5
SenderPrepareError
không thấy selector, thiếu tọa độ, adb không ở trạng thái device
không cho vào ARMED; thoát 5 khi chạy run --armed
audio_overflow
audio_q đầy
bỏ khối cũ nhất; WARNING; tiếp tục
audio_silent
im lặng 30 giây
WARNING; tiếp tục
send_failed
send() trả ok = false hoặc ném lỗi
ERROR; không thử lại; 3 lần liên tiếp thì về LISTENING
failsafe
pyautogui ném FailSafeException
về LISTENING; ghi log failsafe
send_unverified
ô chat còn nội dung sau khi gửi (khi verify_after_send)
WARNING
Lỗi chưa bắt trong thread
exception
log ERROR kèm stack; controller về STOPPED; thoát với mã khác 0
9. Kiểm thử và nghiệm thu
9.1 Bộ test tự động
Tệp
Nội dung
Điều kiện qua
tests/test_vi_number.py
53 ca ở §6.4
53/53
tests/test_gate.py
15 vector ở §6.5 và 2 ca ngưỡng mặc định
17/17
tests/test_decider.py
bảng vết §6.5 và ca disarmed
2/2
tests/test_config.py
cấu hình mặc định hợp lệ; mỗi quy tắc ở bảng kiểm tra §5 có 1 ca sai dẫn tới ERR_CONFIG
tất cả qua
tests/test_senders_fake_page.py
PlaywrightSender với fake_live.html: gửi 199 thì window.__sent bằng ['199']; gửi 20 giá trị liên tiếp thì window.__sent có 20 phần tử đúng thứ tự. Đánh dấu @pytest.mark.browser, bỏ qua khi không có trình duyệt Chromium tương thích (Chrome hoặc Edge)
tất cả qua
tests/test_cli.py
pricetyper --help liệt kê đủ 7 lệnh: run, gui, replay, record, calibrate, discover, latency
qua
pytest -q PHẢI chạy được mà không cần micro, loa, màn hình, mạng hay tài khoản TikTok; riêng nhóm browser cần Chrome hoặc Edge theo cấu hình kiểm thử. Đã kiểm thử trong môi trường tham chiếu: 54 test (37 + 15 + 2) qua trong 0,12 giây.
9.2 Dữ liệu thật và replay
1. Thu: pricetyper record --seconds 120 --out tests/data/live1.wav trong lúc xem livestream.
2. Gán nhãn tay tệp tests/data/live1.truth.json: danh sách các đối tượng có hai khóa nguyên t_audio_end_ms (thời điểm tính từ đầu tệp mà người bán đọc xong từ cuối của giá) và value (giá trị cần gửi):
[
  {"t_audio_end_ms": 4210, "value": 199},
  {"t_audio_end_ms": 9875, "value": 250}
]
3. Replay: pricetyper replay --wav tests/data/live1.wav --dry-run; log nằm trong logs/. Ở dry_run, sender thật không được tạo hay gọi; NullSender thay thế và Decider chạy với armed = true, nên log decision có action = send cho mỗi lệnh lẽ ra được gửi (FR-09).
4. Chỉ số: precision = số lệnh send khớp nhãn chia tổng số lệnh send; recall = số nhãn có lệnh send khớp chia tổng số nhãn. Một lệnh khớp nhãn khi value trùng và thời điểm lệnh nằm trong khoảng từ t_audio_end_ms đến t_audio_end_ms + 3000 (THIẾT KẾ).
5. Mục tiêu v1 (THIẾT KẾ, chưa được kiểm chứng bằng dữ liệu): precision ≥ 0,95 và recall ≥ 0,80 trên ít nhất 30 nhãn. Không đạt thì hiệu chỉnh tham số (U13, U15); không đổi parser mà không cập nhật test.
9.3 Đo độ trễ
`pricetyper latency --wav PATH --truth PATH` chạy pipeline với NullSender và `audio.wav_speed = 1.0`; mỗi lệnh dự kiến ghi `t_send_wall`. Độ trễ một nhãn = `t_send_wall - (t_start_wall + t_audio_end_ms)`, trong đó nhãn audio phải chỉ đúng lúc phát âm xong số và `t_start_wall` là lúc khối đầu tiên được đưa vào pipeline. Lệnh in P50, P95, max (ms) cho nhãn khớp và số nhãn không khớp. Đây là phép đo pipeline replay với NullSender, không đo browser bridge hay ô nhập.

Mục tiêu TikTok end-to-action cần đo riêng từ âm tiết cuối có nhãn đến lúc số được điền/phím Enter được phát; không dùng thời điểm chunk đóng VAD thay cho âm tiết cuối. Mục tiêu dưới 1 giây tới khi comment xuất hiện phụ thuộc thêm TikTok và mạng, không thể được bảo đảm bởi app. Không đọc/scrape chat để xác minh. Ghi exact-number accuracy, số bỏ sót/thừa, P50/P95 end-to-action và quan sát thủ công việc comment xuất hiện thành các chỉ số riêng; chỉ nghiệm thu khi có audio có nhãn và phép đo lặp lại được.
pricetyper latency --bench-sender N: gọi sender.send('1') N lần liên tiếp và in P50, P95 của t_end_ns - t_start_ns (đo L5). Lệnh từ chối chạy khi URL trang đang điều khiển khớp tiktok.com; chỉ dùng với trang giả hoặc NullSender.
9.4 Checklist nghiệm thu v1
1. pytest -q qua toàn bộ.
2. record 10 giây tạo WAV hợp lệ (FR-01).
3. replay --dry-run trên WAV tự thu cho ra log asr_*, parse, decision (FR-02, FR-10, FR-11).
4. F8 đổi LISTENING và ARMED; mỗi lần có dòng state (FR-07).
5. Sau khi tắt bằng F8, hô giá: không có lệnh gửi nào (FR-07).
6. Với trang giả: gửi đúng giá trị, đúng 1 lần (FR-06).
7. Hai lần hô cùng một giá trong 10 giây: 1 lần gửi (FR-05).
8. F10 thoát với mã 130 (FR-08).
9. Checklist GUI §7.2 đạt (FR-13).
10. Android: đạt, hoặc ghi lại mục U tương ứng (§11) cho từng điểm không đạt.
10. Cài đặt và chạy
10.1 Yêu cầu
Windows 10 hoặc 11; Python 3.12 từ python.org; Google Chrome (khi dùng playwright với channel: chrome); scrcpy và adb (khi dùng Android); khoảng 1 GB RAM trống (NFR-03).
10.2 pyproject.toml
[build-system]
requires = ['setuptools>=68']
build-backend = 'setuptools.build_meta'

[project]
name = 'pricetyper'
version = '0.1.0'
requires-python = '>=3.12'
dependencies = [
  'vosk==0.3.45',
  'sherpa-onnx==1.13.8',
  'soundcard>=0.4.6',
  'numpy>=2.0',
  'keyboard==0.13.5',
  'pyautogui==0.9.54',
  'playwright>=1.56',
  'pydantic>=2.9',
  'pyyaml>=6.0',
]

[project.optional-dependencies]
dev = ['pytest>=8', 'pytest-timeout>=2.3', 'ruff']
resample = ['scipy>=1.14']

[project.scripts]
pricetyper = 'pricetyper.cli:main'

[tool.setuptools.packages.find]
where = ['src']

[tool.pytest.ini_options]
markers = ['browser: cần Google Chrome hoặc Microsoft Edge']
timeout = 60
Phiên bản đã đối chiếu trên PyPI ngày 2026-10-19 (ĐÃ XÁC MINH):
Gói
Bản mới nhất
Ngày phát hành
Yêu cầu Python
vosk
0.3.45
2022-12-14
từ 3 trở lên
soundcard
0.4.6
2026-04-12
≥ 3.5
numpy
2.5.4
2026-10-10
≥ 3.12
keyboard
0.13.5
2020-03-23
không ghi
pyautogui
0.9.54
2023-05-24
không ghi
playwright
1.64.0
2026-10-13
≥ 3.10 (chữ ký API kiểm trên 1.56.0)
pydantic
2.14.1
2026-10-11
≥ 3.10
pyyaml
6.0.3
2025-09-25
≥ 3.8
pytest
9.1.1
2026-06-19
≥ 3.10
scipy (chỉ extras resample)
1.18.1
2026-08-21
≥ 3.12
10.3 Lệnh cài (PowerShell; đường dẫn dùng dấu gạch chéo xuôi)
py -3.12 -m venv .venv
.venv/Scripts/Activate.ps1
pip install -e '.[dev]'
copy config.example.yaml config.yaml
python scripts/download_robust_asr_models.py
Nếu chưa có Google Chrome: python -m playwright install chrome (cách dùng của Playwright; chưa chạy trong phiên soạn tài liệu này).
10.4 Chạy lần đầu
pricetyper gui --youtube-test
Hoặc chạy `run-youtube-test.ps1`; nạp extension trong Chrome/Edge, mở video YouTube, rồi chủ động bấm extension để capture audio. Chế độ YouTube luôn ép NullSender, không mở TikTok, không đọc chat và không gửi tin nhắn. Để benchmark Vosk, cài thêm model `vosk-model-small-vn-0.4` vào `models/` rồi chạy `run-youtube-test.ps1 -AsrCompare`.
11. Mục chưa xác minh
Mã
Hạng mục
Lý do chưa xác minh
Cách tự xác minh
U1
Selector ô chat trên web TikTok Live
DOM do TikTok kiểm soát, không có nguồn ổn định
pricetyper discover; mỗi selector được kiểm khớp đúng 1 phần tử hiển thị
U2
Dạng URL phiên live (mặc định **/@*/live*)
chưa kiểm tra
mở livestream, so với url_pattern, sửa cấu hình nếu khác
U3
Phím ENTER có gửi tin trong app TikTok Android
chưa thử
thử send_mode: enter; không gửi thì dùng click_button với send_xy
U4
Chế độ bàn phím mặc định của scrcpy có đưa chữ số vào ô chat TikTok
chưa thử
thử trên thiết bị; không được thì chạy scrcpy với --keyboard=uhid; vẫn không thì dùng sender adb
U5
Model Vosk tiếng Việt xuất số bằng chữ hay chữ số; độ chính xác với nhạc nền và nhiều người nói
chưa có mẫu âm thanh
record rồi replay, xem log DEBUG asr_partial
U6
Độ trễ nhận dạng thực tế; so sánh hai model
cần đo
§9.3
U7
Giới hạn tốc độ chat và hình phạt của TikTok
không có nguồn
giữ max_sends_per_min thấp; Không đủ dữ liệu để xác minh
U8
Văn bản gốc điều khoản TikTok
mới đọc qua nguồn thứ cấp
đọc tại tiktok.com/legal bản áp dụng cho quốc gia của tài khoản
U9
keyboard có cần quyền quản trị trên Windows
chưa thử
chạy pricetyper run không quyền quản trị rồi nhấn F8
U10
Thu loopback 16000 Hz chạy được trên mọi thiết bị âm thanh
mới xác minh cờ trong mã soundcard
pricetyper record trên máy thật; lỗi thì thực hiện nhánh dự phòng ở M2
U11
iOS
không có đường thu âm thanh và điều khiển đã xác minh
ngoài phạm vi v1
U12
Cờ --remote-debugging-port của Chrome khi dùng thư mục dữ liệu mặc định (chế độ attach cdp)
chưa kiểm tra
chạy Chrome với --remote-debugging-port=9222 và --user-data-dir trỏ vào thư mục riêng, rồi thử connect_over_cdp
U13
Giá trị mặc định của hold, cooldown, danh sách loại ngữ cảnh
là giá trị thiết kế
hiệu chỉnh bằng log thật (§9.2)
U14
Độ trễ của adb shell input
chưa đo
chạy 20 lần adb shell input keyevent 66 bằng Measure-Command
U15
Cách người bán thực tế đọc giá (mức phổ biến của cách nói rút gọn như “một trăm hai” = 120; cách ASR ghi chữ “k”: k, ca, ka)
chưa có dữ liệu
thống kê trên nhãn thật (§9.2); chỉnh parser.shorthand và parser.k_tokens
12. Lộ trình triển khai
Mốc
Sản phẩm
Nghiệm thu
P0
YouTube number-recognition prototype: Chrome extension tabCapture, BrowserTabSource, `gui --youtube-test`, transcript and number value without price gate; force NullSender
Unit test protocol/PCM + manual run on known YouTube video: capture is tab-specific, output volume independent, displayed number matches spoken number, no sender/chat/raw audio file. Đây là checkpoint hiện tại.
Bộ so sánh P0.1 và benchmark/cải thiện ASR cục bộ cho điều kiện livestream: Zipformer-VI + Silero VAD là engine mặc định; Vosk, Whisper, Gipformer 1.5 INT8 và một Zipformer RNNT streaming chunk-16 là các nhánh benchmark riêng. Hai model mới chỉ chạy theo yêu cầu trong benchmark local; chúng không thay lõi, không tham gia consensus, TikTok sender hay installer. Ưu tiên đo exact-number, số bỏ sót/thừa, WER/CER, thời điểm partial, P50/P95 và RAM; giá qua gate là phép đo phụ. Model streaming mang giấy phép CC-BY-NC-ND-4.0 nên chỉ dùng thử local, không sửa đổi/đóng gói/phân phối. Sau đó mới đánh giá tách nguồn và overlap detection tự động.
Báo cáo WER/CER, exact-number accuracy, số bỏ sót/thừa, tỷ lệ số trích thừa, P50/P95 và RAM trên tiếng Việt Bắc/Trung/Nam, speech + music/noise và chồng lấp 2+ giọng. Chỉ đưa nhánh tăng cường vào mặc định nếu nó cải thiện exact-number accuracy mà vẫn đạt latency; bất đồng model hoặc chồng lấp không rõ phải abstain. Số tạm từ ASR partial chỉ dùng để đo phản ứng sớm, tách khỏi kết quả final. Đo chunk-to-ASR riêng với độ trễ từ lúc nói xong số đến lúc có kết quả hiển thị; không xem chỉ số chunk-to-ASR là độ trễ đầu-cuối. TikTok pilot chưa thay đổi acceptance P0.1 và không được coi là chứng minh độ chính xác ASR.
M0
Khung dự án: pyproject.toml, cây thư mục §4, config.py (pydantic, gộp 3 lớp theo §5), logging_utils.py, cli.py khai báo 7 lệnh, types.py theo §3.4
pytest -q qua test_config.py và test_cli.py; pricetyper --help liệt kê 7 lệnh
M1
parsing/vi_number.py, parsing/gate.py, decision/decider.py theo mã tham chiếu §6.4 và §6.5; nối DecisionConfig với GateCfg và DeciderCfg
37 + 15 + 2 test qua
M2
audio/loopback.py, audio/wav_source.py, lệnh record
Trên Windows thật: record --seconds 10 tạo WAV hợp lệ (FR-01). Nếu gặp ERR_AUDIO_RATE (U10): thêm nhánh thu 48000 Hz rồi hạ mẫu bằng scipy.signal.resample_poly (extras resample)
M3
asr/zipformer_engine.py + VAD làm engine mặc định; Vosk baseline; pipeline đa luồng theo §3.2, log JSONL §6.8, lệnh replay
replay --dry-run trên WAV tự thu cho ra log đầy đủ; báo cáo precision và recall theo §9.2 và so với mục tiêu ở §9.2
M4
senders/ (playwright_sender.py, desktop_sender.py, null_sender.py), fixtures/fake_live.html, controller.py, ui/hotkeys.py, lệnh latency
test_senders_fake_page.py qua; F8 và F10 hoạt động; latency --bench-sender 20 in P50 và P95
M5
ui/gui.py, lệnh calibrate, lệnh discover
Checklist GUI §7.2 đạt; discover ghi được config.local.yaml
M6
Android: chế độ android_scrcpy, senders/adb_sender.py, tài liệu thao tác
Trên thiết bị Android ≥ 11 thật: thu được âm thanh qua loopback và gửi được vào ô chat (thủ công); mỗi điểm không đạt ghi lại theo mục U3, U4, U14
M7 (pilot Edge cũ)
TikTok Web trên Edge: `gui --tiktok-web`, extension audio của tab Live, `discover --tiktok-web`, Playwright sender và dry-run mặc định. Đây là baseline cũ; sender mở profile Edge riêng.
Các lần kiểm tra M7 chỉ dùng fake page/protocol; không chứng minh browser/account/live hoặc bình luận xuất hiện dưới 1 giây.

M8 (đa trình duyệt; đang triển khai)
Giữ parser, gate, quyết định, Zipformer/VAD và bridge PCM dùng chung. TikTok Web dùng number scope: bỏ qua gate giá, chỉ xử lý ASR final, chọn số cuối; dãy đếm tường minh được tách thành số riêng. Extension Chromium capture và thao tác trong cùng TikTok Live tab, xác minh tab ID, host/path và input nhìn thấy được. Selector input được xét theo thứ tự cụ thể đến tổng quát: ưu tiên duy nhất `[data-e2e="room-chat-input-field"]` khi selector này khớp; nếu nó không khớp thì mới dùng các selector dự phòng. Nếu selector được xét khớp nhiều input, phải từ chối thay vì đoán. Mặc định chỉ điền `@<số>` vào input trống; số nhận dạng vẫn hiển thị dạng thuần trong app. Sau khi điền, extension nhường một microtask cho cập nhật trang rồi xác nhận input còn đúng `@<số>` trước khi gửi. Một checkbox tắt sẵn bật chế độ gửi bằng một synthetic DOM Enter; sự kiện có `isTrusted=false` và TikTok có thể bỏ qua. Cần connect/probe, bỏ dry-run và F8. Chỉ dùng một lần, không retry. Acknowledgement xác nhận event đã được dispatch, không chứng minh TikTok nhận/hiển thị comment. Acceptance cần local fake page, protocol và kiểm tra tương tác thật trên từng browser/OS được công bố. Không gọi “universal” nếu chưa có bằng chứng; unsupported phải hiện rõ. Installer/onboarding cửa hàng, độ đúng số và P95 latency còn chưa nghiệm thu.
P1
Đóng gói bản Windows với Python runtime, installer, shortcut Start/Desktop và uninstaller sau khi P0 đạt; checkbox ở trang hoàn tất có thể mở trợ lý thiết lập extension. Extension local chưa phát hành store vẫn cần người dùng xác nhận nạp thủ công.
Cài và mở trên tài khoản Windows sạch không cần Python hoặc PowerShell; kiểm tra lựa chọn mở trợ lý extension; không làm packaging trong prototype hiện tại

13. Quy trình làm việc với Antigravity
13.1 Mục tiêu khi giao việc
Antigravity là agent lập trình làm việc trực tiếp trong thư mục dự án. Sản phẩm cuối vẫn là ứng dụng cài đặt Windows theo §1; không chuyển thành website hay dịch vụ web. YouTube recognition và TikTok Web sender là hai chế độ riêng; TikTok pilot chưa được coi là nghiệm thu ASR/latency. Android và P1 đóng gói là các mốc sau. Agent phải đọc `AGENTS.md`, quy tắc trong `.agents/rules/` và `docs/SPEC.md` trước khi sửa mã.

Một lần giao việc nên chỉ tập trung vào một mốc, nêu rõ:
• Mã mốc và các module được phép sửa.
• Tiêu chí nghiệm thu lấy nguyên ý từ §12 và yêu cầu liên quan ở §2, §6–§9.
• Trong `--youtube-test` chỉ dùng YouTube và khóa sender thật. Trong `--tiktok-web` chỉ dùng tab Live người dùng mở/chọn; mặc định disarmed/dry-run và chỉ arm bằng F8.
• Báo cáo phải tách: đã làm, lệnh kiểm tra đã chạy, kết quả quan sát được, kiểm tra chưa chạy và lý do.

13.2 Mở dự án
1. Mở Antigravity và chọn thư mục gốc chứa `pyproject.toml`, `AGENTS.md` và `docs/SPEC.md`.
2. Chọn chế độ lập trình trong workspace hiện tại; không tạo ứng dụng web mới.
3. Để Antigravity đọc hướng dẫn repository. Nếu nó không tự đọc, yêu cầu đọc `AGENTS.md` và các tệp quy tắc trước khi thay đổi.
4. Chọn đúng milestone đang được giao: P0/P0.1 cho nhận dạng YouTube, M8 cho TikTok Web, hoặc mốc đóng gói P1; không gộp chúng vào một thay đổi.
5. Khi một yêu cầu chưa thể kiểm tra trên PC hiện tại, agent phải ghi rõ điểm đó vào `docs/IMPLEMENTATION_STATUS.md` hoặc báo cáo, không tự đổi yêu cầu thành đã đạt.

13.3 Nguyên tắc tương tác
• Dùng một nhánh công việc hoặc snapshot có thể phục hồi trước mỗi mốc lớn.
• Không cho agent gộp các mốc lớn thành một lần sửa khó review.
• Cho phép agent tạo hoặc sửa unit test thuộc chính mốc đang thực hiện, vì các test ở §9 là một phần của đặc tả và tiêu chí nghiệm thu.
• Không đưa mật khẩu, cookie, token hoặc thông tin đăng nhập vào prompt, cấu hình hay log.
• Thử gửi trên `tests/fixtures/fake_live.html` trước. Chỉ thử với tài khoản và phiên livestream thật khi người dùng chủ động yêu cầu và đã tự mở đúng cửa sổ đích.
• Không triển khai hành vi né giới hạn, né phát hiện, đọc chat người khác hoặc tương tác thay người dùng ngoài việc nhập số đã nhận dạng và tùy chọn gửi Enter theo xác nhận người dùng.

14. Prompt triển khai theo mốc
Các prompt dưới đây dùng lần lượt trong Antigravity. Nội dung trong ngoặc vuông cần thay bằng thông tin của workspace nếu cần. Không yêu cầu agent báo thành công nếu chưa chạy được tiêu chí tương ứng.

14.1 Prompt M0 — khung dự án
```text
Đọc AGENTS.md, .agents/rules/ và docs/SPEC.md. Thực hiện riêng mốc M0 trong §12: hoàn thiện cấu trúc dự án, pyproject.toml, config.py với Pydantic v2 và gộp mặc định + config.yaml + config.local.yaml theo §5, logging_utils.py, cli.py có đủ 7 lệnh, types.py đúng §3.4. Tạo config.example.yaml và .gitignore theo §4. Viết các test M0 theo §9.1. Không triển khai các mốc M1 trở đi. Chạy đúng lệnh nghiệm thu M0, báo cáo kết quả thật và liệt kê phần chưa chạy.
```

14.2 Prompt M1 — parser và quyết định
```text
Đọc hướng dẫn repository và docs/SPEC.md. Thực hiện riêng M1. Chuyển mã tham chiếu §6.4–§6.5 thành parsing/vi_number.py, parsing/gate.py và decision/decider.py; nối cấu hình Pydantic vào GateCfg/DeciderCfg. Giữ nguyên các vector và kỳ vọng trong SPEC. Thêm tests/test_vi_number.py, test_gate.py, test_decider.py theo §9.1. Chạy chúng và báo cáo từng nhóm; không sửa kỳ vọng để làm test xanh nếu chưa cập nhật lý do trong SPEC.
```

14.3 Prompt M2 — thu âm và record
```text
Đọc hướng dẫn repository và docs/SPEC.md. Thực hiện riêng M2: LoopbackSource, WavSource và lệnh record theo §6.1, §7.1, §8. Mặc định yêu cầu PCM mono 16 kHz int16. Thêm test không cần thiết bị cho định dạng WAV. Không giả vờ đã xác nhận loopback trên máy này: chạy record 10 giây chỉ khi thiết bị âm thanh sẵn sàng, ghi thời lượng thật và kết quả. Nếu thiết bị không nhận 16 kHz, triển khai nhánh resample đúng §12/M2 và ghi rõ phụ thuộc extras.
```

14.4 Prompt M3 — ASR và replay
```text
Đọc hướng dẫn repository và docs/SPEC.md. Thực hiện riêng M3: Vosk streaming, pipeline đa luồng, JSONL logger và replay theo §3, §6.3, §6.8, §9.2. Mỗi quyết định phải có đúng một dòng decision. Replay --dry-run phải dùng NullSender, coi pipeline ở trạng thái armed để decision phản ánh lệnh dự kiến, nhưng tuyệt đối không tạo hay gọi sender thật. Thêm test với dữ liệu âm thanh tổng hợp/fixture, không cần micro. Nếu chưa có WAV có nhãn thật thì không tuyên bố precision/recall đã đạt; ghi thiếu dữ liệu.
```

14.5 Prompt M4 — sender, controller và latency
```text
Đọc hướng dẫn repository và docs/SPEC.md. Thực hiện riêng M4: NullSender, PlaywrightSender, DesktopSender, fake_live.html, Controller, hotkeys và latency theo §6.6–§6.7, §9.3. Giữ tất cả đối tượng Playwright trong một thread duy nhất. Kiểm sender bằng file fake cục bộ; kiểm disarm ngay trước send; lỗi gửi không được thử lại. Thêm test sender với fake page và test không mở trình duyệt. Chặn latency bench khi URL là TikTok. Chạy các nghiệm thu M4 có thể chạy trên máy này và ghi riêng phần cần Chrome hoặc UI thật.
```

14.6 Prompt M5 — GUI và công cụ cấu hình
```text
Đọc hướng dẫn repository và docs/SPEC.md. Thực hiện riêng M5: GUI Tkinter, calibrate và discover theo §6.7, §7.2–§7.3. Tk phải được tạo và cập nhật từ main thread; thread pipeline gửi dữ liệu qua queue và GUI poll bằng root.after. Nút X đóng sạch với mã 0; panic dừng với mã 130. Discover chỉ đọc thuộc tính phần tử nhập liệu hiển thị, không đọc nội dung bình luận/chat. Hoàn thiện checklist GUI §7.2, ghi mục nào cần thao tác thủ công.
```

14.7 Prompt M6 — Android
```text
Đọc hướng dẫn repository và docs/SPEC.md. Thực hiện riêng M6: tài liệu và kết nối Android qua scrcpy/loopback; ADB sender chỉ là đường dự phòng theo §1.3, §6.2, §6.6.3 và §8. Không tuyên bố Android đã đạt nếu chưa thử trên thiết bị thật Android 11 trở lên. Không bật USB debugging thay người dùng, không tự chọn thiết bị khi có nhiều thiết bị, không phát lệnh gửi chat thật trong nghiệm thu tự động. Ghi từng điểm U3, U4, U14 nếu chưa xác minh.
```

14.8 Prompt sửa lỗi sau nghiệm thu
```text
Đọc AGENTS.md, quy tắc liên quan và docs/SPEC.md. Sửa lỗi sau đây trong phạm vi nhỏ nhất: [mô tả lỗi và cách tái hiện]. Trước khi sửa, xác định module và yêu cầu SPEC liên quan. Thêm hoặc cập nhật test hồi quy tương ứng; chạy test liên quan và báo kết quả. Không đổi phạm vi, parser semantics, mặc định gửi hoặc hành vi an toàn nếu chưa nêu rõ trong báo cáo.
```

15. Chỉ dẫn repository cho agent
Các tệp trong mục này là hướng dẫn vận hành của repository, không thay thế yêu cầu kỹ thuật trong SPEC. Nếu một hướng dẫn mâu thuẫn với yêu cầu người dùng hoặc đặc tả được cập nhật, ghi nhận xung đột và ưu tiên yêu cầu mới hơn sau khi cập nhật tài liệu.

15.1 `AGENTS.md` ở thư mục gốc
PHẢI có các nội dung:
• Đọc SPEC và quy tắc liên quan trước khi sửa mã.
• Kiến trúc một ứng dụng Python cục bộ; không tạo web backend/frontend.
• Mặc định disarmed, F8 bật/tắt, F10 panic; dry-run không gọi sender thật.
• Giữ parser/gate/decider độc lập khỏi UI, ASR, audio và sender.
• Thay đổi parser phải cập nhật test và mục §6.4/§6.5.
• Mọi tương tác gửi thử phải dùng fake page hoặc NullSender; không đăng nhập, scrape chat hay phát tán dữ liệu.
• Chạy kiểm tra liên quan và báo trung thực kết quả; không xóa test để né lỗi.

15.2 Quy tắc `.agents/rules/parser.md`
Áp dụng cho `src/pricetyper/parsing/**` và `src/pricetyper/decision/**`. Giữ NFC, thứ tự ưu tiên parser và ranh giới span. Giá trị là đồng chính xác: số trần giữ nguyên; `nghìn`/`ngàn`/`k` nhân 1.000. Dấu chấm/phẩy nhóm hàng nghìn trong chữ số Ả Rập được chuẩn hóa trước khi tách token. Không diễn giải “triệu”, slang hoặc dải nghìn ngoài phạm vi. Thêm ví dụ vào SPEC và test trước khi đổi semantics.

15.3 Quy tắc `.agents/rules/senders.md`
Áp dụng cho `src/pricetyper/senders/**`, `controller.py`, `pipeline.py`, `ui/hotkeys.py`. Send chỉ nhận chuỗi ASCII theo SPEC; không retry; chỉ một sender worker; kiểm armed trước khi gửi. Playwright được tạo, dùng và đóng trong cùng worker thread. Sender preparation phải thành công trước khi vào ARMED. Fail-safe disarm; dry-run dùng NullSender và không khởi tạo sender thật.

15.4 Skill `.agents/skills/pricetyper-milestone/SKILL.md`
Skill này yêu cầu agent: (1) xác định mốc đang làm; (2) đọc các yêu cầu/định nghĩa liên quan; (3) xem trạng thái git và mã hiện có; (4) lập danh sách file cần đổi; (5) thực hiện một mốc; (6) thêm/chạy kiểm tra chỉ trong phạm vi yêu cầu; (7) review diff, rà secret và thay đổi ngoài phạm vi; (8) báo nghiệm thu, phần còn thiếu và rủi ro thiết bị. Không tự chuyển sang mốc kế tiếp.

16. Duy trì `docs/SPEC.md`
`docs/SPEC.md` là bản Markdown chuẩn. Khi chỉnh nội dung đặc tả:
1. Giữ số mục, FR/NFR/U và cross-reference ổn định; nếu đổi thì cập nhật mọi nơi có tham chiếu.
2. Phân biệt rõ ĐÃ XÁC MINH, ĐÃ KIỂM THỬ, THIẾT KẾ và Không đủ dữ liệu để xác minh. Nhãn ĐÃ KIỂM THỬ chỉ dùng khi mã và môi trường đã chạy thật.
3. Với thay đổi parser, quyết định gửi, config, sender hay threading, cập nhật cả đoạn mô tả, mã tham chiếu nếu có, vector test và prompt mốc tương ứng.
4. Không ghi kết quả kiểm thử thiết bị thành sự thật tổng quát; ghi model/OS/thiết bị/ngày và điều kiện đo.
5. Nguồn ngoài phải là trang chính thức hoặc mã nguồn chính thức khi có. Ghi ngày truy cập; nếu không đọc được văn bản gốc, giữ nhãn chưa xác minh.
6. Nếu tạo bản HTML/PDF để đọc, sinh từ Markdown này; không để hai bản nội dung khác nhau.

17. Quy trình nghiệm thu và phát hành
17.1 Trước khi chạy
• Kiểm Python 3.12, môi trường ảo, cấu hình hợp lệ, thư mục model và thiết bị đích.
• Mở Chrome/scrcpy thủ công khi cần. Chọn `dry_run: true` hoặc lệnh replay để xác nhận pipeline trước.
• Đảm bảo trạng thái ban đầu hiển thị LISTENING; thử F8 off rồi mới arm. Kiểm tra F10.

17.2 Nghiệm thu theo tầng
1. Unit: parser 53 ca, gate 15 vector, decider 2 ca và config/CLI.
2. Không thiết bị: `pytest -q`; phần browser có thể bỏ qua nếu không có Chrome như §9.1.
3. Tích hợp audio: record WAV 16 kHz mono, sau đó replay dry-run và kiểm log.
4. Sender giả: fake_live, xác minh chính xác text, số lần và thứ tự.
5. UI/hotkeys: checklist §7.2 và mã thoát §8.
6. Thử thật có kiểm soát: người dùng tự mở đúng livestream, bắt đầu disarmed, xác nhận ô chat và quan sát lệnh đầu tiên. Dừng ngay bằng F8/F10 nếu focus sai hoặc nhận dạng sai.
7. Android: hoàn tất phần tương ứng M6 trên thiết bị được nêu trong biên bản.

17.3 Biên bản kết quả
Mỗi mốc cập nhật một bảng với cột: yêu cầu, lệnh/thao tác, kết quả, môi trường, trạng thái (đạt/chưa đạt/chưa thử), bằng chứng/log. Không gộp “chưa thử” vào “đạt”. Để lại WAV nhãn và log cá nhân trong thư mục bị gitignore; không commit chúng.

17.4 Điều kiện dừng phát hành
Không bật gửi tự động nếu parser/gate/decider hoặc F8/F10 chưa đạt. Không phát hành cấu hình có `start_armed: true`. Không dùng live session làm fixture. Không quảng bá “độ trễ gần 0”: báo P50/P95 đo được và phân biệt độ trễ ASR, sender với độ trễ truyền livestream.

18. Giới hạn, giả định và các quyết định cần dữ liệu
18.1 Kết quả mong đợi
Mục tiêu người dùng là comment xuất hiện dưới 1 giây từ âm cuối của số, nhưng app không kiểm soát TikTok hoặc mạng nên không thể bảo đảm mốc đó. Có thể đo riêng end-to-action local đến lúc điền hoặc phát Enter và exact-number accuracy; không đánh đổi độ chính xác để rút ngắn thời gian chốt. Ảnh người dùng báo khoảng 2 giây là quan sát thủ công, chưa phải benchmark. GUI hiện đo từ chunk đóng VAD đến khi thao tác kết thúc, bỏ qua thời gian VAD đợi im lặng (đang cấu hình 250 ms), nên không đại diện thời gian từ âm cuối. Đo bằng audio có nhãn §9.2–§9.3; chỉ quan sát thủ công việc comment xuất hiện, không đọc/scrape nội dung chat.

18.2 Phạm vi mặc định
• `--youtube-test`: YouTube/Chrome or Edge để kiểm tra audio tab, Zipformer-VI/VAD và parser; không mở TikTok và không gửi chat. Vosk vẫn là baseline benchmark.
• `--tiktok-web`: prototype Windows qua extension Chromium, audio tab local và xử lý số final cuối câu trong cùng TikTok Live tab. Mặc định dry-run/disarmed và chỉ điền; checkbox gửi Enter tắt sẵn. Chỉ gửi sau khi người dùng bật checkbox, rời dry-run và F8. Không gửi từ partial. Browser, exact-number accuracy và end-to-action latency chưa nghiệm thu. Firefox/Safari/mobile là adapter riêng.
• Không hỗ trợ mua hàng tự động, chọn biến thể, thanh toán, đọc chat người xem hoặc chạy nhiều phiên.

18.3 Các giả định chưa được coi là đã xác minh
• TikTok có thể đổi DOM/selector, URL live, giới hạn gửi hoặc quy định theo khu vực; discover phải chạy lại khi UI đổi.
• ASR có thể nhầm giá khi có nhạc, tiếng chồng lấn, giọng vùng miền hoặc cách nói rút gọn.
• Vị trí focus, phím Enter và hành vi scrcpy phụ thuộc app/thiết bị/cấu hình.
• Luật và điều khoản nền tảng thay đổi theo thời điểm và quốc gia. Người dùng cần đọc điều khoản áp dụng cho tài khoản trước khi dùng. Không suy diễn mức phạt khi không có nguồn chính thức.

18.4 Câu hỏi dữ liệu để giải quyết sau khi có mẫu
1. Người bán thường đọc “một trăm hai” theo 120 hay 102?
2. ASR thường trả chữ số hay chữ viết, và ghi “k” ra sao?
3. Mức hold/cooldown nào đạt precision/recall mục tiêu trên ít nhất 30 nhãn?
4. Chrome/TikTok hiện tại có selector ổn định nào và Enter có gửi không?
5. Thiết bị Android cụ thể có route audio/input tương thích không?
Không tự đặt câu trả lời thay dữ liệu; ghi mẫu, ngày, điều kiện và độ tin cậy trong §11.

19. Nguồn tham khảo
Các nguồn dưới đây được đối chiếu ngày 2026-10-19 khi có thể truy cập. Trang web và phiên bản gói có thể đổi; ngày truy cập không chứng minh cấu hình cụ thể của mọi máy.

19.1 Nguồn kỹ thuật chính thức
• Chrome Extensions `tabCapture`: https://developer.chrome.com/docs/extensions/reference/api/tabCapture — user gesture, MediaStream của tab và yêu cầu định tuyến lại audio nếu vẫn muốn nghe.
• Chrome Local Network Access: https://developer.chrome.com/blog/local-network-access — cần thử hành vi kết nối extension tới loopback trên phiên bản Chrome mục tiêu.
• Vosk, danh sách model: https://alphacephei.com/vosk/models — model tiếng Việt small-vn-0.4, kích thước và WER trên Vivos; nguồn không khẳng định chất lượng trên livestream.
• Vosk API, ví dụ Python: https://github.com/alphacep/vosk-api/tree/master/python/example — dạng streaming AcceptWaveform/Result/PartialResult và PCM.
• OpenAI Whisper introduction: https://openai.com/index/whisper/ — multilingual ASR training and reported robustness to accents/background noise; không phải bảo đảm cho tiếng Việt livestream.
• WebRTC Audio Processing Module: https://webrtc.googlesource.com/src/+/refs/heads/main/modules/audio_processing/g3doc/audio_processing_module.md — có noise suppression/AGC/echo cancellation; không được coi là tách nguồn người nói.
• SpeechBrain SepFormer separation: https://speechbrain.readthedocs.io/en/stable/tutorials/basics/what-can-i-do-with-speechbrain.html — mẫu speech enhancement/separation để benchmark, không được mặc định rằng model mẫu phù hợp tiếng Việt bán hàng.
• pyannote.audio: https://github.com/pyannote/pyannote-audio — thành phần diarization, speech activity, speaker change và overlapped-speech detection.
• Playwright Python BrowserType: https://playwright.dev/python/docs/api/class-browsertype — launch persistent context và connect_over_cdp.
• SoundCard PyPI/docs: https://pypi.org/project/SoundCard/ — thiết bị, recorder và dữ liệu NumPy; khả năng resample loopback trên từng thiết bị vẫn cần thử (U10).
• scrcpy audio: https://github.com/Genymobile/scrcpy/blob/master/doc/audio.md — hỗ trợ chuyển tiếp audio Android 11+, điều kiện Android 11, nguồn output/playback và `--require-audio`.
• scrcpy README: https://github.com/Genymobile/scrcpy — chỉ dùng bản phát hành từ repository chính thức.
• Python Tkinter: https://docs.python.org/3/library/tkinter.html#threading-model — event loop và lưu ý threading.
• PyPI Vosk: https://pypi.org/project/vosk/ — metadata phát hành và wheel Windows.
• PyPI keyboard: https://pypi.org/project/keyboard/ — `add_hotkey`, nền tảng và giới hạn quyền của Linux; yêu cầu quyền quản trị Windows chưa xác minh (U9).
• PyAutoGUI: https://pyautogui.readthedocs.io/ — API click/typewrite/press và FAILSAFE; các giá trị mặc định cần gắn với phiên bản pin trong pyproject.
• TikTok Terms of Service: https://www.tiktok.com/legal/terms-of-service — phải chọn khu vực/tài khoản áp dụng và đọc bản hiện hành. Nội dung điều khoản gốc và áp dụng cho khu vực người dùng chưa được xác minh trong bản đặc tả này (U8).

19.2 Quy tắc trích nguồn
Nguồn PyPI chỉ chứng minh metadata gói được hiển thị tại trang; nguồn model chỉ chứng minh benchmark mà nhà phát hành công bố; tài liệu thư viện không chứng minh sender hoạt động trên trang TikTok thật. Nguồn thứ cấp không đủ để kết luận nghĩa pháp lý hoặc chế tài. Các khẳng định đó tiếp tục mang nhãn chưa xác minh cho tới khi kiểm tra văn bản chính thức hiện hành.
