"""
============================================================
  build_db.py — สร้างฐานข้อมูลความรู้ (รันครั้งเดียว)
============================================================
สูตร: PDF → Split (300/30) → all-MiniLM-L6-v2 → Chroma Persist

วิธีใช้:
  python build_db.py

หลังรันสำเร็จ จะได้โฟลเดอร์ chroma_db/ ที่พร้อมใช้งาน
ไม่ต้องรันซ้ำ เว้นแต่เปลี่ยนเอกสาร PDF
============================================================
"""

import os, sys, shutil, time

# ใช้ API Key ที่คุณให้มา
os.environ["GOOGLE_API_KEY"] = "AIzaSyAZCwz_75h5-fCFLOwhx2Z7M59PIDrLNLg"

def main():
    print("=" * 60)
    print("  BUILD KNOWLEDGE BASE (GEMINI EXPERT MODE)")
    print("=" * 60)

    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ ERROR: ไม่พบ GOOGLE_API_KEY ใน Environment Variables")
        print("วิธีแก้: setx GOOGLE_API_KEY \"your_key_here\" แล้วเปิด Terminal ใหม่")
        print("หรือใส่ในไฟล์ .env (ถ้ามี)")
        return

    # --- Step 1: Load PDF ---
    pdf_path = "manual_GCodeV4 (1).pdf"
    if not os.path.exists(pdf_path):
        pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
        if pdf_files:
            pdf_path = pdf_files[0]
        else:
            print("ERROR: PDF not found!")
            sys.exit(1)

    print(f"\nLoading: {pdf_path}")
    t0 = time.time()
    
    from load_data import load_and_split
    docs = load_and_split(pdf_path)
    print(f"   Success: {len(docs)} chunks ({time.time()-t0:.1f}s)")

    # --- Step 2: Delete old DB ---
    from vector_db import DB_DIR
    if os.path.exists(DB_DIR):
        print(f"\nDeleting old DB: {DB_DIR}")
        shutil.rmtree(DB_DIR)

    # --- Step 3: Create Vector DB ---
    print(f"\nCreating Vector DB (embedding {len(docs)} chunks)...")
    t1 = time.time()
    
    from vector_db import create_vector_db
    db = create_vector_db(docs)
    
    print(f"   Success: DB Created ({time.time()-t1:.1f}s)")
    print(f"   Saved at: {os.path.abspath(DB_DIR)}")

    print(f"\n{'=' * 60}")
    print(f"  DONE! (Total {time.time()-t0:.1f}s)")
    print(f"  You can now run: python gui_app.py")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
