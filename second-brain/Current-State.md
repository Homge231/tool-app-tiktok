# Hiện trạng NumberTyper

Cập nhật: 2026-10-23

## Mục tiêu sản phẩm

Ứng dụng Windows nghe audio trực tiếp từ tab TikTok Live do người dùng chọn và nhận diện số tiếng Việt bằng pipeline local. ASR/parser giữ số thô: chế độ chỉ điền thay bản nháp bằng số thuần (ví dụ `12`); chế độ gửi mới định dạng comment thành `@<số>` (nghe `12` thì gửi `@12`). Ưu tiên số đúng và phản hồi nhanh. Mục tiêu dưới 1 giây và độ chính xác rất cao vẫn là mục tiêu cần đo, không phải cam kết đã đạt.

## Đã triển khai

- GUI Windows và pipeline audio/ASR local; Zipformer-VI là core ASR, có Silero VAD.
- Extension Chromium kết nối tab được người dùng chọn, chuyển audio tab về app và gửi yêu cầu thao tác số về cùng tab.
- TikTok mode là number-first; ASR/parser trích số thô. Chế độ chỉ điền thay bản nháp số liên tục bằng số thuần; bản nháp cũ được phép có số thuần hoặc `@` trước số.
- Chế độ gửi Enter tạo nội dung `@<số>` từ số nhận dạng, yêu cầu ô nhập trống và kiểm tra nội dung trước khi dispatch Enter. Sau khi kiểm tra tab thành công, gửi được chọn sẵn; thao tác vẫn disarmed cho tới khi người dùng chủ động tắt dry-run và nhấn F8.
- Hai lựa chọn thao tác là radio buttons; dry-run vẫn là chốt an toàn riêng. F10 dừng khẩn.
- Có cảnh báo một số lỗi audio/bridge/pipeline.
- Installer Windows preview, shortcut Start Menu và trợ lý cài extension thủ công đã được tạo. Extension chưa được cài âm thầm; trình duyệt vẫn cần người dùng xác nhận Load unpacked.

## Bằng chứng gần nhất

- Repo ở commit `023a178` (`fix: replace TikTok number drafts continuously`), đã push thành công lên `origin/master` ngày 2026-10-23.
- Build preview hiện được ghi nhận tại `dist/NumberTyper-Setup-0.1.0-preview.exe`, SHA-256 `D72B30FFE1A6BCC3CC35CE1F67E4DB69B254A31967B207BCF1CD50DC97E3DFEF`. Bản build/model smoke check đã chạy thành công theo nhật ký phiên trước.
- Người dùng từng báo app đã nhận diện và điền số vào TikTok; trước đó có đo khoảng 2 giây, nhưng chưa có benchmark đồng bộ và lặp lại.
- Chưa xác minh rằng comment thật xuất hiện thành công trên Live với cơ chế Enter hiện tại. Extension dùng synthetic DOM Enter (`isTrusted=false`), TikTok có thể bỏ qua.

## Chưa đạt / chưa xác minh

- Chưa có tập dữ liệu gán nhãn đủ lớn để xác nhận độ chính xác số trên nhiều giọng, nhạc, nhiễu và người nói chồng lấp.
- Chưa đạt nghiệm thu đầu-cuối dưới 1 giây từ lúc nói số đến khi comment xuất hiện; thời gian VAD, ASR, thao tác tab và phân phối comment đều ảnh hưởng.
- Chưa chạy soak test 4 giờ sau thay đổi gần nhất; cảnh báo lỗi đã có nhưng không phải cam kết chạy liên tục.
- Chưa nghiệm thu thủ công phiên bản extension/build hiện tại trên Edge, Chrome hoặc Cốc Cốc; chia sẻ API Chromium không đồng nghĩa đã hỗ trợ mọi trình duyệt.
- Kiểm tra tĩnh cho thay đổi M8 hiện tại: `node --check browser_extension/service-worker.js`, `python -m py_compile` cho sender/decider/pipeline/gui, và `git diff --check` đã đạt. Không chạy automated tests, không mở GUI, không chạy TikTok hay build lại installer trong lần cập nhật này.
- Người dùng từng báo comment hiển thị thiếu `@` dù ô nhập có `@123`; code hiện đặt `@<số>` riêng cho chế độ gửi và xác nhận nội dung ô trước Enter, nhưng TikTok hiển thị comment sau Enter vẫn cần kiểm tra thủ công.
- Firefox, Safari và mobile chưa được hỗ trợ.
- Installer preview chưa qua nghiệm thu trên tài khoản Windows sạch hoặc cửa hàng extension; quyền phân phối model và SBOM còn cần rà soát trước phát hành công khai.

## Quy tắc an toàn hiện hành

- Audio/ASR xử lý local; không gửi audio lên cloud.
- Không đọc hoặc scrape chat/comment. Chỉ nhắm đến ô nhập duy nhất trong tab Live do người dùng chọn.
- Không tự bật gửi lúc khởi động: dry-run và disarmed phải được giữ cho tới thao tác chủ động của người dùng; F10 là dừng khẩn cấp.
- Log/ack của bridge không phải bằng chứng comment đã xuất hiện. Ghi nhận đúng mức bằng chứng.

## Tài liệu nguồn

- Đặc tả và quy tắc: `docs/SPEC.md`, `.agents/rules/`
- Trạng thái/mốc: `docs/IMPLEMENTATION_STATUS.md`
- Browser: `docs/BROWSER_COMPATIBILITY.md`
- Benchmark: `docs/ASR_ROBUSTNESS.md`
- Installer: `docs/SPRINT_P1_WINDOWS_INSTALLER.md`
