# Timeline dự án

## 2026-10-23 — M8 điền số liên tục và định dạng comment

- Chế độ chỉ điền liên tục thay bản nháp số cũ bằng số thuần; cooldown/lượt mỗi phút không chặn chế độ này. Nội dung chữ tùy ý trong ô vẫn được giữ nguyên và thao tác bị từ chối.
- ASR/parser tiếp tục đưa ra số thô. Chỉ chế độ gửi định dạng số thành `@<số>` (ví dụ `12` → `@12`); extension xác nhận chuỗi `@<số>` trong ô trước khi dispatch Enter.
- Thay checkbox chọn gửi bằng radio “Chỉ điền số · thay số cũ” / “Gửi @+số bằng Enter”; giữ dry-run, F8 và F10.
- Kiểm tra tĩnh chạy trong phiên: `node --check browser_extension/service-worker.js`; `.venv\Scripts\python.exe -m py_compile` trên sender, decider, pipeline, GUI; `git diff --check` — đều đạt. Không chạy automated tests, không mở GUI/TikTok, không build installer.
- TikTok vẫn chưa được kiểm tra lại: comment cũ từng hiện thiếu `@` dù ô trước Enter có `@123`. Vì app không đọc chat, chỉ có thể xác nhận rằng lệnh gửi/ô trước Enter chứa `@<số>`, không khẳng định comment đã hiện đúng.
- Git push được yêu cầu; trước khi ghi mục hoàn tất cần lưu commit/push hash và trạng thái remote. Android/M9 thay đổi có sẵn trong working tree là phần riêng và chưa được gộp vào M8.

## 2026-10-23 — Tạo Obsidian Second Brain

- Tạo vault `second-brain/` với trang bắt đầu, hiện trạng, kế hoạch và timeline để giữ context giữa các phiên làm việc.
- Thêm yêu cầu vào `AGENTS.md`: đầu phiên đọc vault; cuối phiên cập nhật state/plan/timeline; phân biệt triển khai với kiểm chứng.
- Ghi lại trạng thái code theo commit `b1afd2e`: TikTok auto-submit `@<number>` được chọn sẵn sau probe, nhưng dry-run/disarmed vẫn yêu cầu người dùng chủ động tắt và nhấn F8.
- Ghi rõ giới hạn: chưa nghiệm thu comment thật xuất hiện, độ chính xác số, latency dưới 1 giây, soak test 4 giờ hoặc hỗ trợ mọi browser.
- Chưa chạy test/build trong phiên tạo vault; chưa commit hoặc push các thay đổi vault. Những dữ kiện build được nhắc lại từ tài liệu/nhật ký phiên trước.

## 2026-10-22 — UI poll và auto-submit preview

- Sửa lỗi Tk UI poll bị dừng sau draft event thành công (`error=None`); thêm xử lý để poll tiếp tục và log/cảnh báo lỗi UI.
- Build preview Windows; smoke check app/model theo implementation status là thành công. Installer lưu trong `dist/`.
- Chọn trước auto-submit `@<number>` trong TikTok mode sau khi probe thành công; app vẫn cần dry-run off và F8. Giữ lựa chọn fill-only.
- Commit `b1afd2e` được push lên GitHub theo lịch sử repo. TikTok chưa xác nhận comment xuất hiện với Enter tổng hợp.
- Chi tiết: `docs/IMPLEMENTATION_STATUS.md`, `docs/PROTOTYPE_TIKTOK_WEB.md`, `docs/INSTALL_VI.md`.

## 2026-10-20 đến 2026-10-21 — Audio/ASR và bridge

- Thêm giới hạn đoạn VAD, xử lý hàng đợi audio quá tải, reset generation/disarm và cảnh báo lỗi pipeline/bridge.
- Cải thiện selector ô chat TikTok theo `data-e2e="room-chat-input-field"`; probe không đọc nội dung chat.
- Zipformer-VI vẫn là core local; benchmark một số đoạn cho kết quả không đồng nhất và không đủ dữ liệu để khẳng định độ chính xác/latency mục tiêu.
- Chi tiết và các số đo có giới hạn: `docs/ASR_ROBUSTNESS.md`, `docs/IMPLEMENTATION_STATUS.md`.

## Bối cảnh trước đó

- Dự án bắt đầu từ công cụ nghe lời tiếng Việt trong video/live rồi trích số. Quy tắc đơn vị tiền từng được làm rõ, sau đó sản phẩm chuyển trọng tâm từ giá tiền sang nhận diện số nói chung.
- Prototype YouTube dùng để thử capture audio tab và benchmark ASR; TikTok không được dùng làm fixture cho automated tests.
- Người dùng ưu tiên app Windows dễ cài, chạy local/offline, nhanh và đúng. Không có model ASR nào được xem là đảm bảo chính xác 100% trong nhạc/nhiễu/chồng lấp.
- Cần đối chiếu các chi tiết kỹ thuật cũ với `docs/` trước khi tiếp tục vì project đã thay đổi qua nhiều sprint.
