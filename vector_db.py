import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

DB_DIR = "./chroma_db_expert" # ใช้ชื่อใหม่เพื่อความสะอาด

_embeddings_instance = None

def get_embeddings():
    global _embeddings_instance
    if _embeddings_instance is None:
        # ใช้โมเดลภาษาไทย/Multilingual ที่ดีที่สุดสำหรับรันบนเครื่อง (ไม่ต้องใช้ API Key)
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"device": "cpu"}
        )
    return _embeddings_instance

def create_vector_db(docs):
    embeddings = get_embeddings()
    db = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=DB_DIR
    )
    return db

def load_vector_db():
    if not os.path.exists(DB_DIR) or not os.listdir(DB_DIR):
        raise FileNotFoundError("❌ ไม่พบ Vector DB! กรุณารัน: python build_db.py")
    embeddings = get_embeddings()
    return Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

def load_or_create_vector_db(docs=None):
    if os.path.exists(DB_DIR) and os.listdir(DB_DIR):
        return load_vector_db()
    elif docs:
        return create_vector_db(docs)
    else:
        raise FileNotFoundError("ไม่พบเอกสาร")