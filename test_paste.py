"""
สคริปต์ทดสอบ Paste ใน CTkEntry
ทดสอบ 3 วิธี:
1. ปุ่ม Paste (ใช้ clipboard_get + StringVar)
2. ปุ่ม Paste (ใช้ event_generate)
3. Native Ctrl+V (ไม่มี custom binding)
"""
import customtkinter as ctk
from tkinter import messagebox

ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.title("ทดสอบ Paste")
app.geometry("600x400")

# === Test 1: CTkEntry ปกติ ไม่มี binding อะไร (ทดสอบ Ctrl+V แบบ native) ===
ctk.CTkLabel(app, text="Test 1: CTkEntry ปกติ (ลอง Ctrl+V ที่นี่)", font=("Segoe UI", 12, "bold")).pack(pady=(10,2))
entry1 = ctk.CTkEntry(app, width=500, height=35, font=("Segoe UI", 13))
entry1.pack(pady=5)

# === Test 2: CTkEntry + StringVar + ปุ่ม Paste ===
ctk.CTkLabel(app, text="Test 2: CTkEntry + StringVar + ปุ่มวาง", font=("Segoe UI", 12, "bold")).pack(pady=(10,2))
var2 = ctk.StringVar()
entry2 = ctk.CTkEntry(app, width=500, height=35, font=("Segoe UI", 13), textvariable=var2)
entry2.pack(pady=5)

def paste_via_stringvar():
    try:
        clip = app.clipboard_get()
        current = var2.get()
        var2.set(current + clip)
        entry2.icursor("end")
        messagebox.showinfo("OK", f"วางสำเร็จ: '{clip[:50]}'")
    except Exception as e:
        messagebox.showerror("Error", f"ไม่สามารถวางได้: {e}")

ctk.CTkButton(app, text="📋 วางข้อความ (StringVar)", command=paste_via_stringvar).pack(pady=3)

# === Test 3: CTkEntry + internal _entry + ปุ่ม Paste ===
ctk.CTkLabel(app, text="Test 3: CTkEntry + internal _entry + ปุ่มวาง", font=("Segoe UI", 12, "bold")).pack(pady=(10,2))
entry3 = ctk.CTkEntry(app, width=500, height=35, font=("Segoe UI", 13))
entry3.pack(pady=5)

def paste_via_internal():
    try:
        clip = app.clipboard_get()
        internal = entry3._entry
        internal.insert("end", clip)
        messagebox.showinfo("OK", f"วางสำเร็จ: '{clip[:50]}'")
    except Exception as e:
        messagebox.showerror("Error", f"ไม่สามารถวางได้: {e}")

ctk.CTkButton(app, text="📋 วางข้อความ (internal _entry)", command=paste_via_internal).pack(pady=3)

# === ปุ่มตรวจสอบ Clipboard ===
def check_clipboard():
    try:
        clip = app.clipboard_get()
        messagebox.showinfo("Clipboard", f"ข้อมูลใน Clipboard:\n'{clip[:200]}'")
    except Exception as e:
        messagebox.showerror("Error", f"ไม่สามารถอ่าน Clipboard ได้: {e}")

ctk.CTkButton(app, text="🔍 ตรวจสอบ Clipboard", fg_color="#555", command=check_clipboard).pack(pady=10)

ctk.CTkLabel(app, text="วิธีทดสอบ: ก็อปข้อความจากที่อื่น แล้ว\n1. ลอง Ctrl+V ในช่อง Test 1\n2. กดปุ่ม 'วางข้อความ' ใน Test 2 และ Test 3\n3. กด 'ตรวจสอบ Clipboard' เพื่อดูว่าโปรแกรมอ่าน Clipboard ได้ไหม",
             font=("Segoe UI", 10), text_color="#888", wraplength=550).pack(pady=10)

app.mainloop()
