# Kế hoạch tiếp theo

Cập nhật: 2026-10-23

Đây là thứ tự gợi ý để tiếp tục. Chỉ đổi trạng thái sau khi có kết quả kiểm tra thực tế.

## P0 — Kiểm chứng luồng TikTok hiện tại

- [ ] Chạy bản app có thay đổi mới nhất và nạp/cập nhật extension tương ứng; installer preview chưa được build lại cho thay đổi này.
- [ ] Kiểm tra tab Live được chọn: bridge báo kết nối, RMS thay đổi, transcript vẫn cập nhật khi bấm F8 bật/tắt thao tác.
- [ ] Dry-run: xác nhận số nhận diện không tạo comment thật.
- [ ] Fill-only: xác nhận app điền số thuần vào ô; khi nhận số tiếp theo, thay bản nháp số cũ và không gửi.
- [ ] Submit: xác nhận nghe `12` thì ô nhập nhận `@12` trước Enter. Nếu người dùng chủ động thử gửi, chỉ ghi comment là đạt khi nhìn thấy chính xác `@12`; TikTok có thể bỏ qua hoặc biến đổi Enter tổng hợp.
- [ ] Ghi phiên bản app/trình duyệt/extension và lỗi hiển thị vào `docs/IMPLEMENTATION_STATUS.md` cùng [[Timeline]].

## P1 — Đo tốc độ và độ đúng bằng mẫu có nhãn

- [ ] Tạo bảng mẫu tiếng Việt: câu đầy đủ, số mục tiêu, vùng giọng, điều kiện âm thanh, timestamp và nguồn.
- [ ] Tách thời gian từ cuối âm tiết số đến VAD final, ASR, quyết định, thao tác input và lúc comment xuất hiện. Báo P50/P95; không chỉ dùng thời gian ASR.
- [ ] Tính exact-number precision/recall, bỏ sót và số thừa. Giữ cơ chế abstain khi nhiều model bất đồng hoặc speech overlap.
- [ ] So sánh thay đổi cấu hình/model trên cùng audio và nhãn; Zipformer hiện vẫn là core, không thay core chỉ dựa vào một vài mẫu.

## P2 — Độ ổn định phiên dài

- [ ] Chạy soak test 4 giờ trên audio tab thử nghiệm, không dùng gửi comment thật làm phép thử.
- [ ] Theo dõi bridge reconnect, hàng đợi audio, ASR stall, RAM, trạng thái cảnh báo và khả năng dừng F10.
- [ ] Sửa lỗi có log tái hiện; cảnh báo không được làm app tự re-arm.

## P3 — Preview cài đặt và phát hành

- [ ] Cập nhật installer sau các sửa lỗi được chấp nhận; xác minh shortcut, gỡ cài đặt và giữ dữ liệu người dùng.
- [ ] Rà giấy phép model và thư viện/SBOM trước khi chia sẻ rộng.
- [ ] Chỉ công bố trình duyệt/Windows được nghiệm thu. Thiết kế riêng adapter trước khi hứa Firefox/Safari/mobile.
- [ ] Cài extension từ store hoặc hướng dẫn cài đặt đơn giản hơn; không giả định có thể tự cài âm thầm vào mọi browser.

## Tiêu chí đóng mục tiêu preview

- Luồng setup làm được theo hướng dẫn bởi người dùng không chuyên.
- Capture tab và UI nghe được tiếp tục cập nhật trong khi trạng thái F8 đổi.
- Fill-only và dry-run có hành vi an toàn, dễ hiểu.
- Gửi TikTok được chứng minh bằng quan sát thủ công nếu tính năng đó khả dụng.
- Tốc độ và độ đúng báo bằng dữ liệu có nhãn; không ghi “<1 giây” hay “chính xác” nếu chưa đo.
