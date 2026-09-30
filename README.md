# Facebook Cookie Login - Local

Ứng dụng Python có giao diện để nạp **cookie của chính tài khoản Facebook bạn** vào Google Chrome và mở Facebook.

## Tính năng

- Giao diện đơn giản bằng Tkinter.
- Nhận cookie dạng: `c_user=...; xs=...; datr=...;`
- Mở Google Chrome bằng Selenium.
- Nạp cookie trực tiếp vào phiên Chrome trên máy.
- Không lưu cookie ra file.
- Phát hiện sơ bộ khi Facebook chuyển về trang đăng nhập hoặc checkpoint.
- Không vượt CAPTCHA, checkpoint hoặc 2FA.

## Yêu cầu

- Windows 10/11
- Python 3.10+ khuyến nghị
- Google Chrome
- Kết nối Internet

Selenium 4 có Selenium Manager, vì vậy thông thường không cần tự tải ChromeDriver.

## Cách chạy nhanh

1. Tải repo về máy hoặc chọn **Code > Download ZIP**.
2. Giải nén.
3. Chạy `run.bat`.
4. Dán cookie của tài khoản bạn.
5. Nhấn **Login Facebook**.

Hoặc chạy bằng terminal:

```bash
python -m pip install -r requirements.txt
python main.py
```

## Định dạng cookie

Ví dụ cấu trúc:

```text
c_user=YOUR_VALUE; xs=YOUR_VALUE; datr=YOUR_VALUE;
```

Không đăng cookie thật lên GitHub, chat công khai hoặc gửi cho người khác. Cookie phiên có thể cấp quyền truy cập tài khoản tương tự một phiên đăng nhập.

## Lưu ý bảo mật

Công cụ này chỉ dành cho tài khoản bạn sở hữu hoặc được phép quản lý. Ứng dụng không có chức năng lấy cookie từ máy khác, đánh cắp phiên đăng nhập, vượt checkpoint, CAPTCHA hay 2FA.

Nếu Facebook yêu cầu xác minh, hãy hoàn tất trực tiếp trong cửa sổ Chrome.
