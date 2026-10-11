"""UID-only Facebook checker integration.

Only numeric UIDs are transmitted. Authentication cookies are never inspected
remotely, submitted to this API, or included in exported results.
"""
import csv
import io
import json
import re
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import customtkinter as ctk

API_BASE = "https://accinsfb.com/api/v1"
UID_RE = re.compile(r"^\s*(\d{5,20})(?=\s|[|,;]|$)")


def parse_uids(text):
    """Accept UID, UID|cookie, UID,cookie and CSV; discard cookie data."""
    found, seen = [], set()
    invalid = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        match = UID_RE.match(line.lstrip("\ufeff"))
        if not match:
            invalid += 1
            continue
        uid = match.group(1)
        if uid not in seen:
            seen.add(uid)
            found.append(uid)
    return found, invalid


def api_json(path, api_key, method="GET", payload=None, idempotency_key=None):
    headers = {
        "Authorization": "Bearer " + api_key,
        "Accept": "application/json",
    }
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    req = Request(API_BASE + path, data=body, headers=headers, method=method)
    with urlopen(req, timeout=30) as response:
        result = json.load(response)
    if not isinstance(result, dict) or result.get("success") is False:
        raise ValueError("API response did not report success")
    return result.get("data") or {}


def _collect_limits(obj, names, depth=0):
    if depth > 4 or not isinstance(obj, (dict, list)):
        return []
    values = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in names and isinstance(value, int) and value > 0:
                values.append(value)
            if isinstance(value, (dict, list)):
                values.extend(_collect_limits(value, names, depth + 1))
    else:
        for value in obj:
            values.extend(_collect_limits(value, names, depth + 1))
    return values


class UidCheckerTab:
    """Independent view; no changes to the existing Selenium/browser path."""

    def __init__(self, parent):
        self.parent = parent
        self.uids = []
        self.results = {}
        self.category = "Chưa phân loại"
        self.cancel = threading.Event()
        self.pause = threading.Event()
        self.running = False
        self.total = 0
        self._make_ui()

    def _make_ui(self):
        frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(
            frame, text="CHECK LIVE FACEBOOK • UID",
            font=ctk.CTkFont(size=19, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            frame,
            text="Chỉ gửi UID tới API. Cookie không được tải lên hoặc lưu lại. "
                 "LIVE không có nghĩa là Cookie còn hiệu lực.",
            text_color=("gray40", "gray70"), wraplength=800, justify="left"
        ).pack(anchor="w", pady=(3, 12))

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(top, text="Nhập TXT / CSV", width=145, command=self.load_file).pack(
            side="left", padx=10, pady=9
        )
        self.count_label = ctk.CTkLabel(top, text="Chưa nhập UID")
        self.count_label.pack(side="left", padx=8)
        self.category_select = ctk.CTkOptionMenu(
            top, values=["Chưa phân loại", "NoVerify", "Verify"], width=150
        )
        self.category_select.pack(side="right", padx=10)

        settings = ctk.CTkFrame(frame)
        settings.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(settings, text="API Key:").pack(side="left", padx=(12, 5), pady=9)
        self.key_entry = ctk.CTkEntry(
            settings, show="*", placeholder_text="Key có checker:read / checker:write",
            width=385
        )
        self.key_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(settings, text="API: accinsfb.com", text_color=("gray40", "gray70")
                     ).pack(side="right", padx=12)

        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 8))
        self.start_btn = ctk.CTkButton(
            controls, text="Bắt đầu check UID", command=self.start
        )
        self.start_btn.pack(side="left", padx=(0, 7))
        self.pause_btn = ctk.CTkButton(
            controls, text="Tạm dừng", width=110, command=self.toggle_pause,
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=5)
        self.stop_btn = ctk.CTkButton(
            controls, text="Dừng", width=80, command=self.stop, state="disabled",
            fg_color="#6B2937", hover_color="#8B3547"
        )
        self.stop_btn.pack(side="left", padx=5)
        ctk.CTkButton(
            controls, text="Xuất CSV", width=100, command=self.export
        ).pack(side="right")

        self.progress = ctk.CTkProgressBar(frame)
        self.progress.pack(fill="x", pady=(0, 6))
        self.progress.set(0)
        self.message = ctk.CTkLabel(frame, text="Sẵn sàng", anchor="w")
        self.message.pack(fill="x", pady=(0, 8))

        table_frame = ctk.CTkFrame(frame)
        table_frame.pack(fill="both", expand=True)
        self.table = ttk.Treeview(
            table_frame, columns=("uid", "category", "status"), show="headings"
        )
        for column, title, width in (
            ("uid", "UID", 260),
            ("category", "Nhóm", 165),
            ("status", "Kết quả UID", 190),
        ):
            self.table.heading(column, text=title)
            self.table.column(column, width=width, stretch=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True, padx=(7, 0), pady=7)
        scrollbar.pack(side="right", fill="y", padx=(0, 7), pady=7)

    def load_file(self):
        if self.running:
            messagebox.showwarning("Đang kiểm tra", "Hãy dừng trước khi nhập file mới.")
            return
        path = filedialog.askopenfilename(
            title="Chọn danh sách UID", filetypes=[
                ("Text / CSV", "*.txt *.csv"), ("Tất cả", "*.*")
            ]
        )
        if not path:
            return
        try:
            raw = Path(path).read_text(encoding="utf-8-sig", errors="replace")
            uids, invalid = parse_uids(raw)
        except Exception as exc:
            messagebox.showerror("Không đọc được file", str(exc))
            return
        self.uids = uids[:10000]
        self.category = self.category_select.get()
        self.results = {uid: "CHƯA KIỂM TRA" for uid in self.uids}
        self.table.delete(*self.table.get_children())
        for uid in self.uids:
            self.table.insert("", "end", iid=uid, values=(uid, self.category, "CHƯA KIỂM TRA"))
        self.count_label.configure(text=f"{len(self.uids):,} UID duy nhất")
        notes = []
        if invalid:
            notes.append(f"{invalid} dòng không phải UID")
        if len(uids) > 10000:
            notes.append("chỉ lấy 10.000 UID đầu tiên")
        self.message.configure(text="Đã nhập danh sách. " + "; ".join(notes))
        self.progress.set(0)

    def start(self):
        if self.running:
            return
        key = self.key_entry.get().strip()
        if not self.uids:
            messagebox.showinfo("Chưa có dữ liệu", "Nhập file UID trước.")
            return
        if not key:
            messagebox.showinfo("Thiếu API Key", "Nhập API Key có quyền checker.")
            return
        self.cancel.clear()
        self.pause.clear()
        self.running = True
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal", text="Tạm dừng")
        self.stop_btn.configure(state="normal")
        self.message.configure(text="Đang kết nối API và đọc giới hạn...")
        self.category = self.category_select.get()
        for uid in self.uids:
            self.table.item(uid, values=(uid, self.category, self.results[uid]))
        threading.Thread(target=self._worker, args=(key,), daemon=True).start()

    def toggle_pause(self):
        if self.pause.is_set():
            self.pause.clear()
            self.pause_btn.configure(text="Tạm dừng")
        else:
            self.pause.set()
            self.pause_btn.configure(text="Tiếp tục")

    def stop(self):
        self.cancel.set()
        self.pause.clear()
        self.message.configure(text="Đang dừng sau yêu cầu API hiện tại...")

    def _schedule(self, fn):
        try:
            self.parent.after(0, fn)
        except Exception:
            pass

    def _worker(self, key):
        try:
            capabilities = api_json("/checker/capabilities", key)
            batch_caps = _collect_limits(
                capabilities, {
                    "max_batch", "max_batch_size", "batch_limit",
                    "max_identifiers_per_batch", "max_items_per_batch"
                }
            )
            per_minute_caps = _collect_limits(
                capabilities, {
                    "per_minute", "checks_per_minute",
                    "max_checks_per_minute", "rate_limit_per_minute"
                }
            )
            per_minute = min(per_minute_caps) if per_minute_caps else None
            batch_size = min([50] + batch_caps + ([per_minute] if per_minute else []))
            outstanding = [uid for uid in self.uids
                           if self.results[uid] != "LIVE"]
            for pos in range(0, len(outstanding), batch_size):
                if self.cancel.is_set():
                    break
                while self.pause.is_set() and not self.cancel.is_set():
                    time.sleep(0.15)
                if self.cancel.is_set():
                    break
                chunk = outstanding[pos:pos + batch_size]
                idem = "uidcheck-" + uuid.uuid4().hex
                outcome = {}
                try:
                    data = api_json(
                        "/checker/checks", key, method="POST",
                        payload={"platform": "facebook", "identifiers": chunk},
                        idempotency_key=idem
                    )
                    # API may create an asynchronous check before results arrive.
                    check_id = data.get("check_id")
                    for _ in range(8):
                        if not check_id or data.get("results") or self.cancel.is_set():
                            break
                        if self.cancel.wait(2):
                            break
                        data = api_json("/checker/checks/" + str(check_id), key)
                    for row in data.get("results", []):
                        uid = str(row.get("identifier", ""))
                        state = str(row.get("status", "")).lower()
                        if uid in chunk:
                            outcome[uid] = "LIVE" if state == "live" else "UNKNOWN"
                    for uid in chunk:
                        outcome.setdefault(uid, "UNKNOWN")
                except HTTPError as exc:
                    outcome = {uid: "API_ERROR (" + str(exc.code) + ")" for uid in chunk}
                    if exc.code in (401, 403):
                        self.cancel.set()
                    if exc.code == 429:
                        pause = exc.headers.get("Retry-After", "30")
                        try:
                            seconds = min(120, max(1, int(pause)))
                        except (TypeError, ValueError):
                            seconds = 30
                        self.cancel.wait(seconds)
                except (URLError, ValueError, OSError, TimeoutError, TypeError, KeyError):
                    outcome = {uid: "API_ERROR" for uid in chunk}
                self.results.update(outcome)
                self._schedule(lambda x=outcome.copy(): self._update_result(x))
                if per_minute and not self.cancel.is_set():
                    delay = 60.0 * len(chunk) / per_minute
                    self.cancel.wait(delay)
            self._schedule(self._finished)
        except Exception as exc:
            error_name = type(exc).__name__
            self._schedule(lambda err=error_name: self._finished(error=err))

    def _update_result(self, outcome):
        for uid, status in outcome.items():
            if self.table.exists(uid):
                self.table.item(uid, values=(uid, self.category, status))
        processed = sum(status != "CHƯA KIỂM TRA" for status in self.results.values())
        live = sum(status == "LIVE" for status in self.results.values())
        unknown = sum(status == "UNKNOWN" for status in self.results.values())
        errors = sum(status.startswith("API_ERROR") for status in self.results.values())
        self.progress.set(processed / max(len(self.uids), 1))
        self.message.configure(
            text=f"Đã xử lý {processed:,}/{len(self.uids):,}  •  "
                 f"LIVE {live:,}  •  UNKNOWN {unknown:,}  •  Lỗi API {errors:,}"
        )

    def _finished(self, error=None):
        self.running = False
        self.pause.clear()
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="Tạm dừng")
        self.stop_btn.configure(state="disabled")
        if error:
            self.message.configure(text=f"Không thể kết nối hoặc đọc API ({error}).")
        elif self.cancel.is_set():
            self.message.configure(text=self.message.cget("text") + "  •  Đã dừng")
        else:
            self.message.configure(text=self.message.cget("text") + "  •  Hoàn tất")

    def export(self):
        if not self.uids:
            messagebox.showinfo("Chưa có dữ liệu", "Không có dữ liệu để xuất.")
            return
        path = filedialog.asksaveasfilename(
            title="Xuất kết quả UID", defaultextension=".csv",
            filetypes=[("CSV UTF-8", "*.csv")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["uid", "category", "uid_status", "checked_at"])
            stamp = datetime.now().isoformat(timespec="seconds")
            for uid in self.uids:
                status = self.results[uid]
                writer.writerow([
                    uid, self.category, status,
                    "" if status == "CHƯA KIỂM TRA" else stamp
                ])
        messagebox.showinfo("Đã xuất", "CSV chỉ chứa UID và trạng thái; không có Cookie.")
