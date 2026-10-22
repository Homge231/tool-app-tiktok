# Hồ sơ chuẩn bị cửa hàng — NumberTyper Tab Audio

Trạng thái: bản nháp nội bộ, chưa gửi xét duyệt. Kênh đầu tiên dự kiến: Chrome Web Store. Cần xác nhận lại ID sau khi publisher tạo mục extension trên cửa hàng; không coi việc dựng ZIP là đã phát hành.

## Thông tin trang giới thiệu

- **Tên:** NumberTyper Tab Audio
- **Mô tả ngắn:** Chuyển audio từ tab bạn chọn tới NumberTyper chạy cục bộ trên máy để nhận dạng số tiếng Việt.
- **Mục đích chính:** Cầu nối audio và thao tác giữa tab Chromium do người dùng chủ động chọn với ứng dụng NumberTyper trên cùng máy tính.
- **Phân loại dự kiến:** Công cụ / Năng suất.
- **Ngôn ngữ:** Tiếng Việt; giao diện có thể hiển thị một số nhãn tiếng Anh tùy trình duyệt.
- **Phiên bản nguồn:** `0.1.0`.
- **ID suy ra từ `manifest.key` hiện tại:** `bjhbdndjhpiakgohbjdpclikllfnecjp`.
- **Ảnh chụp cửa hàng:** Chưa tạo; cần ảnh từ bản dựng được kiểm tra, không dùng ảnh mô phỏng.
- **Dự thảo chính sách riêng tư:** [`PRIVACY_POLICY_VI_DRAFT.md`](PRIVACY_POLICY_VI_DRAFT.md). Chưa được host công khai; cần điền thông tin liên hệ và rà soát trước khi submit.

## Mô tả dài dự thảo

NumberTyper Tab Audio kết nối tab trình duyệt do bạn chủ động chọn với ứng dụng NumberTyper đang chạy trên chính máy tính. Ứng dụng desktop xử lý tiếng Việt và trích số tại chỗ bằng model cục bộ.

Bạn tự bắt đầu và dừng việc thu audio từ tab. Extension chuyển các khung audio tới ứng dụng cục bộ qua địa chỉ loopback trên máy (`127.0.0.1`); audio không được gửi tới dịch vụ đám mây. Trong chế độ TikTok thử nghiệm, extension có thể điền số theo dạng `@<số>` (ví dụ `@122`) vào ô nhập của cùng tab sau khi bạn chủ động kết nối. Gửi bằng Enter cần bật riêng trong ứng dụng và kích hoạt bằng F8. Mặc định ứng dụng chạy thử/chưa kích hoạt và chỉ điền `@<số>`. Kết quả nhận dạng có thể sai; extension không xác nhận rằng TikTok đã nhận hoặc hiển thị bình luận.

Extension không đọc danh sách bình luận, nội dung chat, cookie, mật khẩu hoặc thông tin đăng nhập. Không dùng extension để tự mua hàng hoặc tự động thanh toán.

## Quyền cần giải trình

| Quyền | Lý do trong sản phẩm |
|---|---|
| `tabCapture` | Lấy audio của tab sau thao tác chủ động trong popup; không bật microphone hoặc audio toàn hệ thống. |
| `activeTab` | Xác định tab đang được người dùng chọn sau khi bấm extension. |
| `offscreen` | Giữ luồng audio/worklet chạy trong Manifest V3 khi popup đóng. |
| `scripting` | Thực hiện probe thuộc tính của ô nhập hiển thị và thao tác số đã yêu cầu trong cùng tab TikTok Live. Không đọc giá trị ô, chat hay bình luận. |
| `storage` | Lưu trạng thái capture tối thiểu giữa popup, service worker và offscreen document. |
| Host `http://127.0.0.1/*` | Kết nối WebSocket tới NumberTyper trên cùng máy; không kết nối máy chủ bên ngoài. |

## Khai báo dữ liệu dự thảo

- **Âm thanh:** Được chuyển tới ứng dụng NumberTyper cục bộ chỉ sau khi người dùng bắt đầu capture; xử lý trong bộ nhớ, không ghi thành tệp bởi extension.
- **Thông tin tab:** Tab ID, host và path được gửi tới ứng dụng loopback để khóa capture và thao tác vào đúng tab. Không gửi sang nhà phát triển.
- **Nội dung trang:** Probe chỉ đọc thuộc tính của input hiển thị. Khi có yêu cầu điền số, extension đọc riêng nội dung của chính input đó để từ chối ghi đè bản nháp và xác nhận văn bản `@<số>` vừa điền; không lấy danh sách/nội dung chat hoặc bình luận, cookie hay credential.
- **Thu thập, bán hoặc chia sẻ dữ liệu:** Bản nháp khai báo là không thu thập, không bán và không chia sẻ dữ liệu với nhà phát triển hay bên thứ ba. Cần đối chiếu lại với phiên bản đã phát hành và yêu cầu biểu mẫu cửa hàng trước khi nộp.
- **Xử lý:** ASR chạy trong ứng dụng desktop. Không có API speech cloud trong sản phẩm hiện tại.

## Cổng trước khi gửi xét duyệt

1. Publisher tạo mục extension và xác nhận ID cửa hàng khớp `bjhbdndjhpiakgohbjdpclikllfnecjp`; nếu khác, phải cập nhật identity/bridge và dựng lại trước khi phát hành.
2. Đăng chính sách riêng tư công khai và điền chính xác các câu hỏi data-use trong Console.
3. Rà soát giấy phép model/runtime và SBOM của bộ cài desktop; extension store listing không làm hết cổng giấy phép của app.
4. Chạy kiểm tra capture tab và fake-page action trên trình duyệt mục tiêu; không dùng livestream thật làm fixture tự động.
5. Tạo ảnh chụp thật, gửi xét duyệt, ghi lại ngày và trạng thái. Chỉ sau khi được duyệt mới thay hướng dẫn cài thủ công bằng liên kết cửa hàng.

ZIP dựng cục bộ bằng `scripts/package_browser_extension.ps1`. ZIP là artefact tải lên để xét duyệt, không phải extension đã cài hay được cửa hàng chấp thuận.
