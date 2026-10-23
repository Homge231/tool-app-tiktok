# Dự thảo chính sách quyền riêng tư — NumberTyper

**Trạng thái:** dự thảo nội bộ, chưa được đăng công khai hoặc gửi cửa hàng. Trước khi phát hành, nhà phát hành cần điền thông tin liên hệ, host trang chính sách và rà soát nội dung theo đúng phiên bản ứng dụng/extension được phát hành.

## Dữ liệu extension xử lý

NumberTyper Tab Audio chỉ bắt đầu thu audio sau khi người dùng chủ động chọn tab và bấm nút bắt đầu trong extension. Extension chuyển audio của tab qua kết nối loopback `127.0.0.1` tới ứng dụng NumberTyper trên cùng máy. Extension không gửi audio tới máy chủ của nhà phát triển hoặc dịch vụ nhận dạng đám mây, và không ghi raw audio thành tệp.

Extension chuyển tab ID, hostname và đường dẫn của tab tới ứng dụng cục bộ để khóa audio và thao tác vào đúng tab. Khi được yêu cầu điền số, extension đọc nội dung của chính ô nhập đã chọn để thay bản nháp số; khi gửi, extension kiểm tra văn bản `@<số>` đã được điền. Nó không lấy danh sách hoặc nội dung bình luận/chat, cookie, mật khẩu hay thông tin đăng nhập.

Ứng dụng desktop xử lý âm thanh bằng model local. Ứng dụng có thể ghi transcript/số nhận dạng và trạng thái lỗi vào log cục bộ theo cấu hình; người dùng có thể xóa log trong `%LOCALAPPDATA%\NumberTyper\logs`. Raw audio không được lưu thành file bởi pipeline nhận dạng.

## Chia sẻ, bán và lưu giữ

- Nhà phát hành không nhận dữ liệu qua máy chủ trong thiết kế hiện tại.
- Dữ liệu capture/state chỉ cần thiết trong lúc chạy và được giữ cục bộ.
- Không bán dữ liệu, không quảng cáo theo dõi, không dùng analytics từ xa.
- Extension không có máy chủ tài khoản hoặc chức năng đồng bộ đám mây.

## Quyền của extension

`tabCapture` lấy audio của tab được chọn; `activeTab` xác định tab sau thao tác người dùng; `offscreen` duy trì luồng xử lý audio; `scripting` probe ô nhập hiển thị và điền số thô hoặc comment `@<số>` theo chế độ được chọn; `storage` giữ trạng thái capture tối thiểu; quyền host `http://127.0.0.1/*` kết nối tới app cục bộ.

## Thao tác TikTok

Chế độ TikTok là thử nghiệm. Ứng dụng khởi động ở trạng thái chạy thử/chưa kích hoạt. Sau khi kiểm tra tab, người dùng chọn chỉ điền liên tục số thô để thay bản nháp cũ hoặc gửi bằng Enter; khi gửi, số nhận dạng được định dạng `@<số>` (ví dụ `12` thành `@12`). Thao tác cần F8. Extension không xác nhận TikTok đã nhận hoặc hiển thị bình luận. Kết quả nhận dạng có thể sai.

## Liên hệ và cập nhật

Trước khi công bố, thay dòng này bằng email/hình thức liên hệ của nhà phát hành. Cập nhật ngày hiệu lực và phiên bản extension tương ứng khi chính sách thay đổi.
