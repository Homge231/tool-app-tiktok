# NumberTyper — Second Brain

Đây là vault Obsidian ghi nhớ tiến độ và bối cảnh làm việc của NumberTyper. Mở thư mục `second-brain` bằng Obsidian: **Open folder as vault / Mở thư mục dưới dạng vault**. Để Codex tự đọc hướng dẫn đầu phiên, hãy mở/đính kèm cùng repo NumberTyper trong chat; nếu chat mới ở workspace khác, gửi đường dẫn repo hoặc mở repo đó trước.

## Khi bắt đầu một phiên

1. Đọc [[Current-State]] để biết hiện trạng và giới hạn đã xác minh.
2. Đọc [[Plan]] để tiếp tục việc đang ưu tiên.
3. Đọc mục mới nhất trong [[Timeline]] để biết thay đổi của phiên trước.
4. Nếu sửa code, đọc thêm `AGENTS.md`, `docs/SPEC.md` và quy tắc phù hợp trong `.agents/rules/`.

## Khi kết thúc một phiên

- Cập nhật [[Current-State]] nếu có thay đổi trong code, tài liệu, build hoặc kết quả kiểm tra.
- Cập nhật [[Plan]] khi thứ tự hoặc trạng thái công việc thay đổi.
- Thêm một mục ngày tháng vào [[Timeline]]: đã làm gì, kiểm tra nào thực sự chạy, kết quả và phần còn chưa xác minh.
- Phân biệt rõ **đã triển khai**, **đã kiểm tra**, **được người dùng xác nhận**, và **chưa kiểm chứng**. Không ghi mục tiêu thành kết quả.
- Giữ chi tiết kỹ thuật trong `docs/`; vault chỉ lưu bối cảnh, trạng thái, quyết định và đường dẫn.

## Điểm bắt đầu nhanh

- Repo: thư mục gốc NumberTyper đang mở trong Codex.
- Trạng thái: NumberTyper là ứng dụng Windows cục bộ, nhận audio tab bằng extension Chromium, ASR Zipformer-VI chạy local; chưa đạt nghiệm thu độ chính xác hoặc mục tiêu dưới 1 giây.
- Tài liệu kỹ thuật: [implementation status](../docs/IMPLEMENTATION_STATUS.md), [TikTok prototype](../docs/PROTOTYPE_TIKTOK_WEB.md), [browser compatibility](../docs/BROWSER_COMPATIBILITY.md), [ASR robustness](../docs/ASR_ROBUSTNESS.md), [installer sprint](../docs/SPRINT_P1_WINDOWS_INSTALLER.md).
