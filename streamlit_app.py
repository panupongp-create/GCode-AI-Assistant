import streamlit as st
import os

# --- Fix for Protobuf Conflict & ChromaDB ---
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import time
import base64
import uuid
from datetime import datetime
from PIL import Image
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# --- Configuration & Setup ---
st.set_page_config(
    page_title="G-Code AI Expert Assistant",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Key initialization
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("❌ ไม่พบ API Key! กรุณาตรวจสอบไฟล์ `.streamlit/secrets.toml` หรือตั้งค่า Environment Variable")
    st.stop()

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

DB_DIR = "./chroma_db_expert"

# --- Styling ---
st.markdown("""
<style>
    .main {
        background-color: #0d1117;
        color: #e6edf3;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: #1c2128;
        border: 1px solid #30363d;
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: #0d1117;
        border: 1px solid #30363d;
    }
    .thinking-box {
        background-color: #1a1f29;
        border-left: 4px solid #d29922;
        padding: 10px;
        font-size: 0.9em;
        color: #8b949e;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    .user-image {
        max-width: 300px;
        border-radius: 10px;
        margin-bottom: 10px;
        border: 1px solid #30363d;
    }
    .page-reference {
        background-color: #238636;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
    }
    /* CSS Hack to move popover next to send button */
    div[data-testid="stChatInput"] {
        padding-right: 150px !important; /* เว้นที่ว่างด้านขวาสำหรับปุ่มแนบรูป */
    }
    .floating-attach {
        position: fixed;
        bottom: 42px;
        right: calc(50% - 340px); /* จัดให้อยู่ด้านขวา */
        z-index: 1001;
    }
    @media (max-width: 1200px) {
        .floating-attach { right: 100px; }
    }
    /* Chat history styling */
    .chat-history-item {
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 4px;
        cursor: pointer;
        transition: background-color 0.2s;
        border: 1px solid transparent;
    }
    .chat-history-item:hover {
        background-color: #1c2128;
        border-color: #30363d;
    }
    .chat-history-active {
        background-color: #1c2128 !important;
        border-color: #58a6ff !important;
    }
    .chat-history-title {
        font-size: 0.9em;
        font-weight: 500;
        color: #e6edf3;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .chat-history-date {
        font-size: 0.7em;
        color: #8b949e;
    }
    /* Logo styling */
    .top-right-logo {
        position: fixed;
        top: 20px;
        right: 40px;
        text-align: center;
        z-index: 1000;
        pointer-events: none;
    }
    .top-right-logo img {
        width: 80px;
        height: auto;
    }
    .top-right-logo div {
        font-size: 0.75em;
        color: #8b949e;
        margin-top: 5px;
        font-weight: bold;
        line-height: 1.2;
    }
</style>
""", unsafe_allow_html=True)

# --- Header Logo Display ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

logo_b64 = get_base64_image("logo_bict.png")
if logo_b64:
    st.markdown(
        f"""
        <div class="top-right-logo">
            <img src="data:image/png;base64,{logo_b64}">
            <div>ศูนย์เทคโนโลยีสารสนเทศและการสื่อสาร<br>สป. ศธ.</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# --- Session State: Multi-Conversation Management ---

def create_new_conversation():
    """Create a new empty conversation and return its ID."""
    conv_id = str(uuid.uuid4())[:8]
    st.session_state.conversations[conv_id] = {
        "title": "💬 สนทนาใหม่",
        "messages": [],
        "created_at": datetime.now().strftime("%d/%m %H:%M"),
    }
    return conv_id

def get_current_messages():
    """Get messages for the current conversation."""
    conv_id = st.session_state.current_conv_id
    if conv_id in st.session_state.conversations:
        return st.session_state.conversations[conv_id]["messages"]
    return []

def update_conversation_title(conv_id, first_message):
    """Auto-generate conversation title from the first user message."""
    title = first_message[:40]
    if len(first_message) > 40:
        title += "..."
    st.session_state.conversations[conv_id]["title"] = f"💬 {title}"

# Initialize conversation system
if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "current_conv_id" not in st.session_state:
    # Create a default conversation on first load
    first_id = create_new_conversation()
    st.session_state.current_conv_id = first_id

# Ensure current_conv_id is valid
if st.session_state.current_conv_id not in st.session_state.conversations:
    if st.session_state.conversations:
        st.session_state.current_conv_id = list(st.session_state.conversations.keys())[-1]
    else:
        first_id = create_new_conversation()
        st.session_state.current_conv_id = first_id

# --- Logic Functions ---

@st.cache_resource
def get_vector_db():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={"device": "cpu"}
    )
    if os.path.exists(DB_DIR) and os.listdir(DB_DIR):
        return Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    return None

def format_docs_with_pages(docs):
    formatted = ""
    for doc in docs:
        p = int(doc.metadata.get("page", 0)) + 1
        formatted += f"--- ข้อมูลหน้า {p} ---\n{doc.page_content}\n\n"
    return formatted

def get_available_models():
    try:
        import google.generativeai as genai
        # ต้องแนบ API Key ให้ genai ด้วย ไม่งั้นมันดึงชื่อรุ่นไม่ได้
        if "GOOGLE_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name.replace('models/', ''))
        
        if not models:
            return ["gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-2.5-flash"]
        return sorted(models, reverse=True) 
    except Exception as e:
        # ชื่อสำรองที่รับประกันว่าถูกต้องแน่นอน
        return ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]

def get_chatbot(db, model_name):
    llm = ChatGoogleGenerativeAI(
        model=model_name if model_name else "gemini-2.5-flash",
        temperature=0.4,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    
    template = """คุณคือ "AI ที่ปรึกษาด้าน G-Code"
หน้าที่ของคุณคือวิเคราะห์คำถามของผู้ใช้ และให้คำตอบเชิงลึกที่แม่นยำตามหลักการในคู่มือ พร้อมทั้งให้ข้อเสนอแนะที่ช่วยให้ผู้ใช้ทำงานได้ดียิ่งขึ้น

หลักการคิดและวิเคราะห์ของคุณ (Thinking Process):
1. วิเคราะห์เจตนา (Intent) ของผู้ใช้ว่าต้องการแก้ปัญหาเรื่องอะไร
2. ค้นหาข้อมูลที่เกี่ยวข้องจาก "คู่มืออ้างอิง" ที่ให้มาอย่างละเอียด
3. หากข้อมูลในคู่มือมีจำกัด ให้ใช้ตรรกะทางวิศวกรรมที่สอดคล้องกับคู่มือเพื่ออธิบายขยายความเพิ่มเติมได้
4. สรุปเป็นขั้นตอน หรือคำอธิบายที่เข้าใจง่าย แต่คงไว้ซึ่งความถูกต้องเชิงเทคนิค

กฎการตอบ:
1. ให้ความสำคัญกับความถูกต้องตามคู่มือเป็นอันดับหนึ่ง
2. หากไม่มีข้อมูลในคู่มือจริงๆ ให้พยายามอธิบายหลักการที่ใกล้เคียงที่สุด หรือแนะนำขั้นตอนการตรวจสอบเบื้องต้นที่วิศวกรควรทำ
3. อ้างอิงเลขหน้าทุกครั้งที่ใช้ข้อมูลจากหน้านั้น [PAGES: X]
4. ใช้โทนการสนทนาที่เป็นมืออาชีพ สุภาพ และกระตือรือร้นที่จะช่วยเหลือ

คู่มืออ้างอิง:
{context}

คำถาม: {question}
คำแนะนำจาก AI:"""

    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    retriever = db.as_retriever(search_kwargs={"k": 6})
    return {"llm": llm, "prompt": prompt, "retriever": retriever}

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ G-Code AI Settings")
    st.markdown("ระบบผู้ช่วยวิศวกรอัจฉริยะ")
    st.divider()
    
    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        new_id = create_new_conversation()
        st.session_state.current_conv_id = new_id
        st.rerun()
    
    st.divider()
    
    # Model Selection UI
    available_models = get_available_models()
    default_index = 0
    if "gemini-1.5-flash" in available_models:
        default_index = available_models.index("gemini-1.5-flash")
    
    selected_model = st.selectbox(
        "🤖 เลือกโมเดล AI:",
        options=available_models,
        index=default_index,
        help="หากรันไม่ได้ ให้ลองเปลี่ยนเป็นรุ่นอื่นในรายการนี้"
    )
    
    st.divider()
    
    # --- Chat History List ---
    st.markdown("### 📋 ประวัติการสนทนา")
    
    # Sort conversations: newest first
    sorted_convs = sorted(
        st.session_state.conversations.items(),
        key=lambda x: x[1].get("created_at", ""),
        reverse=True
    )
    
    if not sorted_convs:
        st.caption("ยังไม่มีประวัติการสนทนา")
    else:
        for conv_id, conv_data in sorted_convs:
            is_active = (conv_id == st.session_state.current_conv_id)
            title = conv_data.get("title", "💬 สนทนาใหม่")
            created = conv_data.get("created_at", "")
            msg_count = len(conv_data.get("messages", []))
            
            # Container for each history item
            col_btn, col_del = st.columns([5, 1])
            
            with col_btn:
                # Show active indicator
                label = f"{'🔵 ' if is_active else ''}{title}"
                if st.button(
                    label,
                    key=f"conv_{conv_id}",
                    use_container_width=True,
                    disabled=is_active
                ):
                    st.session_state.current_conv_id = conv_id
                    st.rerun()
            
            with col_del:
                if st.button("🗑️", key=f"del_{conv_id}", help="ลบการสนทนานี้"):
                    del st.session_state.conversations[conv_id]
                    # If we deleted the active conversation, switch to another or create new
                    if conv_id == st.session_state.current_conv_id:
                        if st.session_state.conversations:
                            st.session_state.current_conv_id = list(st.session_state.conversations.keys())[-1]
                        else:
                            new_id = create_new_conversation()
                            st.session_state.current_conv_id = new_id
                    st.rerun()
            
            # Show metadata below button
            if msg_count > 0:
                st.caption(f"   🕐 {created} · {msg_count} ข้อความ")
    
    st.divider()
    st.info("💡 **Tips:** ถามเจาะจงขั้นตอน หรือโค้ด G-Code ที่ต้องการตรวจสอบเพื่อให้ได้คำตอบที่แม่นยำที่สุด")

# --- Main UI ---
st.title("🛡️ G-Code Expert Assistant")

# Get current conversation messages
current_messages = get_current_messages()

# Load DB
db = get_vector_db()

if db is None:
    st.error("❌ ไม่พบฐานข้อมูลความรู้! กรุณาตรวจสอบว่ามีโฟลเดอร์ `chroma_db_expert` หรือไม่")
    st.stop()

try:
    chatbot = get_chatbot(db, selected_model)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อกับ AI ได้: {e}")
    st.stop()

# Display Chat History for current conversation
for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "pages" in message and message["pages"]:
            cols = st.columns(len(message["pages"]))
            for idx, p in enumerate(message["pages"]):
                img_path = f"page_images/page_{p}.png"
                if os.path.exists(img_path):
                    with cols[idx]:
                        st.image(img_path, caption=f"คู่มือหน้า {p}")

# --- Chat Interaction Area ---
# UI for Attachments (Floating over the chat input, on the right)
st.markdown('<div class="floating-attach">', unsafe_allow_html=True)
with st.popover("📎 แนบรูปภาพ"):
    uploaded_image = st.file_uploader("เลือกรูปภาพ", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    if uploaded_image:
        st.image(uploaded_image, caption="รูปที่เลือก")
st.markdown('</div>', unsafe_allow_html=True)

# Chat Input
if prompt := st.chat_input("พิมพ์คำถามเกี่ยวกับ G-Code ที่นี่..."):
    conv_id = st.session_state.current_conv_id
    conv = st.session_state.conversations[conv_id]
    
    # Store image data if any
    current_image_bytes = None
    if uploaded_image:
        current_image_bytes = uploaded_image.getvalue()

    # Auto-title from first message
    if not conv["messages"]:
        update_conversation_title(conv_id, prompt)

    # Add user message
    conv["messages"].append({
        "role": "user", 
        "content": prompt,
        "image": current_image_bytes
    })
    
    with st.chat_message("user"):
        st.markdown(prompt)
        if current_image_bytes:
            st.image(current_image_bytes, caption="รูปภาพแนบ")

    # Generate response
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown('<div class="thinking-box">🔍 AI กำลังวิเคราะห์ข้อมูล (และรูปภาพ)...</div>', unsafe_allow_html=True)
        
        response_placeholder = st.empty()
        full_response = ""
        
        # Retrieval
        docs = chatbot["retriever"].invoke(prompt)
        context = format_docs_with_pages(docs)
        
        # Identify pages for reference
        unique_pages = []
        seen_pages = set()
        for doc in docs:
            p = int(doc.metadata.get("page", 0)) + 1
            if p not in seen_pages:
                unique_pages.append(p)
                seen_pages.add(p)
        final_pages = unique_pages[:3]

        # Prepare Multimodal Message
        from langchain_core.messages import HumanMessage
        
        formatted_prompt_text = chatbot["prompt"].format(context=context, question=prompt)
        
        content_list = [{"type": "text", "text": formatted_prompt_text}]
        
        if current_image_bytes:
            # Convert to base64
            img_b64 = base64.b64encode(current_image_bytes).decode("utf-8")
            content_list.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
            })
            
        try:
            # Using ChatGoogleGenerativeAI with list of contents
            for chunk in chatbot["llm"].stream([HumanMessage(content=content_list)]):
                full_response += chunk.content
                response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            thinking_placeholder.empty()
            
            # Show images if relevant
            # Simple heuristic: don't show images if response is very short or looks like a rejection
            rejection_keywords = ["ขออภัย", "ไม่มีข้อมูล", "ไม่เข้าใจ"]
            is_rejected = any(kw in full_response for kw in rejection_keywords)
            
            pages_to_show = []
            if not is_rejected and final_pages:
                pages_to_show = final_pages
                st.markdown("---")
                st.subheader("📸 เอกสารที่เกี่ยวข้อง:")
                cols = st.columns(len(pages_to_show))
                for idx, p in enumerate(pages_to_show):
                    img_path = f"page_images/page_{p}.png"
                    if os.path.exists(img_path):
                        with cols[idx]:
                            st.image(img_path, caption=f"คู่มือหน้า {p}")
            
            # Save assistant message to current conversation
            conv["messages"].append({
                "role": "assistant", 
                "content": full_response, 
                "pages": pages_to_show
            })
            
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {str(e)}")
            thinking_placeholder.empty()
