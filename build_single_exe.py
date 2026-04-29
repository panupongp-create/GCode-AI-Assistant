import subprocess
import sys
import os

def build_single():
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("[!] PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # PyInstaller command for SINGLE FILE
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Setup_GCode_AI_Assistant", # ตั้งชื่อให้เหมือนตัวติดตั้ง
        "--onefile",            # รวมเป็นไฟล์เดียวตามที่ USER ต้องการ
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data=manual_GCodeV4 (1).pdf;.",
        "--add-data=page_images;page_images",
        "--hidden-import=langchain",
        "--hidden-import=langchain_community",
        "--hidden-import=langchain_community.document_loaders",
        "--hidden-import=langchain_community.vectorstores",
        "--hidden-import=langchain_community.embeddings",
        "--hidden-import=langchain_text_splitters",
        "--hidden-import=langchain_ollama",
        "--hidden-import=langchain.chains",
        "--hidden-import=langchain.prompts",
        "--hidden-import=chromadb",
        "--hidden-import=sentence_transformers",
        "--hidden-import=pypdf",
        "--hidden-import=tiktoken",
        "--hidden-import=huggingface_hub",
        "--hidden-import=tokenizers",
        "--hidden-import=torch",
        "--hidden-import=numpy",
        "--hidden-import=pydantic",
        "--hidden-import=requests",
        "--hidden-import=httpx",
        "--collect-submodules=langchain",
        "--collect-submodules=langchain_community",
        "--collect-submodules=langchain_text_splitters",
        "--collect-submodules=langchain_ollama",
        "--collect-submodules=chromadb",
        "--collect-submodules=sentence_transformers",
        "--collect-submodules=tokenizers",
        "--collect-data=sentence_transformers",
        "--collect-data=chromadb",
        "--collect-data=tokenizers",
        "gui_app.py",
    ]

    print("\nBuilding SINGLE EXE (This will take a while and produce a large file)...")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("[SUCCESS] Single EXE Created!")
        print("=" * 50)
        print(f"\nFile: dist/Setup_GCode_AI_Assistant.exe")
        print("\nNote:")
        print("  - The first run will be slow because it extracts files to temp.")
        print("  - Must have Ollama installed and model llama3.2:3b pulled.")
    else:
        print(f"\n[FAILED] Build failed (exit code: {result.returncode})")

if __name__ == "__main__":
    build_single()
