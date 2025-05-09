import os
import re
from docx import Document
# Đường dẫn thư mục
input_folder = "legal_docs"
output_file = "training_data.txt"
def read_docx(file_path):
    try:
        doc = Document(file_path)
        full_text = []
        for paragraph in doc.paragraphs:
            text = paragraph.text
            # Loại bỏ các ký tự đặc biệt và số
            text = re.sub(r'[^\w\s]', '', text)
            text = re.sub(r'\d+', '', text)
            full_text.append(text)
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""
def process_docx_files():
    try:
        # Mở file output để ghi
        with open(output_file, 'w', encoding='utf-8') as outfile:
            # Duyệt qua tất cả các file trong thư mục input
            for filename in os.listdir(input_folder):
                if filename.endswith(".docx"):
                    file_path = os.path.join(input_folder, filename)
                    text = read_docx(file_path)
                    if text:
                        outfile.write(f"Filename: {filename}\n{text}\n\n")
        print(f"All docx files processed. Output saved to {output_file}")
    except Exception as e:
        print(f"Error processing files: {e}")
if __name__ == "__main__":
    process_docx_files()


