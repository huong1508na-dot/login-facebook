import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options


APP_NAME = "Facebook Cookie Login"
APP_VERSION = "2.0"
FACEBOOK_URL = "https://www.facebook.com/"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


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


class FacebookCookieLoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("920x650")
        self.minsize(820, 590)

        self.drivers = []
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()
        self._build_footer()

    def _build_header(self):
        header = ctk.CTkFrame(self, corner_radius=0, height=112)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        logo = ctk.CTkLabel(
            header,
            text="f",
            width=58,
            height=58,
            corner_radius=18,
            fg_color=("#1877F2", "#1877F2"),
            text_color="white",
            font=ctk.CTkFont(size=38, weight="bold"),
        )
        logo.grid(row=0, column=0, rowspan=2, padx=(28, 16), pady=26)

        title = ctk.CTkLabel(
            header,
            text="Facebook Cookie Login",
            anchor="w",
            font=ctk.CTkFont(size=25, weight="bold"),
        )
        title.grid(row=0, column=1, sticky="sw", pady=(26, 0))

        subtitle = ctk.CTkLabel(
            header,
            text="Local session launcher • Cookie không được lưu vào file",
            anchor="w",
            text_color=("gray40", "gray70"),
            font=ctk.CTkFont(size=13),
        )
        subtitle.grid(row=1, column=1, sticky="nw", pady=(3, 24))

        version = ctk.CTkLabel(
            header,
            text=f"v{APP_VERSION}",
            width=54,
            height=28,
            corner_radius=14,
            fg_color=("gray85", "gray22"),
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        version.grid(row=0, column=2, rowspan=2, padx=(10, 28))

    def _build_content(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=26, pady=22)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        info = ctk.CTkFrame(body, corner_radius=16)
        info.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        info.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            info,
            text="Dán cookie của tài khoản bạn",
            anchor="w",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 3))

        ctk.CTkLabel(
            info,
            text="Định dạng hỗ trợ: c_user=...; xs=...; datr=...;  •  Không gửi cookie lên server.",
            anchor="w",
            text_color=("gray40", "gray70"),
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 14))

        editor = ctk.CTkFrame(body, corner_radius=18)
        editor.grid(row=1, column=0, sticky="nsew")
        editor.grid_columnconfigure(0, weight=1)
        editor.grid_rowconfigure(1, weight=1)

        editor_top = ctk.CTkFrame(editor, fg_color="transparent")
        editor_top.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 10))
        editor_top.grid_columnconfigure(0, weight=1)

        self.cookie_counter = ctk.CTkLabel(
            editor_top,
            text="0 cookie",
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.cookie_counter.grid(row=0, column=0, sticky="w")

        paste_btn = ctk.CTkButton(
            editor_top,
            text="Dán từ clipboard",
            width=138,
            height=34,
            corner_radius=10,
            command=self.paste_cookie,
        )
        paste_btn.grid(row=0, column=1, padx=(8, 8))

        clear_btn = ctk.CTkButton(
            editor_top,
            text="Xóa",
            width=72,
            height=34,
            corner_radius=10,
            fg_color=("gray75", "gray28"),
            hover_color=("gray68", "gray34"),
            command=self.clear_cookie,
        )
        clear_btn.grid(row=0, column=2)

        self.cookie_text = ctk.CTkTextbox(
            editor,
            corner_radius=12,
            border_width=1,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
        )
        self.cookie_text.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=18,
            pady=(0, 14),
        )
        self.cookie_text.bind("<KeyRelease>", self.update_cookie_counter)

        controls = ctk.CTkFrame(editor, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 17))
        controls.grid_columnconfigure(1, weight=1)

        self.incognito = ctk.CTkSwitch(
            controls,
            text="Chrome ẩn danh",
            onvalue=True,
            offvalue=False,
        )
        self.incognito.grid(row=0, column=0, sticky="w")
        self.incognito.select()

        self.login_btn = ctk.CTkButton(
            controls,
            text="Đăng nhập Facebook",
            width=190,
            height=44,
            corner_radius=12,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_login,
        )
        self.login_btn.grid(row=0, column=2, sticky="e")

        self.progress = ctk.CTkProgressBar(editor, mode="indeterminate")
        self.progress.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 18))
        self.progress.set(0)

    def _build_footer(self):
        footer = ctk.CTkFrame(self, corner_radius=0, height=56)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        self.status_dot = ctk.CTkLabel(
            footer,
            text="●",
            width=22,
            text_color=("#2DA44E", "#3FB950"),
            font=ctk.CTkFont(size=13),
        )
        self.status_dot.grid(row=0, column=0, padx=(26, 4), pady=16)

        self.status = ctk.CTkLabel(
            footer,
            text="Sẵn sàng",
            anchor="w",
            text_color=("gray35", "gray72"),
            font=ctk.CTkFont(size=12),
        )
        self.status.grid(row=0, column=1, sticky="ew", pady=16)

        security = ctk.CTkLabel(
            footer,
            text="Không vượt checkpoint / CAPTCHA / 2FA",
            text_color=("gray42", "gray62"),
            font=ctk.CTkFont(size=11),
        )
        security.grid(row=0, column=2, padx=(10, 26), pady=16)

    def set_status(self, text: str, kind: str = "normal"):
        colors = {
            "normal": ("#2DA44E", "#3FB950"),
            "busy": ("#1877F2", "#58A6FF"),
            "warning": ("#BF8700", "#D29922"),
            "error": ("#CF222E", "#F85149"),
        }
        self.status.configure(text=text)
        self.status_dot.configure(text_color=colors.get(kind, colors["normal"]))

    def update_cookie_counter(self, _event=None):
        raw = self.cookie_text.get("1.0", "end").strip()
        count = len(parse_cookie_header(raw))
        self.cookie_counter.configure(text=f"{count} cookie")

    def paste_cookie(self):
        try:
            value = self.clipboard_get()
        except tk.TclError:
            messagebox.showinfo("Clipboard trống", "Không có nội dung văn bản trong clipboard.")
            return

        self.cookie_text.delete("1.0", "end")
        self.cookie_text.insert("1.0", value.strip())
        self.update_cookie_counter()
        self.set_status("Đã dán cookie từ clipboard")

    def clear_cookie(self):
        self.cookie_text.delete("1.0", "end")
        self.update_cookie_counter()
        self.set_status("Đã xóa nội dung cookie")

    def start_login(self):
        raw = self.cookie_text.get("1.0", "end").strip()
        cookies = parse_cookie_header(raw)

        if not cookies:
            messagebox.showerror(
                "Cookie không hợp lệ",
                "Không tìm thấy cookie dạng name=value.",
            )
            return

        use_incognito = bool(self.incognito.get())

        self.login_btn.configure(state="disabled", text="Đang mở Chrome...")
        self.progress.start()
        self.set_status(f"Đã đọc {len(cookies)} cookie. Đang khởi tạo Chrome...", "busy")

        threading.Thread(
            target=self.login_worker,
            args=(cookies, use_incognito),
            daemon=True,
        ).start()

    def finish_login_ui(self):
        self.progress.stop()
        self.progress.set(0)
        self.login_btn.configure(state="normal", text="Đăng nhập Facebook")

    def login_worker(self, cookies, use_incognito):
        driver = None

        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")

            if use_incognito:
                chrome_options.add_argument("--incognito")

            driver = webdriver.Chrome(options=chrome_options)
            self.drivers.append(driver)

            self.after(
                0,
                lambda: self.set_status(
                    "Chrome đã mở. Đang nạp cookie vào facebook.com...",
                    "busy",
                ),
            )

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
                    rejected += 1

            if accepted == 0:
                raise RuntimeError(
                    "Chrome không chấp nhận cookie nào. Hãy kiểm tra lại định dạng."
                )

            self.after(
                0,
                lambda: self.set_status(
                    f"Đã nạp {accepted} cookie. Đang kiểm tra phiên đăng nhập...",
                    "busy",
                ),
            )

            driver.get("https://www.facebook.com/me/")
            current = driver.current_url.lower()

            if "checkpoint" in current:
                text = (
                    "Facebook yêu cầu checkpoint/xác minh. "
                    "Hãy hoàn tất trực tiếp trong Chrome."
                )
                kind = "warning"
            elif "login" in current:
                text = (
                    "Facebook chuyển về trang đăng nhập. "
                    "Cookie có thể đã hết hạn hoặc không còn hợp lệ."
                )
                kind = "warning"
            else:
                text = (
                    f"Đã mở Facebook • cookie nhận: {accepted}"
                    + (f" • bỏ qua: {rejected}" if rejected else "")
                )
                kind = "normal"

            self.after(0, lambda: self.set_status(text, kind))

        except WebDriverException as exc:
            short_error = str(exc).splitlines()[0] if str(exc) else "WebDriver error"
            self.after(
                0,
                lambda: messagebox.showerror(
                    "Không mở được Chrome",
                    "Hãy kiểm tra Google Chrome và kết nối Internet.\n\n"
                    f"Chi tiết: {short_error}",
                ),
            )
            self.after(0, lambda: self.set_status("Không mở được Chrome", "error"))

            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

        except Exception as exc:
            self.after(
                0,
                lambda: messagebox.showerror("Không thể đăng nhập", str(exc)),
            )
            self.after(0, lambda: self.set_status("Không thể nạp cookie", "error"))

            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

        finally:
            self.after(0, self.finish_login_ui)

    def on_close(self):
        for driver in list(self.drivers):
            try:
                driver.quit()
            except Exception:
                pass

        self.destroy()


if __name__ == "__main__":
    app = FacebookCookieLoginApp()
    app.mainloop()
