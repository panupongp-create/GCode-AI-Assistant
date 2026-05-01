import subprocess
import sys
import os

def build():
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("[!] PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=GCode_AI_Assistant",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data=V9 คู่มือ Gcode  Version_9 28042569.pdf;.",
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

    print("\nBuilding .exe ...")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("[SUCCESS] Build Completed!")
        print("=" * 50)
        print(f"\nLocation: dist/GCode_AI_Assistant/")
        print(f"Execute: dist/GCode_AI_Assistant/GCode_AI_Assistant.exe")
        print("\nNote:")
        print("  - Must have Ollama installed")
        print("  - Must pull model: llama3.2:3b")
        print("  - Must run Ollama: ollama serve")
    else:
        print(f"\n[FAILED] Build failed (exit code: {result.returncode})")

if __name__ == "__main__":
    build()
