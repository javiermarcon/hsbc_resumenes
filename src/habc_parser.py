#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from table_parse import pdfParserTable
import struct
import re

def extract_hsbc_table(tabla):
    fieldwidths = (
    9, -2, 50 - 11, 65 - 51, 74 - 66, 94 - 75, -10, 10)  # negative widths represent ignored padding fields
    fmtstring = ' '.join('{}{}'.format(abs(fw), 'x' if fw < 0 else 's') for fw in fieldwidths)
    lenfmt = sum([abs(x) for x in fieldwidths])
    fieldstruct = struct.Struct(fmtstring)
    parse = fieldstruct.unpack_from
    # print('fmtstring: {!r}, recsize: {} chars'.format(fmtstring, fieldstruct.size))

    i = [x[0] for x in tabla]
    for line in i:
        # print(line)
        if len(line) < lenfmt:
            line += ' ' * (lenfmt - len(line))
        try:
            fields = parse(line)
            print('fields: {}'.format(fields))
        except Exception as e:
            print(e)



pt = pdfParserTable('/home/javier/proyectos/finanzas/hsbc_resumenes/docs/resumen_feb_2019.pdf')
encabezado = pt.extactDocument(0, "EXTRACTO", "CUENTA CORRIENTE EN $ NRO.")
omitir = [u' PRODUCTO', u'SUC', u'CUENTA', u'CBU', u'SALDO ANTERIOR', u'SALDO ACTUAL']

cuentas = [ re.split(r'\s{2,}',x[0]) for x in encabezado if re.split(r'\s{2,}',x[0]) != omitir]
for cuenta in cuentas:
    print(len(cuenta), cuenta)

omitir_tabla = [[u'-',u'DETALLE DE OPERACIONES','-'],
[u'FECHA',u'REFERENCIA',u'NRO',u'DEBITO',u'CREDITO',u'SALDO']]

fin_tabla = {u'CUENTA CORRIENTE EN $ NRO': '- RESUMEN DE ACUERDOS - (*)',
             u'CAJA DE AHORRO EN u$s NRO': '- DETALLE DE INTERESES -',
             u'CUENTA SUELDO EN $ NRO': '- DETALLE DE INTERESES -'}

cantcuentas = len(cuentas)

for cuenta in cuentas:
    spcuenta = cuenta[0].split()
    moneda = spcuenta[-1]
    nomcuenta = ' '.join([x for x in spcuenta if x != moneda])
    encabezado = u"{} EN {} NRO".format(nomcuenta, moneda)
    pag_inicio = pt.searchInAllPages(encabezado)
    pag_fin = pt.searchInAllPages(fin_tabla[encabezado], pag_inicio)
    nro = cuenta[2]
    cbu = cuenta[3]
    saldoant = cuenta[4]
    saldoact = cuenta[5]
    print(encabezado)
    tabla = pt.extactDocument(pag_inicio, encabezado, fin_tabla[encabezado])
    extract_hsbc_table(tabla)
    if (pag_fin - pag_inicio) > 1:
        pag_next = pag_inicio + 1
        for page in range(pag_next. pag_fin):
            tabla = pt.parseRectangle(page)
            extract_hsbc_table(tabla)
    tabla = pt.extactDocument(pag_fin, '', fin_tabla[encabezado])
    extract_hsbc_table(tabla)
