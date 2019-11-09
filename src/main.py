
import os
import pprint


def savepath(numero):
    dest = '/tmp/pdfprueba_{}.pdf'.format(numero)

def save(texto, filename):
    with open(filename, 'w+') as arch:
        arch.write(texto)

folderPath = '/home/javier/Documentos/economia/bancos/hsbc/resumenes'
fileName = 'resumen_feb_2019.pdf'
filePath = os.path.join(folderPath, fileName)
"""
from tika import parser
raw = parser.from_file(filePath)
text1 = raw['content']
detOp = '- DETALLE DE OPERACIONES -'
"""
import fitz
# https://pymupdf.readthedocs.io/en/latest/app2/#appendix2
doc = fitz.open(filePath)
text = []
for page in doc:
    t = page.getText().encode("utf8")
    text.append(t)
print(text)

page = doc[0]
d = page.getText("dict")
pprint.pprint(d)
"""
import camelot
tables = camelot.read_pdf(filePath)
"""

from tabula import read_pdf
import pandas as pd
pd.set_option('display.max_rows', 700)
pd.set_option('display.max_columns', 700)
pd.set_option('display.width', 2000)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
x = read_pdf('/home/javier/proyectos/finanzas/hsbc_resumenes/docs/resumen_feb_2019.pdf', pages='all', multiple_tables=True, stream=True, guess=False)
