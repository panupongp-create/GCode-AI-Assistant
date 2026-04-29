from google import genai
import os

# ใส่ API Key ของคุณที่นี่เพื่อทดสอบ
api_key = "AIzaSyACOAppItMx9b5w0HEFfLetlKWLr7nqu6o"
client = genai.Client(api_key=api_key)

print("--- เริ่มการทดสอบเชื่อมต่อ Gemini (New SDK) ---")
try:
    # 1. ลองลิสต์โมเดล
    print("1. กำลังดึงรายชื่อโมเดล...")
    models = client.models.list()
    found_any = False
    for m in models:
        print(f"   - พบโมเดล: {m.name}")
        found_any = True
    
    if not found_any:
        print("   ❌ ไม่พบโมเดลใดๆ เลยในคีย์นี้")
    
    # 2. ลองส่งข้อความสั้นๆ
    print("\n2. กำลังลองส่งคำถาม 'Hello' ไปยัง gemini-1.5-flash...")
    response = client.models.generate_content(
        model='gemini-1.5-flash', 
        contents="Hello, are you there?"
    )
    print(f"   ✅ ตอบกลับสำเร็จ: {response.text}")

except Exception as e:
    print(f"\n❌ เกิดข้อผิดพลาด: {e}")

print("\n--- จบการทดสอบ ---")
