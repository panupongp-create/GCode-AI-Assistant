import fitz  # PyMuPDF
import os

def extract_pdf_pages_as_images(pdf_path, output_folder="page_images"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    doc = fitz.open(pdf_path)
    print(f"Converting PDF {len(doc)} pages to images...")
    
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        # ปรับความคมชัด (zoom)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
        output_path = os.path.join(output_folder, f"page_{page_index + 1}.png")
        pix.save(output_path)
        
    print(f"✅ Success: {output_folder}")
    doc.close()

if __name__ == "__main__":
    pdf_path = "manual_GCodeV4 (1).pdf"
    if os.path.exists(pdf_path):
        extract_pdf_pages_as_images(pdf_path)
    else:
        # หาไฟล์ PDF อื่นๆ
        pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
        if pdf_files:
            extract_pdf_pages_as_images(pdf_files[0])
