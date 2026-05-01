import os
from datetime import datetime
from load_data import load_and_split
from vector_db import create_vector_db
from chatbot import create_chatbot

print("กำลังเตรียมข้อมูลเอกสาร (V9 คู่มือ Gcode  Version_9 28042569.pdf)...")
# โหลดเอกสาร
docs = load_and_split()

print("กำลังสร้างฐานข้อมูล Vector...")
# สร้าง vector db
db = create_vector_db(docs)

print("กำลังสร้าง Chatbot...")
# สร้าง chatbot
qa = create_chatbot(db)

history = []

print("\n--- ยินดีต้อนรับสู่ RAG Chatbot! (พิมพ์ 'exit' เพื่อบันทึกประวัติและออกจากโปรแกรม) ---")

# loop ถาม-ตอบ
while True:
    q = input("\nคุณ: ")
    if q.lower() in ["exit", "quit", "ออก"]:
        print("กำลังบันทึกประวัติการสนทนา...")
        # ส่งออกไฟล์ text
        filename = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("--- ประวัติการสนทนา ---\n")
            for entry in history:
                f.write(f"คุณ: {entry['user']}\n")
                f.write(f"AI: {entry['bot']}\n")
                f.write("-" * 20 + "\n")
        print(f"บันทึกไฟล์เสร็จสิ้น: {filename}")
        print("ลาก่อนครับ!")
        break

    if not q.strip():
        continue

    print("AI กำลังพิมพ์...")
    try:
        # ใช้ LCEL chain — invoke ด้วย string ตรงๆ
        ans = qa.invoke(q)
        print("AI:", ans)
        
        # เก็บลง history
        history.append({"user": q, "bot": ans})
        
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")