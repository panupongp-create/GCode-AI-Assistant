import os, re
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

def format_docs_with_pages(docs):
    formatted = ""
    for doc in docs:
        p = int(doc.metadata.get("page", 0)) + 1
        formatted += f"--- ข้อมูลหน้า {p} ---\n{doc.page_content}\n\n"
    return formatted

_response_cache = {}

def create_chatbot(db):
    cpu_threads = os.cpu_count() or 4
    llm = OllamaLLM(
        model="llama3.2:3b", 
        temperature=0.4, # เพิ่ม Temperature เล็กน้อยเพื่อให้วิเคราะห์ได้ลื่นไหลขึ้น
        num_ctx=8192,    # เพิ่ม Context window ให้จำรายละเอียดได้มากขึ้น
        num_thread=cpu_threads,
        keep_alive="30m"
    )

    template = """คุณคือ "วิศวกรผู้เชี่ยวชาญระบบ G-Code และที่ปรึกษาด้านเทคนิคอาวุโส"
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
5. ตอบเป็น "ภาษาไทย" เท่านั้น ห้ามมีภาษาจีนหรือภาษาอื่นปน (ยกเว้นคำศัพท์ทางเทคนิคที่เป็นภาษาอังกฤษที่จำเป็น)
6. ห้ามใช้คำว่า "保存" ให้ใช้คำว่า "บันทึก" หรือ "บันทึกข้อมูล" แทนเท่านั้น

คู่มืออ้างอิง:
{context}

คำถาม: {question}
การวิเคราะห์และคำตอบจากวิศวกร:"""

    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    retriever = db.as_retriever(search_kwargs={"k": 6}) # เพิ่มข้อมูลอ้างอิงเป็น 6 ชิ้นเพื่อให้ AI เห็นภาพกว้างขึ้น
    return {"llm": llm, "prompt": prompt, "retriever": retriever}

def ask_question(chatbot, question, on_token_callback, stop_event=None):
    try:
        retriever = chatbot["retriever"]
        prompt = chatbot["prompt"]
        llm = chatbot["llm"]

        docs = retriever.invoke(question)
        
        # กรองหน้าซ้ำ
        unique_pages = []
        seen_pages = set()
        for doc in docs:
            p = int(doc.metadata.get("page", 0)) + 1
            if p not in seen_pages:
                unique_pages.append(p)
                seen_pages.add(p)
        
        final_pages = unique_pages[:3]
        context = format_docs_with_pages(docs)
        thinking_text = f"⚙️ วิศวกรกำลังตรวจสอบคู่มือ..."
        
        # ส่งข้อความ thinking ก่อน แต่ยังไม่ส่งรูป (ส่ง [] ก่อน)
        on_token_callback("", thinking_text, [])

        # เริ่ม Stream
        full_answer = ""
        formatted_prompt = prompt.format(context=context, question=question)
        
        for chunk in llm.stream(formatted_prompt):
            if stop_event and stop_event.is_set(): break
            full_answer += chunk
            # ยังไม่ส่งรูประหว่าง Stream
            on_token_callback(chunk, thinking_text, [])

        # ตรวจสอบเจตนาการปฏิเสธ (เฉพาะเมื่อหาข้อมูลไม่ได้เลยจริงๆ)
        rejection_keywords = ["ขออภัยครับ ข้อมูลส่วนนี้ไม่มีอยู่ในคู่มือ", "ผมไม่เข้าใจคำถามของคุณ"]
        is_hard_rejected = any(kw in full_answer for kw in rejection_keywords)
        
        # แสดงรูปหากไม่ใช่การปฏิเสธแบบเด็ดขาด
        display_pages = [] if is_hard_rejected else final_pages
        on_token_callback("", thinking_text, display_pages)

        return {"answer": full_answer, "pages": display_pages}

    except Exception as e:
        on_token_callback(f"❌ Error: {str(e)}", "Error", [])
        return None

def prewarm_model(chatbot):
    try: chatbot["llm"].invoke("hi")
    except: pass