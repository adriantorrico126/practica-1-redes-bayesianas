"""Genera la versión para Class Notebook sin resumen, conclusiones ni anexo."""
from pathlib import Path
from docx import Document

ROOT = Path(__file__).parent
SOURCE = ROOT / 'Informe_Practica_1_Redes_Bayesianas_Adrian_Torrico.docx'
TARGET = ROOT / 'Informe_Practica_1_Redes_Bayesianas_Adrian_Torrico_Class_Notebook.docx'

doc = Document(SOURCE)
remove_ranges = [
    ('Resumen ejecutivo', '1. Objetivo y datos'),
    ('9. Conclusiones y recomendaciones', None),
]

for start, stop in remove_ranges:
    deleting = False
    for paragraph in list(doc.paragraphs):
        if paragraph.text.strip() == start:
            deleting = True
        if deleting and paragraph.text.strip() == stop:
            deleting = False
        if deleting:
            paragraph._element.getparent().remove(paragraph._element)

doc.save(TARGET)
print(TARGET)
