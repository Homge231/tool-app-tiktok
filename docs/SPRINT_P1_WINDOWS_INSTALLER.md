# Sprint P1 — Cài đặt và thiết lập NumberTyper trên Windows

**Trạng thái:** Đã dựng bản cài preview cá nhân; chưa nghiệm thu phát hành  
**Sản phẩm:** NumberTyper (tên package Python hiện tại vẫn là `pricetyper`)  
**Mục tiêu sprint:** Người dùng Windows cài ứng dụng bằng một bộ cài, mở từ lối tắt mà không cần tự cài Python hay chạy PowerShell, rồi làm theo hướng dẫn để kết nối tiện ích mở rộng với tab TikTok Live do họ chọn.

**Tiến độ MUST:** 1/11 hạng mục đạt điều kiện nghiệm thu là M1 (đã chốt phạm vi và ghi rõ tổ hợp trình duyệt chưa xác minh; điều này không có nghĩa browser đã được hỗ trợ). M2–M9 có phần triển khai hoặc tài liệu hoàn tất nhưng còn cổng nghiệm thu; M10 chưa chạy và M11 chưa qua cổng phát hành.

## Phạm vi và giả định

- Bản đầu nhắm tới Windows 10/11 64-bit. Sprint này không bao gồm macOS, Linux, điện thoại hay cam kết hỗ trợ mọi trình duyệt.
- Chỉ ghi một trình duyệt là “được hỗ trợ” sau khi kiểm tra đúng phiên bản, thu được âm thanh của tab đã chọn và thực hiện được thao tác trong chính tab đó. Chrome, Edge và Cốc Cốc hiện mới là ứng viên cần kiểm tra.
- Nhận dạng giọng nói (ASR) tiếp tục chạy ngoại tuyến; âm thanh chỉ ở trong bộ nhớ. Ứng dụng mở ở trạng thái chưa kích hoạt và chạy thử; mặc định chỉ điền số, không gửi.
- Sprint này tập trung vào bộ cài và quy trình thiết lập. Nó không cải thiện độ chính xác nhận dạng, không xác nhận mục tiêu dưới một giây và không bảo đảm TikTok hiển thị bình luận.
- P0/P0.1 và M8 vẫn chưa được nghiệm thu theo `docs/IMPLEMENTATION_STATUS.md`. `docs/SPEC.md` đặt P1 sau P0. Sprint này không được ghi nhận các mốc đó là hoàn tất. Có thể chuẩn bị/triển khai đóng gói, nhưng chỉ phát hành khi các cổng cần thiết đã qua.
- Bản phát hành cho người dùng phổ thông nên cài tiện ích mở rộng từ cửa hàng của trình duyệt. Tiện ích được nạp từ thư mục đã giải nén (unpacked) chỉ phù hợp cho phát triển và kiểm tra nội bộ, không phải quy trình phát hành cuối. Tham khảo [phân phối tiện ích mở rộng Chrome](https://developer.chrome.com/docs/extensions/how-to/distribute) và [phân phối tiện ích mở rộng Microsoft Edge](https://learn.microsoft.com/en-us/microsoft-edge/extensions/publish/hosting-and-updating).

## Backlog MoSCoW

MoSCoW phân loại mức ưu tiên của từng hạng mục trong sprint: **Must (Bắt buộc)** phải hoàn thành; **Should (Nên làm)** nên hoàn thành nếu không ảnh hưởng Must; **Could (Có thể làm)** là tùy chọn; **Won’t (Không làm)** được chủ động để ngoài sprint này.

### MUST — Bắt buộc để có bản cài Windows dùng được

| Mã | Công việc | Trạng thái hiện tại | Điều kiện nghiệm thu |
|---|---|---|---|
| M1 | Chốt phạm vi bản đầu: Windows 10/11 64-bit và trình duyệt/cửa hàng tiện ích mở rộng mục tiêu. Cập nhật ma trận tương thích làm nguồn thông tin chính thức duy nhất. | **Hoàn tất phạm vi** — Windows 10/11 64-bit và Chrome Web Store đã chọn cho kênh đầu; ma trận ghi rõ tổ hợp chưa xác minh. Chưa có browser nào được công bố là đã hỗ trợ. | Tên trình duyệt/phiên bản chỉ được quảng bá là hỗ trợ khi có kết quả kiểm tra; các tổ hợp chưa thử phải ghi rõ chưa xác minh hoặc không hỗ trợ. |
| M2 | Kiểm tra quyền phân phối và giấy phép của môi trường chạy Python, thư viện native, Zipformer-VI, VAD và các thành phần tiện ích mở rộng trước khi đóng gói. | **Một phần** — đã quét danh sách package trong PyInstaller Analysis, ghi 25 package Python, và loại nhóm PyAutoGUI/GPL khỏi bundle app; quyền của model ONNX và native closure/notices vẫn chưa xác minh đầy đủ. | Có SBOM tái lập theo đúng installer, ghi nguồn/giấy phép/quyền phân phối; mọi notice cần thiết có trong artifact. Không kèm thành phần chưa rõ quyền phân phối. |
| M3 | Tạo bản ứng dụng Windows có giao diện, kèm môi trường chạy Python, thư viện nhận dạng giọng nói/âm thanh native và các mô hình cần cho chế độ nhận dạng số TikTok. Đưa tài nguyên tiện ích mở rộng theo đúng phương án cài đã chọn. | **Một phần** — đã dựng lại bundle và installer sau khi loại dependency desktop không dùng; lần dựng mới chưa chạy executable/model smoke check và chưa cài thử. | Bản dựng mở được trên máy không có Python và không bật cửa sổ dòng lệnh; nạp được mô hình cục bộ; báo lỗi dễ hiểu nếu thiếu tài nguyên. Không đưa mô hình, log cá nhân hay âm thanh vào Git. |
| M4 | Tách tài nguyên chỉ đọc trong thư mục cài đặt khỏi cấu hình/log có thể ghi trong hồ sơ người dùng. Mọi đường dẫn mô hình/tiện ích mở rộng phải hoạt động dù ứng dụng được mở từ lối tắt hoặc thư mục có dấu cách. | **Một phần** — đường dẫn user-data và tài nguyên bundle đã tách; unit/path smoke check qua. Chưa xác minh bằng tài khoản sạch không có quyền quản trị. | Tài khoản không có quyền quản trị vẫn mở ứng dụng, ghi cấu hình/log đúng thư mục người dùng và nạp mô hình. Âm thanh thu được không lưu thành tệp. |
| M5 | Tạo bộ cài theo tài khoản người dùng, lối tắt trong Menu Bắt đầu, lựa chọn tạo lối tắt trên Màn hình nền và trình gỡ cài đặt. Hỗ trợ cài lại/nâng cấp mà không âm thầm xóa cấu hình. | **Một phần** — installer/shortcut/uninstaller đã tạo; bản cũ từng qua smoke install/uninstall. Smoke installer hiện tại từ chối chạy vì phát hiện cài đặt/shortcut sẵn có; chưa thử trên môi trường sạch và chưa kiểm nâng cấp bản hiện tại. | Cài, mở từ từng lối tắt, cài đè/nâng cấp và gỡ trên môi trường sạch đều hoạt động; người dùng không cần cài Python hay chạy PowerShell. |
| M6 | Tạo hướng dẫn thiết lập lần đầu: kiểm tra mô hình, cài/bật tiện ích mở rộng, mở Live, bắt âm thanh tab, kết nối và kiểm tra đúng tab. Hiển thị lỗi rõ khi thiếu tiện ích/mô hình, tab ngắt hoặc trình duyệt chưa hỗ trợ. | **Một phần** — wizard và hướng dẫn đã có; extension vẫn phải nạp thủ công, và luồng UI chưa được nghiệm thu với người dùng mới/máy sạch. | Người mới làm theo giao diện để tới trạng thái sẵn sàng nghe. Hướng dẫn không tự bật gửi, không tự kích hoạt thao tác và không đổi mặc định chỉ điền số. |
| M7 | Chuẩn bị tiện ích mở rộng cho kênh phát hành đầu tiên: chọn cửa hàng, chuẩn bị gói và nội dung trang giới thiệu, chốt ID tiện ích, khóa cầu kết nối vào đúng ID và mô tả quyền riêng tư/quyền truy cập. | **Một phần** — ZIP, ID nguồn, nội dung listing và bản nháp chính sách đã chuẩn bị; chưa có publisher account, URL listing hay lần gửi xét duyệt. | Cầu kết nối chỉ chấp nhận ID tiện ích đã duyệt; không phát hành với origin wildcard hiện tại. Trạng thái gửi xét duyệt/được duyệt được ghi lại; việc cửa hàng xét duyệt có thể là cổng bên ngoài sprint. |
| M8 | Giữ nguyên an toàn và riêng tư trong bản đóng gói: mặc định chạy thử/chưa kích hoạt, Enter cần lựa chọn đồng ý riêng, F8/F10, không thử gửi lại, không đọc chat/bình luận, nhận dạng ngoại tuyến, có cảnh báo lỗi khi chạy. | **Một phần** — kiểm soát an toàn và fake-page tests có trong mã; kiểm tra gói cài xác nhận dry-run không gọi sender thật chưa chạy. | Kiểm thử tự động chỉ dùng trang giả lập hoặc `NullSender`; kiểm tra bản đóng gói xác nhận không gọi bộ gửi thật khi chạy thử. |
| M9 | Viết hướng dẫn tiếng Việt ngắn cho cài đặt, thiết lập lần đầu, sử dụng, vị trí log và xử lý lỗi phổ biến. | **Một phần** — tài liệu tiếng Việt đã viết; chưa có lần hướng dẫn người dùng không rành kỹ thuật để xác nhận họ tự hoàn tất được. | Người không rành kỹ thuật không cần PowerShell để cài, mở, thêm tiện ích mở rộng từ kênh đã chọn, kết nối tab và tìm thông tin lỗi. |
| M10 | Kiểm tra trên tài khoản/máy Windows sạch không có Python và công cụ phát triển. Bao gồm cài đặt, lối tắt, khởi tạo mô hình, kết nối tiện ích mở rộng, trạng thái an toàn, cài lại và gỡ. | **Chưa làm** — chưa có tài khoản/VM Windows sạch được dùng cho kiểm tra nghiệm thu. | Ghi phiên bản Windows, trình duyệt/tiện ích, các bước và kết quả vào `docs/IMPLEMENTATION_STATUS.md` và `docs/BROWSER_COMPATIBILITY.md`. Kiểm thử trang giả lập không đủ để tuyên bố trình duyệt đã được hỗ trợ. |
| M11 | Giữ cổng phát hành riêng cho P0/P0.1 và M8: kiểm tra trạng thái nghiệm thu, thực hiện các phép kiểm tra còn thiếu cho tổ hợp trình duyệt ban đầu hoặc ghi rõ đây chỉ là bản thử nghiệm. | **Chưa qua cổng** — P0/P0.1, M8, độ chính xác ASR, browser acceptance và latency dưới 1 giây chưa được chấp nhận. | Không gọi bản cài là bản phát hành dùng được trên TikTok nếu chưa có bằng chứng thu âm thanh và thao tác cùng tab ở trình duyệt đã chọn. Không dùng livestream thật làm dữ liệu kiểm thử tự động. |

### SHOULD — Nên làm sau khi Must ổn định

| Mã | Công việc | Trạng thái hiện tại | Điều kiện nghiệm thu |
|---|---|---|---|
| S1 | Gửi tiện ích mở rộng lên cửa hàng Chromium thứ hai sau khi trang phát hành đầu có ID ổn định. | **Chưa làm** — chờ kênh đầu có ID/listing ổn định. | Phiên bản, trạng thái gửi xét duyệt và trạng thái phát hành được theo dõi riêng cho từng cửa hàng. |
| S2 | Nhận diện trình duyệt và thêm nút mở đúng trang cài tiện ích/hướng dẫn. | **Một phần** — wizard nhận diện một số Chromium và mở trang quản lý extension; chưa mở trang cửa hàng vì extension chưa được phát hành. | Không đánh dấu hỗ trợ chỉ dựa trên chuỗi user-agent hoặc việc trình duyệt có API Chromium. |
| S3 | Ký số bộ cài và tệp thực thi bằng chứng thư nhà phát hành. | **Chưa làm** — chưa có chứng thư/chữ ký phát hành. | Chữ ký trên gói cài đặt xác minh hợp lệ; không hứa hết cảnh báo SmartScreen nếu chưa quan sát trên máy người dùng. |
| S4 | Thêm quy trình cập nhật ứng dụng đơn giản, có phiên bản và ghi chú phát hành. | **Chưa làm** — chưa có updater. | Cập nhật không làm mất cấu hình người dùng; không tự cập nhật im lặng. |
| S5 | Thêm chức năng xuất gói chẩn đoán tối thiểu, chỉ gồm phiên bản ứng dụng, lỗi đã làm sạch và thông tin môi trường cần thiết. | **Chưa làm** — hiện chỉ có log cục bộ và hướng dẫn vị trí log. | Không chứa âm thanh, bản chép lời, bình luận, cookie, thông tin đăng nhập hay dữ liệu cá nhân. |

### COULD — Có thể làm nếu còn thời gian

| Mã | Công việc | Trạng thái hiện tại | Điều kiện nghiệm thu |
|---|---|---|---|
| C1 | Thêm trang kiểm tra mô hình/dung lượng đĩa trước khi khởi động nhận dạng giọng nói. | **Chưa làm**. | Thông tin dung lượng khớp với gói cài và trạng thái được kiểm tra thực tế. |
| C2 | Thêm nút sửa chữa để kiểm tra lại tài nguyên cài đặt và mở hướng dẫn. | **Chưa làm** — wizard hiện có chưa phải chức năng sửa chữa. | Không đặt lại cấu hình người dùng hoặc thay đổi trạng thái an toàn. |
| C3 | Chuẩn bị quy trình tạo máy ảo/bản chụp Windows sạch để lặp lại kiểm tra bộ cài. | **Chưa làm**. | Hướng dẫn có thể dựng lại môi trường kiểm tra mà không chạm vào tài khoản trình duyệt thật. |

### WON’T — Không làm trong sprint này

- Hỗ trợ Firefox, Safari, điện thoại hoặc tuyên bố tương thích với mọi trình duyệt.
- Thay đổi nhận dạng giọng nói/bộ phân tích số, thêm khử nhiễu/nhận diện người nói, hoặc tối ưu và cam kết độ chính xác hay thời gian dưới một giây.
- Tự cài tiện ích mở rộng im lặng vào trình duyệt bất kỳ hoặc né bước xác nhận/chính sách cửa hàng của trình duyệt.
- Gửi bình luận thật trong kiểm tra bộ cài; đọc nội dung chat/bình luận; dùng livestream thật làm dữ liệu kiểm thử tự động.
- Nhận dạng giọng nói qua đám mây, thu thập dữ liệu sử dụng, tự mua hàng, tự thử gửi lại hoặc né giới hạn tốc độ.

## Thứ tự thực hiện và phụ thuộc

1. **Chốt cổng phát hành:** chọn trình duyệt/cửa hàng đầu tiên; xác nhận tài khoản chủ trang phát hành; kiểm tra giấy phép mô hình và thư viện. Đây là các quyết định ảnh hưởng trực tiếp đến gói cài và không nên tự đoán.
2. **Đóng gói môi trường chạy:** tách đường dẫn tài nguyên/cấu hình, đóng gói giao diện cùng thư viện native, tạo gói dựng có thể tái tạo.
3. **Bộ cài và hướng dẫn lần đầu:** tạo bộ cài, lối tắt, trình gỡ cài đặt, hướng dẫn lần đầu, kiểm tra trạng thái tiện ích và tài liệu tiếng Việt.
4. **Kiểm chứng:** chạy kiểm tra khởi động gói dựng, kiểm tra bộ gửi bằng trang giả lập, cài trên môi trường Windows sạch; cập nhật tài liệu trạng thái và ma trận tương thích bằng kết quả thật.
5. **Quyết định phát hành:** chỉ phân phối sau khi quyền phân phối, cửa hàng tiện ích mở rộng và tổ hợp Windows/trình duyệt được chọn đều đạt cổng tương ứng.

## Điều kiện hoàn tất sprint

- Tài khoản Windows sạch không cài Python có thể cài và mở NumberTyper từ lối tắt, không dùng PowerShell.
- Ứng dụng khởi tạo được mô hình nhận dạng số cục bộ và ghi cấu hình/log trong hồ sơ người dùng.
- Hướng dẫn lần đầu giúp người dùng cài tiện ích mở rộng từ cửa hàng đã chọn và kết nối đúng tab; ứng dụng không chuyển sang dùng microphone hoặc âm thanh toàn hệ thống.
- Ứng dụng vẫn khởi động ở chế độ chạy thử/chưa kích hoạt, mặc định chỉ điền số, và giữ các điều khiển/cảnh báo hiện có.
- Giấy phép, bộ cài, tiện ích mở rộng và tuyên bố hỗ trợ trình duyệt có bằng chứng. P0/P0.1, M8, độ chính xác số và mục tiêu dưới một giây được báo cáo riêng theo kết quả kiểm tra thực tế.

## Trạng thái hiện tại

### Tình trạng triển khai — 2026-10-21

| Nhóm | Tình trạng | Bằng chứng / phần còn thiếu |
|---|---|---|
| M1 | Hoàn tất phạm vi | Windows 10/11 64-bit và Chrome Web Store được chọn; ma trận tương thích ghi rõ các tổ hợp chưa được kiểm tra. Đây là hoàn tất phạm vi và tài liệu, không phải browser acceptance. |
| M2 | Một phần | `docs/THIRD_PARTY_NOTICES.md` có danh sách 25 gói Python được PyInstaller thu vào build mới. Nhóm desktop automation có GPL trong metadata đã bị loại khỏi app bundle. Chưa hoàn thành native dependency closure, đủ license text/notices, SBOM artifact cuối, hay quyền phân phối model ONNX. |
| M3 | Đã dựng lại, chưa smoke check | PyInstaller one-directory và NSIS installer đã được dựng lại sau thay đổi packaging. Lần build mới chưa chạy executable/model smoke check, chưa cài đặt hoặc kiểm trên Windows sạch. |
| M4 | Một phần | Tài nguyên trong bundle chỉ đọc; cấu hình, log và trạng thái hướng dẫn ở `%LOCALAPPDATA%\NumberTyper`. Unit test path và smoke check qua working directory khác đã qua; tài khoản sạch không quyền quản trị chưa được kiểm tra. |
| M5 | Một phần | Installer NSIS per-user, shortcut Start Menu, chọn shortcut Desktop, đăng ký gỡ cài và giữ user data. Previous build đã qua smoke install/uninstall; bản dựng hiện tại chưa chạy smoke install vì tài khoản đã có cài đặt/shortcut và script từ chối ghi đè. Chưa có máy/tài khoản sạch. |
| M6 | Một phần | Wizard tiếng Việt dò Edge/Chrome/Cốc Cốc, mở trang quản lý extension của trình duyệt đã chọn, mở hoặc sao chép thư mục extension; hướng dẫn ghi rõ dry-run phải tắt trước F8. Extension vẫn nạp thủ công vì chưa có listing store. Unit test helper qua; chưa kiểm tra thao tác UI trên tài khoản sạch. |
| M7 | Một phần | Có script tạo ZIP extension, ID từ manifest key `bjhbdndjhpiakgohbjdpclikllfnecjp`, nội dung listing và draft chính sách riêng tư. ZIP chưa được gửi xét duyệt; chưa có publisher account, URL listing hoặc trạng thái duyệt. |
| M8 | Có trong mã, chưa nghiệm thu gói trên Live | Safety và fake-page tests giữ nguyên. Smoke installer không mở TikTok và không dựng sender thật. Chưa có kiểm tra thủ công audio/action ở browser sau thay đổi gói. |
| M9 | Một phần | Hướng dẫn cài/thiết lập, dữ liệu cục bộ, log, giới hạn và xử lý lỗi bằng tiếng Việt đã viết; chưa xác nhận người dùng mới tự hoàn tất được. |
| M10 | Chưa làm | Chưa có Windows/tài khoản sạch không công cụ phát triển; smoke test mới của installer từ chối chạy do đã phát hiện cài đặt/shortcut NumberTyper hiện có. |
| M11 | Chưa qua cổng | P0/P0.1, M8, ASR accuracy, browser acceptance và mục tiêu comment dưới 1 giây vẫn chưa được chấp nhận. |

Artefact cục bộ hiện tại: `dist/NumberTyper-Setup-0.1.0-preview.exe`, SHA-256 `4362B29E28BED3A14FAF69744F577646D3EB3C0DACF2714B40CC991EB3EAEA2D`; extension store package: `dist/NumberTyper-Tab-Audio-0.1.0.zip`, SHA-256 `7C1402F77A9648F9749580EC50D5536B8E19CAA140ABAADC3BC7BA7669BC95F6`. Bản app là preview cá nhân phi thương mại; chưa sẵn sàng phát hành công khai hoặc lên store. Các kiểm tra và giới hạn chi tiết ở `docs/IMPLEMENTATION_STATUS.md` và `docs/BROWSER_COMPATIBILITY.md`.
