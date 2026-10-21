# Cài NumberTyper Preview trên Windows

## Phạm vi bản preview

Bản này dành cho Windows 10/11 64-bit, chạy nhận dạng Zipformer-VI cục bộ và đi kèm extension để lấy âm thanh đúng tab trình duyệt. Extension hiện chưa có trên cửa hàng nên cần nạp thủ công một lần. Wizard thiết lập có thể mở trang extension của Edge, Chrome hoặc một Chromium khác đã chọn, mở thư mục extension và sao chép đường dẫn. Trình duyệt vẫn không tự cài extension. Tổ hợp chưa có trong `docs/BROWSER_COMPATIBILITY.md` vẫn chưa được xác nhận hỗ trợ.

> **Lưu ý giấy phép:** gói Zipformer-VI đi kèm được công bố theo CC BY-NC-ND 4.0. Bản preview này chỉ dành cho sử dụng cá nhân, phi thương mại. Không dùng gói này cho hoạt động kinh doanh hoặc phát hành thương mại khi chưa có quyền phù hợp. Xem `THIRD_PARTY_NOTICES.md`.

## Cài và mở

1. Mở `NumberTyper-Setup-0.1.0-preview.exe`.
2. Cài theo hướng dẫn. Không cần cài Python hay chạy PowerShell.
3. Có thể chọn tạo shortcut ngoài Desktop; shortcut trong Menu Bắt đầu luôn được tạo.
4. Ở lần mở đầu, chọn đúng trình duyệt rồi bấm **Mở trang tiện ích**. Bấm **Mở thư mục tiện ích** để mở thư mục extension; có thể dùng **Sao chép đường dẫn**.

## Nạp extension thủ công

Trong trình duyệt Chromium mà bạn muốn thử:

1. Tại trang quản lý extension vừa mở, bật **Chế độ nhà phát triển**.
2. Chọn **Nạp tiện ích đã giải nén** (Load unpacked).
3. Chọn thư mục extension mà NumberTyper vừa mở.
4. Mở một trang TikTok Live. Bấm biểu tượng NumberTyper trên thanh extension rồi bấm **Bắt đầu thu tab này**.
5. Trở lại NumberTyper và bấm **Kết nối tab TikTok đang nghe** để kiểm tra tab/ô nhập.

Extension chỉ cấp âm thanh của tab đã chọn và yêu cầu thao tác số quay lại đúng tab đó. Nếu capture dừng, bấm F10 nếu cần dừng ngay, kết nối lại extension rồi kiểm tra tab. Không đổi sang microphone hay âm thanh toàn máy.

## Chế độ an toàn

- Ứng dụng khởi động ở chế độ chạy thử/chưa kích hoạt. Nó không tự điền hoặc gửi comment.
- Sau khi tab đã được kiểm tra, F8 bật thao tác số; F10 dừng khẩn.
- Mặc định chỉ điền số vào ô chat. Gửi bằng Enter cần bật lựa chọn riêng trong ứng dụng.
- Enter chỉ được xác nhận là đã phát lệnh; ứng dụng không xác nhận comment đã xuất hiện trên TikTok.
- Không dùng livestream thật trong kiểm thử tự động.

## Dữ liệu cục bộ và gỡ cài đặt

Cấu hình và log nằm tại `%LOCALAPPDATA%\NumberTyper`. Log có thể chứa bản chép lời/số nhận dạng và thông tin trạng thái; audio tab chỉ xử lý trong bộ nhớ, không ghi thành tệp. Gỡ ứng dụng không xóa cấu hình/log để tránh mất dữ liệu; tự xóa thư mục trên nếu bạn muốn xóa chúng.

Mở **Cài đặt → Ứng dụng → Ứng dụng đã cài đặt → NumberTyper → Gỡ cài đặt**, hoặc chạy mục gỡ trong thư mục cài. Bản cài không yêu cầu quyền quản trị.

## Nếu có lỗi

- Không mở được: xem `%LOCALAPPDATA%\NumberTyper\logs\startup.log` và `crash.log`.
- Extension không kết nối: kiểm tra extension đang bật, đúng trình duyệt, đúng tab TikTok Live và cổng localhost không bị chặn.
- Không có audio: xác nhận đã bấm **Bắt đầu thu tab này** trên chính tab đang phát; âm thanh phải phát ra từ tab đó.
- Mất tab hoặc cảnh báo quá tải: ứng dụng sẽ khóa thao tác để tránh dùng transcript bị đứt. Kết nối lại và kiểm tra trạng thái trước khi bật F8.

## Giới hạn đã biết

Độ chính xác tiếng Việt khi có nhạc, nhiều giọng nói hoặc giọng chồng lấp chưa được nghiệm thu. Mục tiêu comment xuất hiện dưới 1 giây cũng chưa được đo/chấp nhận. Hiện chưa có kiểm thử trên tài khoản Windows sạch, extension chưa có bản phát hành store, và extension vẫn cần nạp thủ công. Cốc Cốc là lựa chọn thiết lập trong wizard nhưng chưa được nghiệm thu tương thích.
