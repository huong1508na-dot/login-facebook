# Facebook Session Toolkit v2.1

Ứng dụng Windows có giao diện hiện đại để nạp **cookie của chính tài khoản Facebook bạn** vào Google Chrome và mở phiên đăng nhập cục bộ.

## Bản v2 có gì mới?

- Giao diện dark mode bằng CustomTkinter.
- Nút **Dán từ clipboard** và **Xóa**.
- Hiển thị số cookie nhận được.
- Thanh trạng thái và hiệu ứng xử lý khi mở Chrome.
- Tùy chọn mở Chrome ẩn danh.
- Tự đóng các phiên Chrome do ứng dụng mở khi thoát app.
- Không lưu cookie ra file.
- Có script và GitHub Actions để build Windows EXE.\n- Có tab **Tìm Group**: nhập chủ đề, chọn 1–100 kết quả, quét group đang hiển thị và mở từng group để duyệt thủ công.

## Cách dùng bản Python

1. Cài Google Chrome.
2. Cài Python 3.10+.
3. Chạy `run.bat`.
4. Dán cookie dạng:
   `c_user=...; xs=...; datr=...;`
5. Nhấn **Đăng nhập Facebook**.

## Build file EXE trên Windows

Chạy:

```text
build_exe.bat
```

Sau khi build thành công, file nằm tại:

```text
dist\FacebookCookieLogin.exe
```

EXE được build dạng một file và không hiện cửa sổ console.

## Build tự động bằng GitHub Actions

Workflow `Build Windows EXE` tự chạy khi các file ứng dụng chính thay đổi.

Vào tab **Actions** → chọn lần chạy **Build Windows EXE** → tải artifact:

```text
FacebookCookieLogin-Windows
```

Artifact chứa `FacebookCookieLogin.exe`.

## Lưu ý bảo mật

- Chỉ sử dụng cookie của tài khoản bạn sở hữu hoặc được phép quản lý.
- Không đăng cookie thật lên GitHub, chat công khai hoặc gửi cho người khác.
- Cookie phiên có thể cấp quyền truy cập tài khoản tương tự một phiên đăng nhập.
- Ứng dụng không có chức năng lấy cookie từ máy khác.
- Ứng dụng không vượt checkpoint, CAPTCHA hoặc 2FA.
- Nếu Facebook yêu cầu xác minh, hãy hoàn tất trực tiếp trong Chrome.

## Yêu cầu

- Windows 10/11
- Google Chrome
- Internet
- Với bản EXE đã build: không cần cài Python để chạy ứng dụng.


## Group Finder

1. Đăng nhập Facebook ở tab **Đăng nhập**.
2. Chuyển sang tab **Tìm Group**.
3. Nhập chủ đề cần tìm.
4. Chọn số lượng từ 1 đến 100.
5. Nhấn **Quét Group**.
6. Tool sẽ cuộn trang tìm kiếm, gom các group Facebook đang hiển thị và đưa vào danh sách.
7. Nhấn **Mở** để kiểm tra từng group và tự quyết định có tham gia hay không.

Group Finder không tự gửi yêu cầu Join hàng loạt và không có chức năng né kiểm duyệt/luật đăng bài của group.


## Chọn nhiều group để duyệt

Sau khi quét group:

1. Tick những group bạn quan tâm hoặc dùng **Chọn tất cả**.
2. Nhấn **Duyệt đã chọn**.
3. Tool mở group đầu tiên trong Chrome.
4. Bạn kiểm tra nội dung/quy định và bấm **Join** thủ công nếu muốn.
5. Quay lại tool và nhấn **Nhóm tiếp theo**.
6. Lặp lại cho đến hết danh sách đã chọn.

Tool không tự gửi yêu cầu tham gia hàng loạt; mỗi lần tham gia vẫn do bạn xác nhận trực tiếp trên Facebook.


## Chế độ hỗ trợ thao tác (v2.3)

Khi đang duyệt danh sách group đã chọn:

- **F8** hoặc nút **Tham gia nhóm hiện tại**: tool tìm nút Join trên đúng trang Facebook Group và bấm giúp bạn.
- Nếu group hiện câu hỏi, điều khoản hoặc bước xác nhận bổ sung, xử lý trực tiếp trong Chrome.
- **F9** hoặc **Nhóm tiếp theo**: chuyển sang group kế tiếp.

Chế độ này giảm thao tác chuột xuống mức tối thiểu nhưng vẫn cần một xác nhận của bạn cho từng group.


## Check LIVE Facebook (nhánh feature/uid-live-checker, v2.5)

- Tab mới **Check LIVE** bên cạnh **Đăng nhập** và **Tìm Group**. Luồng Chrome/Selenium cũ vẫn giữ nguyên.
- Nhập TXT hoặc CSV, mỗi dòng có thể là `UID`, `UID|Cookie`, `UID,Cookie`. Chỉ lấy UID dạng số; dữ liệu Cookie bị loại bỏ ngay khi nhập, không được gửi tới API hoặc xuất ra CSV.
- Danh sách giới hạn 10.000 UID duy nhất. Có thể gán nhãn nguồn `NoVerify` hoặc `Verify` bằng menu (đây là nhãn người dùng chọn, tool **không tự xác thực** tình trạng verify).
- Điền API Key có quyền `checker:read` và `checker:write` vào giao diện, sau đó nhấn **Bắt đầu check UID**. Key chỉ nằm trong bộ nhớ ứng dụng, không ghi vào repo hay file xuất.
- Đọc `GET /checker/capabilities` để điều chỉnh số UID mỗi đợt (tối đa mặc định 50); `POST /checker/checks` có Idempotency-Key mới; `GET /checker/checks/{check_id}` cho kết quả bất đồng bộ. Có tiến độ, tạm dừng, dừng và chạy lại các kết quả UNKNOWN/API_ERROR.
- Kết quả phân loại `LIVE`, `UNKNOWN`, `API_ERROR`, `CHƯA KIỂM TRA`. API hiện **không chứng minh được DIE**, không thể kết luận cookie còn đăng nhập được hay tài khoản đã vượt checkpoint.
- Xuất CSV gồm UID, nhãn nhóm, trạng thái UID và thời gian; không có Cookie.

Tham khảo tài liệu API từ nhà cung cấp: https://accinsfb.com/client/api-docs.
API bên thứ ba chưa được kiểm nghiệm độc lập; cần tự đăng ký quyền và API Key, thử với bộ UID có sự đồng ý trước khi sử dụng rộng rãi. Không nhập Cookie vào bất kỳ dịch vụ trực tuyến nào.

### Test nhanh

```bash
python main.py --self-test
```

Kiểm tra này chỉ xác nhận parsing UID và Cookie mẫu giả; **chưa kiểm thử API với Key thật, UI Windows hoặc bản build EXE**. Không merge vào main cho đến khi kiểm thử các phần trên.
