from pypdf import PdfReader
import os 

PATH = r'C:\Users\NoahY\OneDrive\Documents\Finances\Banking\Chase Statements\Credit Card statements\2024.03.25'
PDF_DIR = os.path.normpath(PATH)

for filename in os.listdir(PDF_DIR):
    reader = PdfReader(PDF_DIR + '\\' + filename)
    number_of_pages = len(reader.pages)
    for pg_num in range(0, number_of_pages):
        page = reader.pages[pg_num]
        text = page.extract_text()
        print(text)
    
