# Facebook Cookie Login v2

Ứng dụng Windows có giao diện hiện đại để nạp **cookie của chính tài khoản Facebook bạn** vào Google Chrome và mở phiên đăng nhập cục bộ.

## Bản v2 có gì mới?

- Giao diện dark mode bằng CustomTkinter.
- Nút **Dán từ clipboard** và **Xóa**.
- Hiển thị số cookie nhận được.
- Thanh trạng thái và hiệu ứng xử lý khi mở Chrome.
- Tùy chọn mở Chrome ẩn danh.
- Tự đóng các phiên Chrome do ứng dụng mở khi thoát app.
- Không lưu cookie ra file.
- Có script và GitHub Actions để build Windows EXE.

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
