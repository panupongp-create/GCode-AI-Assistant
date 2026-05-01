# -*- coding: utf-8 -*-
import os, sys, threading, shutil, uuid, time, queue
from ollama_manager import OllamaManager
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
from datetime import datetime
from PIL import Image, ImageTk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ADMIN_USER, ADMIN_PASS = "admin", "1234"
C_BG = "#0d1117"
C_SIDEBAR = "#161b22"
C_PANEL = "#1c2128"
C_BORDER = "#30363d"
C_ACCENT = "#58a6ff"
C_GREEN = "#3fb950"
C_RED = "#f85149"
C_TEXT = "#e6edf3"
C_DIM = "#7d8590"
C_USER_BG = "#1c2128"
C_BOT_BG = "#0d1117"
C_THINK = "#1a1f29"

def resource_path(p):
    if hasattr(sys, '_MEIPASS'): return os.path.join(sys._MEIPASS, p)
    return os.path.join(os.path.abspath("."), p)

def get_docs_folder():
    base = os.path.dirname(os.path.abspath(sys.argv[0]))
    d = os.path.join(base, "documents"); os.makedirs(d, exist_ok=True); return d

# ============================================================
class LoginPage(ctk.CTkFrame):
    def __init__(self, parent, on_guest, on_admin):
        super().__init__(parent, fg_color=C_BG)
        self.on_guest, self.on_admin = on_guest, on_admin
        box = ctk.CTkFrame(self, fg_color=C_PANEL, corner_radius=16, width=400, height=480, border_width=1, border_color=C_BORDER)
        box.place(relx=0.5, rely=0.5, anchor="center"); box.pack_propagate(False)
        ctk.CTkLabel(box, text="⚙️", font=("Segoe UI Emoji", 40)).pack(pady=(30, 5))
        ctk.CTkLabel(box, text="G-Code AI Assistant", font=("Segoe UI", 20, "bold"), text_color=C_TEXT).pack()
        ctk.CTkLabel(box, text="ระบบตอบคำถามอัจฉริยะจากคู่มือ G-Code", font=("Segoe UI", 11), text_color=C_DIM).pack(pady=(2, 20))
        ctk.CTkFrame(box, height=1, fg_color=C_BORDER).pack(fill="x", padx=35)
        ctk.CTkLabel(box, text="ชื่อผู้ใช้", font=("Segoe UI", 11), text_color=C_DIM).pack(anchor="w", padx=40, pady=(15, 2))
        self.u = ctk.CTkEntry(box, height=36, corner_radius=8, font=("Segoe UI", 12))
        self.u.pack(fill="x", padx=40)
        ctk.CTkLabel(box, text="รหัสผ่าน", font=("Segoe UI", 11), text_color=C_DIM).pack(anchor="w", padx=40, pady=(10, 2))
        self.p = ctk.CTkEntry(box, height=36, corner_radius=8, show="●", font=("Segoe UI", 12))
        self.p.pack(fill="x", padx=40)
        self.p.bind("<Return>", lambda e: self._login())
        self.err = ctk.CTkLabel(box, text="", font=("Segoe UI", 10), text_color="#f85149")
        self.err.pack(pady=(5, 0))
        ctk.CTkButton(box, text="เข้าสู่ระบบ Admin", height=38, corner_radius=8, font=("Segoe UI", 12, "bold"), 
                      fg_color=C_ACCENT, hover_color="#79c0ff", text_color="#0d1117", command=self._login).pack(fill="x", padx=40, pady=(8, 5))
        ctk.CTkButton(box, text="💬 เข้าใช้งานแชท (Guest)", height=36, corner_radius=8, font=("Segoe UI", 11), 
                      fg_color="transparent", border_width=1, border_color=C_BORDER, text_color=C_TEXT, command=self.on_guest).pack(fill="x", padx=40, pady=(0, 25))

    def _login(self):
        if self.u.get().strip() == ADMIN_USER and self.p.get().strip() == ADMIN_PASS: self.on_admin()
        else: self.err.configure(text="❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

# ============================================================
class ImagePreview(ctk.CTkToplevel):
    def __init__(self, parent, img_path, page_num):
        super().__init__(parent)
        self.title(f"ตัวอย่างรูปภาพ - หน้า {page_num}")
        self.geometry("900x900")
        self.configure(fg_color=C_BG)
        self.after(10, self.lift) # ให้อยู่หน้าสุด
        
        # โหลดรูปขนาดใหญ่
        img = Image.open(img_path)
        w, h = img.size
        ratio = min(850/w, 800/h)
        new_w, new_h = int(w*ratio), int(h*ratio)
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.photo = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(new_w, new_h))
        
        lbl = ctk.CTkLabel(self, image=self.photo, text="")
        lbl.pack(padx=20, pady=20, expand=True)
        ctk.CTkLabel(self, text=f"หน้า {page_num} (กดปิดหน้าต่างเพื่อกลับสู่แชท)", font=("Segoe UI", 12), text_color=C_DIM).pack(pady=(0, 20))

# ============================================================
class ChatPage(ctk.CTkFrame):
    def __init__(self, parent, is_admin, go_login):
        super().__init__(parent, fg_color=C_BG)
        self.is_admin, self.go_login = is_admin, go_login
        self.chatbot = None
        self.system_ready = False
        self.is_asking = False
        self.stop_event = threading.Event()
        self.conversations = {} 
        self.current_conv = None
        self.active_content_label = None
        self.active_think_label = None
        self.active_image_frame = None
        self.start_time = 0
        self._token_buffer = ""
        self._thinking_cache = ""
        self._pages_cache = []
        self._images_drawn = False
        self._flush_scheduled = False
        self._build()
        self._new_chat()
        self._start_loading()

    def _build(self):
        self.sidebar = ctk.CTkFrame(self, width=260, fg_color=C_SIDEBAR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y"); self.sidebar.pack_propagate(False)
        sh = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=50)
        sh.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkButton(sh, text="＋ แชทใหม่", height=36, corner_radius=8, font=("Segoe UI", 12), 
                      fg_color=C_BORDER, text_color=C_TEXT, command=self._new_chat).pack(fill="x")
        self.conv_list = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.conv_list.pack(fill="both", expand=True, padx=6, pady=5)
        sb = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        sb.pack(fill="x", padx=10, pady=8)
        if self.is_admin:
            ctk.CTkButton(sb, text="📄 อัพโหลดเอกสาร", height=32, corner_radius=8, font=("Segoe UI", 11), 
                          fg_color=C_GREEN, text_color="#0d1117", command=self._upload_doc).pack(fill="x", pady=(0, 4))
        ctk.CTkButton(sb, text="🚪 ออกจากระบบ", height=32, corner_radius=8, font=("Segoe UI", 11), 
                      fg_color="transparent", border_width=1, border_color=C_BORDER, text_color=C_DIM, command=self.go_login).pack(fill="x")
        main = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        main.pack(side="right", fill="both", expand=True)
        hdr = ctk.CTkFrame(main, height=48, fg_color=C_PANEL, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="⚙️ G-Code AI", font=("Segoe UI", 13, "bold"), text_color=C_TEXT).pack(side="left", padx=14)
        self.status_lbl = ctk.CTkLabel(hdr, text="● โหลดระบบ...", font=("Segoe UI", 10), text_color="#d29922")
        self.status_lbl.pack(side="left", padx=8)
        self.chat_area = ctk.CTkScrollableFrame(main, fg_color=C_BG, corner_radius=0)
        self.chat_area.pack(fill="both", expand=True)
        inp_bar = ctk.CTkFrame(main, height=70, fg_color=C_BG, corner_radius=0)
        inp_bar.pack(fill="x")
        inp_inner = ctk.CTkFrame(inp_bar, fg_color=C_PANEL, corner_radius=12, border_width=1, border_color=C_BORDER)
        inp_inner.pack(fill="x", padx=20, pady=12)
        
        self.inp_var = ctk.StringVar()
        self.inp = ctk.CTkEntry(inp_inner, height=40, corner_radius=10, border_width=0, fg_color="transparent", 
                                placeholder_text="ถามคำถามเกี่ยวกับ G-Code...", font=("Segoe UI", 13), 
                                text_color=C_TEXT, textvariable=self.inp_var)
        self.inp.pack(side="left", fill="both", expand=True, padx=(12, 5))
        self.inp.bind("<Return>", lambda e: self._on_send())
        
        # บังคับ Bind Ctrl+V สำหรับการวางข้อความ
        self.inp.bind("<Control-v>", self._manual_paste_handler)
        self.inp.bind("<Control-V>", self._manual_paste_handler)
        
        self.send_btn = ctk.CTkButton(inp_inner, text="➤", width=44, height=36, corner_radius=8, font=("Segoe UI", 16),
                                      fg_color=C_ACCENT, hover_color="#79c0ff", text_color="#0d1117", command=self._on_send)
        self.send_btn.pack(side="right", padx=6, pady=4)
        
        self.copy_all_btn = ctk.CTkButton(inp_inner, text="📋 คัดลอกทั้งหมด", width=120, height=36, corner_radius=8, font=("Segoe UI", 10),
                                      fg_color="#555555", hover_color="#777777", text_color="#ffffff", command=self._copy_all_chat)
        self.copy_all_btn.pack(side="right", padx=6, pady=4)

        # ปุ่มวางข้อความ (Paste Button) - ตามที่ USER ต้องการ
        self.paste_btn = ctk.CTkButton(inp_inner, text="📋 วาง", width=70, height=36, corner_radius=8, font=("Segoe UI", 10),
                                      fg_color="#333333", hover_color="#444444", text_color="#ffffff", command=self._manual_paste_handler)
        self.paste_btn.pack(side="right", padx=2, pady=4)

        # เมนูคลิกขวา
        self.ctx_menu = ctk.CTkFrame(self, fg_color=C_PANEL, corner_radius=8, border_width=1, border_color=C_BORDER)
        ctk.CTkButton(self.ctx_menu, text="📄 คัดลอก (Copy)", height=28, fg_color="transparent", anchor="w", 
                      command=self._ctx_copy).pack(fill="x")
        ctk.CTkButton(self.ctx_menu, text="📋 วาง (Paste)", height=28, fg_color="transparent", anchor="w", 
                      command=self._ctx_paste).pack(fill="x")
        self.inp.bind("<Button-3>", self._show_ctx_menu)

    def _manual_paste_handler(self, event=None):
        """Logic การวางข้อความ (พยายามใช้หลายวิธีเพื่อให้มั่นใจว่าติด)"""
        try:
            # ดึงข้อความจาก Clipboard
            clip = self.winfo_toplevel().clipboard_get()
            if not clip: return "break"
            
            # วิธีที่ 1: ใส่ที่ตำแหน่ง Cursor ปัจจุบัน (ใช้ internal _entry เพื่อความแม่นยำ)
            try:
                self.inp._entry.insert("insert", clip)
            except:
                # วิธีที่ 2: ถ้าวิธีแรกพลาด ให้ต่อท้าย StringVar
                current = self.inp_var.get()
                self.inp_var.set(current + clip)
            
            self.after(10, lambda: self.inp.icursor("end"))
            self.inp.focus_set()
        except Exception as e:
            print(f"Paste error: {e}")
        return "break"

    def _show_ctx_menu(self, event):
        self.ctx_menu.place(x=event.x_root - self.winfo_rootx(), y=event.y_root - self.winfo_rooty())
        self.ctx_menu.lift()

    def _ctx_copy(self):
        self.inp.event_generate("<<Copy>>")
        self.ctx_menu.place_forget()

    def _ctx_paste(self):
        self.ctx_menu.place_forget()
        self.inp.focus_set()
        self._manual_paste_handler()

    def _new_chat(self):
        cid = str(uuid.uuid4())[:8]
        self.conversations[cid] = {"title": "แชทใหม่", "messages": []}
        self.current_conv = cid
        self._refresh_conv_list(); self._render_chat()

    def _refresh_conv_list(self):
        for w in self.conv_list.winfo_children(): w.destroy()
        for cid, data in reversed(list(self.conversations.items())):
            btn = ctk.CTkButton(self.conv_list, text="💬 " + data["title"][:25], height=34, corner_radius=8,
                                font=("Segoe UI", 11), anchor="w", fg_color=C_BORDER if cid == self.current_conv else "transparent",
                                hover_color="#484f58", text_color=C_TEXT, command=lambda c=cid: self._switch_conv(c))
            btn.pack(fill="x", pady=1)

    def _switch_conv(self, cid):
        self.current_conv = cid
        self._refresh_conv_list(); self._render_chat()

    def _render_chat(self):
        for w in self.chat_area.winfo_children(): w.destroy()
        if not self.current_conv: return
        for msg in self.conversations[self.current_conv]["messages"]: self._draw_message(msg)

    def _draw_message(self, msg, is_streaming=False):
        is_user = msg["role"] == "user"
        row = ctk.CTkFrame(self.chat_area, fg_color=C_USER_BG if is_user else C_BOT_BG, corner_radius=0)
        row.pack(fill="x", pady=1)
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=40, pady=14)
        icon, name, color = ("👤", "คุณ", C_GREEN) if is_user else ("🤖", "AI", C_ACCENT)
        ctk.CTkLabel(inner, text=f"{icon} {name}", font=("Segoe UI", 11, "bold"), text_color=color).pack(anchor="w")
        think_lbl = None; img_frame = None
        if not is_user:
            think_frame = ctk.CTkFrame(inner, fg_color=C_THINK, corner_radius=8, border_width=1, border_color=C_BORDER)
            think_frame.pack(fill="x", pady=(6, 4))
            think_header = ctk.CTkFrame(think_frame, fg_color="transparent")
            think_header.pack(fill="x", padx=10, pady=(6, 2))
            ctk.CTkLabel(think_header, text="🔍 กระบวนการคิด", font=("Segoe UI", 10, "bold"), text_color="#d29922").pack(side="left")
            self.think_timer = ctk.CTkLabel(think_header, text="", font=("Segoe UI", 9), text_color=C_DIM)
            self.think_timer.pack(side="right")
            think_lbl = ctk.CTkLabel(think_frame, text=msg.get("thinking", "กำลังเตรียมข้อมูล..."), font=("Segoe UI", 10), 
                                     text_color=C_DIM, wraplength=580, justify="left", anchor="w")
            think_lbl.pack(fill="x", padx=10, pady=(0, 8))
        content_lbl = ctk.CTkLabel(inner, text=msg["content"], font=("Segoe UI", 12), text_color=C_TEXT, 
                                   wraplength=620, justify="left", anchor="w")
        content_lbl.pack(fill="x", pady=(6, 0))
        if not is_user:
            img_frame = ctk.CTkFrame(inner, fg_color="transparent")
            img_frame.pack(fill="x", pady=(10, 0))
            if "pages" in msg and msg["pages"]: self._display_pages(img_frame, msg["pages"])
        if is_streaming:
            self.active_content_label = content_lbl
            self.active_think_label = think_lbl
            self.active_image_frame = img_frame
            self._images_drawn = False
            
        if not is_user:
            btn_row = ctk.CTkFrame(inner, fg_color="transparent")
            btn_row.pack(fill="x", pady=(5, 0))
            ctk.CTkButton(btn_row, text="📋 คัดลอกข้อความ", width=100, height=24, corner_radius=6, 
                          font=("Segoe UI", 10), fg_color=C_BORDER, hover_color="#484f58", 
                          command=lambda t=msg["content"]: self._copy_to_clipboard(t)).pack(side="left")

        return content_lbl

    def _copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        messagebox.showinfo("สำเร็จ", "คัดลอกลง Clipboard แล้ว")

    def _copy_all_chat(self):
        if not self.current_conv: return
        msgs = self.conversations[self.current_conv]["messages"]
        lines = []
        for m in msgs:
            role = "คุณ" if m["role"] == "user" else "AI"
            lines.append(f"{role}: {m['content']}")
        full_text = "\n".join(lines)
        self._copy_to_clipboard(full_text)

    def _display_pages(self, frame, pages):
        if not pages: return
        for w in frame.winfo_children(): w.destroy()
        ctk.CTkLabel(frame, text="📸 รูปภาพจากคู่มือ (คลิกที่รูปเพื่อขยาย):", font=("Segoe UI", 10, "bold"), text_color=C_DIM).pack(anchor="w", pady=(0, 5))
        scroll_img = ctk.CTkScrollableFrame(frame, height=260, orientation="horizontal", fg_color="transparent")
        scroll_img.pack(fill="x")
        for p in pages:
            img_path = resource_path(f"page_images/page_{p}.png")
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    ratio = img.height / img.width; new_w = 300; new_h = int(new_w * ratio)
                    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(new_w, new_h))
                    container = ctk.CTkFrame(scroll_img, fg_color=C_PANEL, corner_radius=8, border_width=1, border_color=C_BORDER)
                    container.pack(side="left", padx=5)
                    btn = ctk.CTkButton(container, image=ctk_img, text="", fg_color="transparent", hover_color=C_BORDER, 
                                        width=new_w, height=new_h, command=lambda path=img_path, num=p: self._preview_image(path, num))
                    btn.pack(padx=2, pady=2)
                    ctk.CTkLabel(container, text=f"หน้า {p}", font=("Segoe UI", 9), text_color=C_DIM).pack(pady=(0, 4))
                except Exception as e: print(f"Error loading image p{p}: {e}")

    def _preview_image(self, path, num):
        ImagePreview(self.winfo_toplevel(), path, num)

    def _start_loading(self): threading.Thread(target=self._load, daemon=True).start()
    def _load(self):
        try:
            self._set_status("กำลังตรวจสอบ Ollama...", "#d29922")
            mgr = OllamaManager(model_name="llama3.2:3b")
            
            if not mgr.is_server_running():
                self._set_status("กำลังเริ่ม Ollama...", "#d29922")
                if not mgr.start_server():
                    self._set_status("เริ่ม Ollama ไม่ได้", "#f85149")
                    return
            
            self._set_status("ตรวจสอบโมเดล...", "#d29922")
            if not mgr.check_and_pull_model(progress_callback=lambda m: self._set_status(m, "#d29922")):
                self._set_status("โหลดโมเดลไม่สำเร็จ", "#f85149")
                return

            self._set_status("โหลด Vector DB...", "#d29922")
            from vector_db import load_vector_db
            try: db = load_vector_db()
            except FileNotFoundError:
                from load_data import load_and_split; from vector_db import create_vector_db
                docs = load_and_split(resource_path("V9 คู่มือ Gcode  Version_9 28042569.pdf")); db = create_vector_db(docs)
            from chatbot import create_chatbot, prewarm_model
            self.chatbot = create_chatbot(db); prewarm_model(self.chatbot)
            self.system_ready = True; self._set_status("พร้อมใช้งาน", C_GREEN)
        except Exception as e: 
            print(f"Load error: {e}")
            self._set_status("ข้อผิดพลาด", "#f85149")

    def _set_status(self, t, c): self.after(0, lambda: self.status_lbl.configure(text=f"● {t}", text_color=c))

    def _on_send(self):
        if self.is_asking: self.stop_event.set(); return
        q = self.inp.get().strip()
        if not q or not self.system_ready: return
        self.inp.delete(0, "end"); conv = self.conversations[self.current_conv]
        if not conv["messages"]: conv["title"] = q[:30]; self._refresh_conv_list()
        conv["messages"].append({"role": "user", "content": q}); self._render_chat()
        self.is_asking = True; self.stop_event.clear(); self.start_time = time.time()
        self.send_btn.configure(text="■", fg_color=C_RED, hover_color="#ff7b72")
        self._update_bubble_timer()
        threading.Thread(target=self._ask, args=(q,), daemon=True).start()

    def _update_bubble_timer(self):
        if self.is_asking:
            elapsed = int(time.time() - self.start_time)
            if hasattr(self, 'think_timer'): self.think_timer.configure(text=f"⏳ {elapsed}s")
            self.after(1000, self._update_bubble_timer)

    def _flush_tokens(self):
        self._flush_scheduled = False
        if not self._token_buffer and not self._pages_cache: return
        buf = self._token_buffer; think = self._thinking_cache; pages = self._pages_cache
        self._token_buffer = ""
        if self.active_content_label:
            if buf: cur = self.active_content_label.cget("text"); self.active_content_label.configure(text=cur + buf)
            if self.active_think_label and think: self.active_think_label.configure(text=think)
            if self.active_image_frame and pages and not self._images_drawn:
                self._images_drawn = True; self._display_pages(self.active_image_frame, pages)
            self.chat_area._parent_canvas.yview_moveto(1.0)

    def _ask(self, question):
        try:
            from chatbot import ask_question
            msg_obj = {"role": "bot", "content": "", "thinking": "กำลังค้นหาเอกสารที่เกี่ยวข้อง...", "pages": []}
            self.conversations[self.current_conv].setdefault("messages", []).append(msg_obj)
            self.after(0, lambda: self._draw_message(msg_obj, is_streaming=True))
            def on_token(token, thinking, pages):
                self._token_buffer += token; self._thinking_cache = thinking; self._pages_cache = pages
                msg_obj["content"] += token; msg_obj["thinking"] = thinking; msg_obj["pages"] = pages
                if not self._flush_scheduled: self._flush_scheduled = True; self.after(50, self._flush_tokens)
            ask_question(self.chatbot, question, on_token, stop_event=self.stop_event)
            self.after(0, self._flush_tokens); self.after(10, self._finalize)
        except Exception as e: self.after(0, self._finalize)

    def _finalize(self):
        self.is_asking = False
        self.send_btn.configure(text="➤", fg_color=C_ACCENT, hover_color="#79c0ff")
        self._set_status("พร้อมใช้งาน", C_GREEN); self.inp.focus_set()

    def _upload_doc(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        if files:
            for f in files: shutil.copy2(f, os.path.join(get_docs_folder(), os.path.basename(f)))
            messagebox.showinfo("สำเร็จ", "กรุณารีสตาร์ทโปรแกรมเพื่ออัพเดทฐานข้อมูล")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("G-Code AI Assistant"); self.geometry("1100x720")
        self.page = None; self._show_login()
    def _show_login(self):
        if self.page: self.page.destroy()
        self.page = LoginPage(self, lambda: self._show_chat(False), lambda: self._show_chat(True)); self.page.pack(fill="both", expand=True)
    def _show_chat(self, admin):
        self.page.destroy()
        self.page = ChatPage(self, admin, self._show_login)
        self.page.pack(fill="both", expand=True)

if __name__ == "__main__":
    App().mainloop()
