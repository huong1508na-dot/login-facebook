import threading
import tkinter as tk
from tkinter import messagebox, ttk

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options


FACEBOOK_URL = "https://www.facebook.com/"


def parse_cookie_header(raw: str):
    """Parse a standard Cookie header: name=value; name2=value2."""
    cookies = []
    for part in raw.replace("\n", ";").split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        name = name.strip()
        value = value.strip()
        if name:
            cookies.append({"name": name, "value": value})
    return cookies


class FacebookCookieLoginApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Facebook Cookie Login - Local")
        self.root.geometry("760x520")
        self.root.minsize(680, 460)

        self.drivers = []

        frame = ttk.Frame(root, padding=18)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Facebook Cookie Login",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            frame,
            text=(
                "Dùng cookie của chính tài khoản bạn. Cookie chỉ được nạp vào Chrome "
                "trên máy này và không được lưu bởi ứng dụng."
            ),
            wraplength=700,
        ).pack(anchor="w", pady=(6, 14))

        ttk.Label(
            frame,
            text="Dán cookie dạng: c_user=...; xs=...; datr=...;",
        ).pack(anchor="w")

        self.cookie_text = tk.Text(frame, height=14, wrap="word")
        self.cookie_text.pack(fill="both", expand=True, pady=(6, 12))

        options_frame = ttk.Frame(frame)
        options_frame.pack(fill="x")

        self.incognito = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Mở Chrome ẩn danh",
            variable=self.incognito,
        ).pack(side="left")

        self.login_btn = ttk.Button(
            options_frame,
            text="Login Facebook",
            command=self.start_login,
        )
        self.login_btn.pack(side="right")

        self.clear_btn = ttk.Button(
            options_frame,
            text="Xóa cookie",
            command=lambda: self.cookie_text.delete("1.0", "end"),
        )
        self.clear_btn.pack(side="right", padx=(0, 8))

        self.status = tk.StringVar(value="Sẵn sàng")
        ttk.Label(frame, textvariable=self.status).pack(anchor="w", pady=(12, 0))

        ttk.Separator(frame).pack(fill="x", pady=12)
        ttk.Label(
            frame,
            text=(
                "Ứng dụng không vượt checkpoint, CAPTCHA hoặc 2FA. Nếu Facebook yêu cầu "
                "xác minh, hãy hoàn tất trực tiếp trong cửa sổ Chrome."
            ),
            wraplength=700,
        ).pack(anchor="w")

    def start_login(self):
        raw = self.cookie_text.get("1.0", "end").strip()
        cookies = parse_cookie_header(raw)

        if not cookies:
            messagebox.showerror(
                "Cookie không hợp lệ",
                "Không tìm thấy cookie dạng name=value.",
            )
            return

        self.login_btn.config(state="disabled")
        self.status.set(f"Đã đọc {len(cookies)} cookie. Đang mở Chrome...")

        use_incognito = bool(self.incognito.get())
        thread = threading.Thread(
            target=self.login_worker,
            args=(cookies, use_incognito),
            daemon=True,
        )
        thread.start()

    def login_worker(self, cookies, use_incognito):
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            if use_incognito:
                chrome_options.add_argument("--incognito")

            driver = webdriver.Chrome(options=chrome_options)
            self.drivers.append(driver)

            # Selenium chỉ cho phép add_cookie sau khi đã ở đúng domain.
            driver.get(FACEBOOK_URL)

            accepted = 0
            rejected = 0
            for cookie in cookies:
                payload = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": ".facebook.com",
                    "path": "/",
                }
                try:
                    driver.add_cookie(payload)
                    accepted += 1
                except Exception:
                    # Một số cookie có thuộc tính/định dạng Chrome không chấp nhận.
                    rejected += 1

            if accepted == 0:
                raise RuntimeError(
                    "Chrome không chấp nhận cookie nào. Hãy kiểm tra lại định dạng."
                )

            driver.get("https://www.facebook.com/me/")

            current = driver.current_url.lower()
            if "login" in current:
                result = (
                    "Cookie đã được nạp nhưng Facebook chuyển về trang đăng nhập. "
                    "Cookie có thể đã hết hạn."
                )
            elif "checkpoint" in current:
                result = (
                    "Facebook yêu cầu checkpoint/xác minh. "
                    "Hãy hoàn tất thủ công trong Chrome."
                )
            else:
                result = "Đã nạp cookie và mở Facebook."

            details = f"{result} Thành công: {accepted}, bỏ qua: {rejected}."
            self.root.after(0, lambda: self.status.set(details))

        except WebDriverException as exc:
            msg = (
                "Không mở được Chrome. Hãy chắc chắn Google Chrome đã được cài và "
                f"thử lại.\n\nChi tiết: {exc}"
            )
            self.root.after(0, lambda: messagebox.showerror("Lỗi Chrome", msg))
            self.root.after(0, lambda: self.status.set("Lỗi khi mở Chrome"))
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        except Exception as exc:
            self.root.after(
                0,
                lambda: messagebox.showerror("Không thể đăng nhập", str(exc)),
            )
            self.root.after(0, lambda: self.status.set("Không thể nạp cookie"))
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        finally:
            self.root.after(0, lambda: self.login_btn.config(state="normal"))


if __name__ == "__main__":
    root = tk.Tk()
    app = FacebookCookieLoginApp(root)
    root.mainloop()
