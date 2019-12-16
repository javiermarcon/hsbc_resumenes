#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from table_parse import pdfParserTable
import struct
import datetime
import re
import pprint

def parsear_fecha(txtFecha, fecDefault):
    return (txtFecha, fecDefault)

def extract_hsbc_table(tabla, fecDefault):
    '''parsea una tabla generada por el extract de pdf para devolver los campos bien x delimitador de ancho'''
    fieldwidths = (8, -1, 40, 14, 9, 18, -10, 10)  # negative widths represent ignored padding fields
    fmtstring = ' '.join('{}{}'.format(abs(fw), 'x' if fw < 0 else 's') for fw in fieldwidths) #bytes para py3
    lenfmt = sum([abs(x) for x in fieldwidths])
    fieldstruct = struct.Struct(fmtstring)
    parse = fieldstruct.unpack_from
    # print('fmtstring: {!r}, recsize: {} chars'.format(fmtstring, fieldstruct.size))
    content = []
    i = [x[0] for x in tabla]
    for line in i:
        # print(line)
        omitir_txts = [u'- DETALLE DE OPERACIONES -',
                       u'FECHA              REFERENCIA                      NRO           DEBITO          CREDITO               SALDO',
                       u'7510224-7',
                       u'_____________________________________________________________________________________________________________']
        stline = line.strip()
        if stline in omitir_txts:
            continue
        if len(line) < lenfmt:
            line += ' ' * (lenfmt - len(line))
        try:
            fields = parse(line)
            #print(fields)
            fields = [x.strip() for x in fields]
            #print(fields)
            if all( not v for v in fields):
                continue
            if fields[1].startswith('-') or not content:
                fields[0], fecDefault = parsear_fecha(fields[0], fecDefault)
                fields[1] = fields[1].replace('-','',1).strip()
                content.append(fields)
            else:
                newdesc = '{} {}'.format(content[-1][1], stline)
                content[-1][1] = newdesc
        except Exception as e:
            print(e)
    #pprint.pprint(content)
    return content

def get_cuentas(pt):
    '''Extrae la info de las cuentas de un pdf'''
    encabezado = pt.extactDocument(0, "EXTRACTO", "CUENTA CORRIENTE EN $ NRO.")
    omitir = [u' PRODUCTO', u'SUC', u'CUENTA', u'CBU', u'SALDO ANTERIOR', u'SALDO ACTUAL']
    return [re.split(r'\s{2,}', x[0]) for x in encabezado if re.split(r'\s{2,}', x[0]) != omitir]

def get_default_date(pt):
    '''Extrae el año del resumen'''
    periodo = pt.searchTextLine('EXTRACTO DEL', 0)[0][0].strip()
    periodoSep = periodo.split()
    return datetime.datetime.strptime(periodoSep[2],'%d/%m/%Y').date()

pt = pdfParserTable('/home/javier/proyectos/finanzas/hsbc_resumenes/docs/resumen_feb_2019.pdf')
fecDefault = get_default_date(pt)
cuentas = get_cuentas(pt)
for cuenta in cuentas:
    print(len(cuenta), cuenta)

fin_tabla = {u'CUENTA CORRIENTE EN $ NRO': '- RESUMEN DE ACUERDOS - (*)',
             u'CAJA DE AHORRO EN u$s NRO': '- DETALLE DE INTERESES -',
             u'CUENTA SUELDO EN $ NRO': '- DETALLE DE INTERESES -'}

cantcuentas = len(cuentas)

for cuenta in cuentas:
    content = []
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
    try:
        tabla = pt.extactDocument(pag_inicio, encabezado, fin_tabla[encabezado])
    except ValueError:
        tabla = pt.extactDocument(pag_inicio, encabezado)
    content.extend(extract_hsbc_table(tabla, fecDefault))
    if (pag_fin - pag_inicio) > 1:
        pag_next = pag_inicio + 1
        for page in range(pag_next. pag_fin):
            tabla = pt.parseRectangle(page)
            content.extend(extract_hsbc_table(tabla, fecDefault))
    tabla = pt.extactDocument(pag_fin, '', fin_tabla[encabezado])
    content.extend(extract_hsbc_table(tabla, fecDefault))
    pprint.pprint(content)
