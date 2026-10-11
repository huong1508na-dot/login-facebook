import os
import re
import sys
import threading

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")
import time
import tkinter as tk
from tkinter import messagebox
from urllib.parse import quote_plus

import customtkinter as ctk
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from uid_checker import UidCheckerTab


APP_NAME = "Facebook Cookie Login"
APP_VERSION = "2.5"
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
        self.geometry("980x720")
        self.minsize(880, 640)

        self.drivers = []
        self.group_results = []
        self.group_select_vars = {}
        self.review_queue = []
        self.review_index = -1
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<F8>", lambda _event: self.join_current_group())
        self.bind("<F9>", lambda _event: self.open_next_review_group())

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()
        self._build_footer()

    def _build_header(self):
        header = ctk.CTkFrame(self, corner_radius=0, height=108)
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
        logo.grid(row=0, column=0, rowspan=2, padx=(28, 16), pady=24)

        title = ctk.CTkLabel(
            header,
            text="Facebook Session Toolkit",
            anchor="w",
            font=ctk.CTkFont(size=25, weight="bold"),
        )
        title.grid(row=0, column=1, sticky="sw", pady=(24, 0))

        subtitle = ctk.CTkLabel(
            header,
            text="Cookie login • Group Finder • Local-only",
            anchor="w",
            text_color=("gray40", "gray70"),
            font=ctk.CTkFont(size=13),
        )
        subtitle.grid(row=1, column=1, sticky="nw", pady=(3, 22))

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
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=20)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.tabs = ctk.CTkTabview(body, corner_radius=18)
        self.tabs.grid(row=0, column=0, sticky="nsew")

        login_tab = self.tabs.add("Đăng nhập")
        groups_tab = self.tabs.add("Tìm Group")
        checker_tab = self.tabs.add("Check LIVE")

        login_tab.grid_columnconfigure(0, weight=1)
        login_tab.grid_rowconfigure(1, weight=1)
        groups_tab.grid_columnconfigure(0, weight=1)
        groups_tab.grid_rowconfigure(3, weight=1)

        self._build_login_tab(login_tab)
        self._build_groups_tab(groups_tab)
        self.uid_checker = UidCheckerTab(checker_tab)

    def _build_login_tab(self, parent):
        info = ctk.CTkFrame(parent, corner_radius=16)
        info.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 12))
        info.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            info,
            text="Dán cookie của tài khoản bạn",
            anchor="w",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 3))

        ctk.CTkLabel(
            info,
            text="Định dạng: c_user=...; xs=...; datr=...;  •  Cookie không được lưu vào file.",
            anchor="w",
            text_color=("gray40", "gray70"),
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 14))

        editor = ctk.CTkFrame(parent, corner_radius=18)
        editor.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
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

        ctk.CTkButton(
            editor_top,
            text="Dán từ clipboard",
            width=138,
            height=34,
            corner_radius=10,
            command=self.paste_cookie,
        ).grid(row=0, column=1, padx=(8, 8))

        ctk.CTkButton(
            editor_top,
            text="Xóa",
            width=72,
            height=34,
            corner_radius=10,
            fg_color=("gray75", "gray28"),
            hover_color=("gray68", "gray34"),
            command=self.clear_cookie,
        ).grid(row=0, column=2)

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

    def _build_groups_tab(self, parent):
        search_card = ctk.CTkFrame(parent, corner_radius=16)
        search_card.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 12))
        search_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            search_card,
            text="Group Finder",
            anchor="w",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(16, 2))

        ctk.CTkLabel(
            search_card,
            text=(
                "Tìm group theo chủ đề và gom kết quả để bạn xem trước. "
                "Tool không tự bấm Join và không né quy trình kiểm duyệt của group."
            ),
            anchor="w",
            justify="left",
            wraplength=820,
            text_color=("gray40", "gray70"),
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, columnspan=4, sticky="ew", padx=20, pady=(0, 12))

        self.group_keyword = ctk.CTkEntry(
            search_card,
            placeholder_text="Ví dụ: đồ công nghệ, du lịch, AI, ô tô...",
            height=40,
        )
        self.group_keyword.grid(row=2, column=0, sticky="ew", padx=(20, 10), pady=(0, 16))

        ctk.CTkLabel(
            search_card,
            text="Số lượng",
            font=ctk.CTkFont(size=12),
        ).grid(row=2, column=1, padx=(0, 6), pady=(0, 16))

        self.group_limit = ctk.CTkEntry(search_card, width=70, height=40)
        self.group_limit.insert(0, "20")
        self.group_limit.grid(row=2, column=2, padx=(0, 10), pady=(0, 16))

        self.group_scan_btn = ctk.CTkButton(
            search_card,
            text="Quét Group",
            width=130,
            height=40,
            corner_radius=11,
            command=self.start_group_scan,
        )
        self.group_scan_btn.grid(row=2, column=3, padx=(0, 20), pady=(0, 16))

        action_bar = ctk.CTkFrame(parent, fg_color="transparent")
        action_bar.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        action_bar.grid_columnconfigure(1, weight=1)

        self.group_count_label = ctk.CTkLabel(
            action_bar,
            text="Chưa có kết quả",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.group_count_label.grid(row=0, column=0, sticky="w")

        self.group_status = ctk.CTkLabel(
            action_bar,
            text="Đăng nhập Facebook trước, sau đó nhập chủ đề để quét.",
            anchor="e",
            text_color=("gray40", "gray70"),
            font=ctk.CTkFont(size=11),
        )
        self.group_status.grid(row=0, column=1, sticky="e", padx=(10, 10))

        ctk.CTkButton(
            action_bar,
            text="Mở tìm kiếm",
            width=104,
            height=32,
            corner_radius=10,
            fg_color=("gray75", "gray28"),
            hover_color=("gray68", "gray34"),
            command=self.open_group_search,
        ).grid(row=0, column=2, sticky="e", padx=(4, 4))

        ctk.CTkButton(
            action_bar,
            text="Chọn tất cả",
            width=96,
            height=32,
            corner_radius=10,
            fg_color=("gray75", "gray28"),
            hover_color=("gray68", "gray34"),
            command=self.select_all_groups,
        ).grid(row=0, column=3, sticky="e", padx=4)

        ctk.CTkButton(
            action_bar,
            text="Bỏ chọn",
            width=82,
            height=32,
            corner_radius=10,
            fg_color=("gray75", "gray28"),
            hover_color=("gray68", "gray34"),
            command=self.clear_group_selection,
        ).grid(row=0, column=4, sticky="e", padx=4)

        self.review_start_btn = ctk.CTkButton(
            action_bar,
            text="Duyệt đã chọn",
            width=112,
            height=32,
            corner_radius=10,
            command=self.start_selected_review,
        )
        self.review_start_btn.grid(row=0, column=5, sticky="e", padx=4)

        self.review_next_btn = ctk.CTkButton(
            action_bar,
            text="Nhóm tiếp theo",
            width=118,
            height=32,
            corner_radius=10,
            state="disabled",
            command=self.open_next_review_group,
        )
        self.review_next_btn.grid(row=0, column=6, sticky="e", padx=(4, 0))

        assist_bar = ctk.CTkFrame(parent, corner_radius=14)
        assist_bar.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))
        assist_bar.grid_columnconfigure(0, weight=1)

        self.join_current_btn = ctk.CTkButton(
            assist_bar,
            text="Tham gia nhóm hiện tại  •  F8",
            height=48,
            corner_radius=12,
            font=ctk.CTkFont(size=15, weight="bold"),
            state="disabled",
            command=self.join_current_group,
        )
        self.join_current_btn.grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=12)

        ctk.CTkLabel(
            assist_bar,
            text="F9 = nhóm tiếp theo",
            width=120,
            text_color=("gray45", "gray65"),
            font=ctk.CTkFont(size=11),
        ).grid(row=0, column=1, padx=(6, 12), pady=12)

        self.group_results_frame = ctk.CTkScrollableFrame(
            parent,
            corner_radius=16,
            label_text="Kết quả tìm thấy",
        )
        self.group_results_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=14,
            pady=(0, 14),
        )
        self.group_results_frame.grid_columnconfigure(0, weight=1)

        self._render_empty_group_state()

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

    def navigate_with_timeout(self, driver, url, timeout=30):
        driver.set_page_load_timeout(timeout)
        try:
            driver.get(url)
            return True
        except TimeoutException:
            try:
                driver.execute_script("window.stop();")
            except Exception:
                pass
            return False

    def wait_for_document(self, driver, timeout=8):
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState")
                in ("interactive", "complete")
            )
            return True
        except Exception:
            return False

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
            driver.set_script_timeout(15)
            self.drivers.append(driver)

            self.after(
                0,
                lambda: self.set_status(
                    "Chrome đã mở. Đang nạp cookie vào facebook.com...",
                    "busy",
                ),
            )

            loaded_home = self.navigate_with_timeout(driver, FACEBOOK_URL, timeout=30)
            self.wait_for_document(driver, timeout=6)

            accepted = 0
            rejected = 0
            accepted_names = set()

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
                    accepted_names.add(cookie["name"])
                except Exception:
                    rejected += 1

            if accepted == 0:
                raise RuntimeError(
                    "Chrome không chấp nhận cookie nào. Hãy kiểm tra lại định dạng."
                )

            required = {"c_user", "xs"}
            missing_required = sorted(required - accepted_names)
            if missing_required:
                raise RuntimeError(
                    "Thiếu cookie phiên cần thiết hoặc Chrome không nhận: "
                    + ", ".join(missing_required)
                    + "."
                )

            self.after(
                0,
                lambda: self.set_status(
                    f"Đã nạp {accepted} cookie. Đang kiểm tra phiên đăng nhập...",
                    "busy",
                ),
            )

            profile_loaded = self.navigate_with_timeout(
                driver,
                "https://www.facebook.com/me/",
                timeout=30,
            )
            self.wait_for_document(driver, timeout=8)
            current = (driver.current_url or "").lower()

            blocked_markers = (
                "checkpoint",
                "two_step_verification",
                "login/identify",
                "recover/",
            )

            if any(marker in current for marker in blocked_markers):
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
            elif not driver.get_cookie("c_user"):
                text = (
                    "Cookie c_user đã bị Facebook/Chrome loại bỏ sau khi kiểm tra. "
                    "Phiên đăng nhập không còn hợp lệ."
                )
                kind = "warning"
            else:
                timeout_note = " • trang tải chậm" if not (loaded_home and profile_loaded) else ""
                text = (
                    f"Đăng nhập hợp lệ • cookie nhận: {accepted}"
                    + (f" • bỏ qua: {rejected}" if rejected else "")
                    + timeout_note
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
            error_text = str(exc)
            self.after(
                0,
                lambda error_text=error_text: messagebox.showerror(
                    "Không thể đăng nhập",
                    error_text,
                ),
            )
            self.after(0, lambda: self.set_status("Không thể nạp cookie", "error"))

            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

        finally:
            self.after(0, self.finish_login_ui)

    def get_active_driver(self):
        for driver in reversed(self.drivers):
            try:
                _ = driver.current_url
                return driver
            except Exception:
                continue
        return None

    def _get_group_settings(self):
        keyword = self.group_keyword.get().strip()
        if not keyword:
            raise ValueError("Hãy nhập chủ đề cần tìm.")

        try:
            limit = int(self.group_limit.get().strip())
        except ValueError as exc:
            raise ValueError("Số lượng phải là số nguyên.") from exc

        if limit < 1 or limit > 100:
            raise ValueError("Số lượng hỗ trợ từ 1 đến 100.")

        return keyword, limit

    def _group_search_url(self, keyword):
        return f"https://www.facebook.com/search/groups/?q={quote_plus(keyword)}"

    def open_group_search(self):
        driver = self.get_active_driver()
        if not driver:
            messagebox.showinfo(
                "Chưa có phiên Facebook",
                "Hãy đăng nhập Facebook ở tab Đăng nhập trước.",
            )
            return

        try:
            keyword, _ = self._get_group_settings()
        except ValueError as exc:
            messagebox.showwarning("Thiếu thông tin", str(exc))
            return

        try:
            driver.get(self._group_search_url(keyword))
            self.group_status.configure(text="Đã mở trang tìm kiếm Facebook.")
        except Exception as exc:
            messagebox.showerror("Không mở được tìm kiếm", str(exc))

    def start_group_scan(self):
        driver = self.get_active_driver()
        if not driver:
            messagebox.showinfo(
                "Chưa có phiên Facebook",
                "Hãy đăng nhập Facebook ở tab Đăng nhập trước.",
            )
            return

        try:
            keyword, limit = self._get_group_settings()
        except ValueError as exc:
            messagebox.showwarning("Thiếu thông tin", str(exc))
            return

        self.group_scan_btn.configure(state="disabled", text="Đang quét...")
        self.group_status.configure(text="Đang tải kết quả và gom các group hiển thị...")
        self.group_count_label.configure(text="Đang quét...")

        threading.Thread(
            target=self.group_scan_worker,
            args=(driver, keyword, limit),
            daemon=True,
        ).start()

    def _group_relevance_score(self, name, context, keyword):
        terms = [
            term.casefold()
            for term in re.findall(r"\w+", keyword, flags=re.UNICODE)
            if len(term) >= 2
        ]
        name_cf = (name or "").casefold()
        context_cf = (context or "").casefold()

        score = 0
        for term in terms:
            if term in name_cf:
                score += 4
            elif term in context_cf:
                score += 1
        return score

    def _group_visibility_from_context(self, context):
        text = (context or "").casefold()
        public_markers = ("công khai", "public group", "public")
        private_markers = ("riêng tư", "private group", "private")

        if any(marker in text for marker in public_markers):
            return "Công khai"
        if any(marker in text for marker in private_markers):
            return "Riêng tư"
        return "Không rõ"

    def group_scan_worker(self, driver, keyword, limit):
        try:
            search_url = self._group_search_url(keyword)
            driver.get(search_url)
            time.sleep(2.0)

            groups = {}
            stagnant_rounds = 0
            last_count = 0
            candidate_target = min(max(limit * 2, limit), 100)
            max_rounds = min(max(10, candidate_target // 3 + 4), 40)

            for _ in range(max_rounds):
                anchors = driver.find_elements(By.CSS_SELECTOR, "a[href*='/groups/']")

                for anchor in anchors:
                    try:
                        href = anchor.get_attribute("href") or ""
                        label = " ".join((anchor.text or "").split())

                        context = ""
                        try:
                            context = driver.execute_script(
                                """
                                let e = arguments[0];
                                let parts = [];
                                for (let i = 0; i < 4 && e; i++, e = e.parentElement) {
                                    if (e.innerText) parts.push(e.innerText);
                                }
                                return parts.join(" | ");
                                """,
                                anchor,
                            ) or ""
                        except Exception:
                            context = ""

                        match = re.search(
                            r"^https://(?:www\.)?facebook\.com/groups/([^/?#]+)",
                            href,
                        )
                        if not match:
                            continue

                        group_id = match.group(1)
                        if group_id.lower() in {
                            "feed",
                            "discover",
                            "create",
                            "search",
                            "groups",
                        }:
                            continue

                        root_url = f"https://www.facebook.com/groups/{group_id}/"

                        if root_url not in groups:
                            name = label or f"Facebook Group {group_id}"
                            groups[root_url] = {
                                "name": name,
                                "context": context,
                                "order": len(groups),
                            }
                        elif label and len(label) > len(groups[root_url]["name"]):
                            groups[root_url]["name"] = label
                            if context:
                                groups[root_url]["context"] = context

                        if len(groups) >= candidate_target:
                            break
                    except Exception:
                        continue

                if len(groups) >= candidate_target:
                    break

                if len(groups) == last_count:
                    stagnant_rounds += 1
                else:
                    stagnant_rounds = 0

                if stagnant_rounds >= 3:
                    break

                last_count = len(groups)
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(1.25)

            ranked = []
            for url, meta in groups.items():
                visibility = self._group_visibility_from_context(meta["context"])
                relevance = self._group_relevance_score(
                    meta["name"],
                    meta["context"],
                    keyword,
                )
                visibility_rank = {
                    "Công khai": 0,
                    "Không rõ": 1,
                    "Riêng tư": 2,
                }.get(visibility, 1)

                ranked.append(
                    {
                        "name": meta["name"],
                        "url": url,
                        "visibility": visibility,
                        "relevance": relevance,
                        "order": meta["order"],
                        "_sort": (
                            visibility_rank,
                            -relevance,
                            meta["order"],
                        ),
                    }
                )

            ranked.sort(key=lambda item: item["_sort"])
            results = ranked[:limit]

            for item in results:
                item.pop("_sort", None)

            self.after(0, lambda: self.render_group_results(results))
            self.after(
                0,
                lambda: self.group_status.configure(
                    text=(
                        f"Đã xếp {len(results)} group: ưu tiên Công khai khi Facebook "
                        "hiển thị rõ, sau đó theo độ khớp chủ đề và thứ tự Facebook."
                    )
                ),
            )

        except Exception as exc:
            error_text = str(exc)
            self.after(
                0,
                lambda error_text=error_text: messagebox.showerror(
                    "Quét group thất bại",
                    error_text,
                ),
            )
            self.after(
                0,
                lambda: self.group_status.configure(
                    text="Không thể đọc kết quả tìm kiếm Facebook."
                ),
            )
        finally:
            self.after(
                0,
                lambda: self.group_scan_btn.configure(
                    state="normal",
                    text="Quét Group",
                ),
            )

    def _render_empty_group_state(self):
        for widget in self.group_results_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.group_results_frame,
            text="Chưa có group nào được quét.",
            text_color=("gray45", "gray60"),
            font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, pady=24)

    def render_group_results(self, results):
        self.group_results = results
        self.group_select_vars = {}
        self.review_queue = []
        self.review_index = -1
        self.review_next_btn.configure(state="disabled")
        self.join_current_btn.configure(state="disabled")

        for widget in self.group_results_frame.winfo_children():
            widget.destroy()

        if not results:
            self.group_count_label.configure(text="0 group")
            self._render_empty_group_state()
            return

        self.group_count_label.configure(text=f"{len(results)} group")

        for index, group in enumerate(results, start=1):
            row = ctk.CTkFrame(self.group_results_frame, corner_radius=12)
            row.grid(row=index - 1, column=0, sticky="ew", padx=4, pady=5)
            row.grid_columnconfigure(2, weight=1)

            selected_var = tk.BooleanVar(value=False)
            self.group_select_vars[group["url"]] = selected_var

            ctk.CTkCheckBox(
                row,
                text="",
                width=24,
                variable=selected_var,
                command=self.update_selected_group_status,
            ).grid(row=0, column=0, rowspan=2, padx=(10, 4), pady=10)

            ctk.CTkLabel(
                row,
                text=str(index),
                width=34,
                height=34,
                corner_radius=10,
                fg_color=("gray82", "gray24"),
                font=ctk.CTkFont(size=12, weight="bold"),
            ).grid(row=0, column=1, rowspan=2, padx=(4, 10), pady=10)

            ctk.CTkLabel(
                row,
                text=group["name"],
                anchor="w",
                justify="left",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).grid(row=0, column=2, sticky="ew", pady=(10, 1))

            detail_text = group["url"]
            visibility = group.get("visibility")
            if visibility:
                detail_text = f"{visibility}  •  {detail_text}"

            ctk.CTkLabel(
                row,
                text=detail_text,
                anchor="w",
                text_color=("gray45", "gray62"),
                font=ctk.CTkFont(size=10),
            ).grid(row=1, column=2, sticky="ew", pady=(0, 10))

            ctk.CTkButton(
                row,
                text="Mở",
                width=72,
                height=34,
                corner_radius=10,
                command=lambda url=group["url"]: self.open_group(url),
            ).grid(row=0, column=3, rowspan=2, padx=12, pady=10)

    def update_selected_group_status(self):
        selected = sum(
            1 for var in self.group_select_vars.values() if var.get()
        )
        total = len(self.group_results)
        self.group_count_label.configure(
            text=f"{total} group • đã chọn {selected}"
        )

    def select_all_groups(self):
        for var in self.group_select_vars.values():
            var.set(True)
        self.update_selected_group_status()

    def clear_group_selection(self):
        for var in self.group_select_vars.values():
            var.set(False)
        self.review_queue = []
        self.review_index = -1
        self.review_next_btn.configure(state="disabled")
        self.join_current_btn.configure(state="disabled")
        self.update_selected_group_status()

    def start_selected_review(self):
        selected_urls = {
            url for url, var in self.group_select_vars.items() if var.get()
        }
        self.review_queue = [
            group for group in self.group_results if group["url"] in selected_urls
        ]
        self.review_index = -1

        if not self.review_queue:
            messagebox.showinfo(
                "Chưa chọn group",
                "Hãy tick các group muốn duyệt trước.",
            )
            return

        self.review_next_btn.configure(state="normal")
        self.join_current_btn.configure(state="normal")
        self.open_next_review_group()

    def open_next_review_group(self):
        if not self.review_queue:
            self.review_next_btn.configure(state="disabled")
            self.join_current_btn.configure(state="disabled")
            return

        self.review_index += 1
        if self.review_index >= len(self.review_queue):
            self.review_next_btn.configure(state="disabled")
            self.join_current_btn.configure(state="disabled")
            self.group_status.configure(
                text="Đã duyệt hết các group đã chọn."
            )
            messagebox.showinfo(
                "Hoàn tất",
                "Bạn đã duyệt hết danh sách group đã chọn.",
            )
            return

        group = self.review_queue[self.review_index]
        driver = self.get_active_driver()
        if not driver:
            messagebox.showinfo(
                "Chưa có phiên Facebook",
                "Phiên Chrome đã đóng. Hãy đăng nhập lại.",
            )
            self.review_next_btn.configure(state="disabled")
            self.join_current_btn.configure(state="disabled")
            return

        try:
            driver.get(group["url"])
            self.wait_for_document(driver, timeout=8)
            self.join_current_btn.configure(state="normal")
            self.group_status.configure(
                text=(
                    f"Đang duyệt {self.review_index + 1}/{len(self.review_queue)}: "
                    f"{group['name']}. Nhấn F8 hoặc nút lớn để tham gia; "
                    "sau đó nhấn F9 hoặc Nhóm tiếp theo."
                )
            )
        except Exception as exc:
            messagebox.showerror("Không mở được group", str(exc))


    def _find_visible_button_by_labels(self, driver, labels):
        lowered = {label.casefold() for label in labels}

        candidates = driver.find_elements(
            By.XPATH,
            "//*[@role='button' or self::button]",
        )

        for element in candidates:
            try:
                text = " ".join((element.text or "").split()).casefold()
                aria = " ".join(
                    (element.get_attribute("aria-label") or "").split()
                ).casefold()

                if (text in lowered or aria in lowered) and element.is_displayed():
                    if element.is_enabled():
                        return element
            except Exception:
                continue

        return None

    def join_current_group(self):
        if self.review_index < 0 or self.review_index >= len(self.review_queue):
            messagebox.showinfo(
                "Chưa có group đang duyệt",
                "Hãy chọn group và bấm Duyệt đã chọn trước.",
            )
            return

        driver = self.get_active_driver()
        if not driver:
            messagebox.showinfo(
                "Chưa có phiên Facebook",
                "Phiên Chrome đã đóng. Hãy đăng nhập lại.",
            )
            return

        current_url = (driver.current_url or "").lower()
        if "facebook.com/groups/" not in current_url:
            messagebox.showwarning(
                "Không ở trang group",
                "Chrome hiện không ở trang Facebook Group. Hãy mở group đang duyệt trước.",
            )
            return

        self.join_current_btn.configure(
            state="disabled",
            text="Đang tìm nút Join...",
        )

        threading.Thread(
            target=self._join_current_group_worker,
            args=(driver,),
            daemon=True,
        ).start()

    def _join_current_group_worker(self, driver):
        try:
            already_labels = (
                "Đã tham gia",
                "Joined",
                "Đã gửi yêu cầu",
                "Request sent",
                "Đang chờ",
                "Pending",
            )
            join_labels = (
                "Tham gia nhóm",
                "Tham gia",
                "Join group",
                "Join",
            )

            self.wait_for_document(driver, timeout=8)

            already = self._find_visible_button_by_labels(
                driver,
                already_labels,
            )
            if already:
                self.after(
                    0,
                    lambda: self.group_status.configure(
                        text=(
                            "Group hiện tại đã tham gia hoặc yêu cầu đang chờ. "
                            "Bạn có thể chuyển sang nhóm tiếp theo."
                        )
                    ),
                )
                return

            join_button = None
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: self._find_visible_button_by_labels(
                        d,
                        join_labels,
                    )
                    is not None
                )
                join_button = self._find_visible_button_by_labels(
                    driver,
                    join_labels,
                )
            except Exception:
                pass

            if not join_button:
                self.after(
                    0,
                    lambda: messagebox.showwarning(
                        "Không tìm thấy nút Join",
                        (
                            "Tool không tìm thấy nút Tham gia trên group này. "
                            "Có thể bạn đã tham gia, group không cho tham gia trực tiếp, "
                            "hoặc giao diện Facebook đã thay đổi."
                        ),
                    ),
                )
                return

            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    join_button,
                )
                time.sleep(0.25)
                driver.execute_script("arguments[0].click();", join_button)
            except Exception:
                join_button.click()

            time.sleep(0.8)

            self.after(
                0,
                lambda: self.group_status.configure(
                    text=(
                        "Đã bấm Join cho group hiện tại. "
                        "Nếu Facebook hiện câu hỏi/điều khoản, hãy xử lý trong Chrome; "
                        "sau đó bấm Nhóm tiếp theo hoặc F9."
                    )
                ),
            )

        except Exception as exc:
            error_text = str(exc)
            self.after(
                0,
                lambda error_text=error_text: messagebox.showerror(
                    "Không thể bấm Join",
                    error_text,
                ),
            )
        finally:
            self.after(
                0,
                lambda: self.join_current_btn.configure(
                    state="normal",
                    text="Tham gia nhóm hiện tại  •  F8",
                ),
            )

    def open_group(self, url):
        driver = self.get_active_driver()
        if not driver:
            messagebox.showinfo(
                "Chưa có phiên Facebook",
                "Phiên Chrome đã đóng. Hãy đăng nhập lại.",
            )
            return

        try:
            driver.execute_script("window.open(arguments[0], '_blank');", url)
            self.group_status.configure(
                text="Đã mở group trong tab mới. Bạn có thể kiểm tra rồi bấm Join thủ công."
            )
        except Exception as exc:
            messagebox.showerror("Không mở được group", str(exc))

    def on_close(self):
        for driver in list(self.drivers):
            try:
                driver.quit()
            except Exception:
                pass

        self.destroy()


def run_self_test():
    sample = "c_user=12345; xs=abc%3Axyz; datr=test;"
    parsed = parse_cookie_header(sample)
    names = {item["name"] for item in parsed}
    return 0 if {"c_user", "xs", "datr"}.issubset(names) else 1


def run_chrome_self_test():
    driver = None
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)
        driver.get("data:text/html,<title>ok</title><p>chrome-self-test</p>")
        return 0 if driver.title == "ok" else 2
    except Exception as exc:
        try:
            with open("chrome-self-test-error.txt", "w", encoding="utf-8") as handle:
                handle.write(f"{type(exc).__name__}: {exc}")
        except Exception:
            pass
        return 1
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(run_self_test())

    if "--chrome-self-test" in sys.argv:
        raise SystemExit(run_chrome_self_test())

    app = FacebookCookieLoginApp()
    app.mainloop()
