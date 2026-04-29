import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_and_split(path="manual_GCodeV4 (1).pdf"):
    if not os.path.exists(path):
        pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
        if pdf_files:
            path = pdf_files[0]
        else:
            raise FileNotFoundError(f"ไม่พบไฟล์ PDF ในเส้นทาง: {path}")

    loader = PyPDFLoader(path)
    documents = loader.load()

    # ขยายเป็น 1000 เพื่อให้ขั้นตอนที่ยาวๆ อยู่ใน chunk เดียวกัน ไม่ขาดตอน
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )

    return splitter.split_documents(documents)