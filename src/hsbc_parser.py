#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from table_parse import pdfParserTable
import struct
import datetime
import re
import pprint
import glob

meses = { 'ENE': 1, 'FEB': 2, 'MAR': 3, 'ABR': 4, 'MAY': 5, 'JUN': 6, 'JUL': 7, 'AGO': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DIC': 12 }

def parse_date(txtFecha, fecDefault):
    ''' Parsea un texto conteniendo dia y mes y devuelve una fecha con ese dia, y mes y el año de la fecha default
        o fecha por default (si el string esta vacio)'''
    if txtFecha:
        lfecha = txtFecha.split('-')
        #print(lfecha)
        fecDefault = datetime.date(fecDefault.year, meses[lfecha[1]], int(lfecha[0]))
    return fecDefault

def convert_float(txtNumero):
    '''Convierte un numero string a float'''
    if txtNumero:
        if txtNumero.endswith('-'):
            txtNumero = '{}{}'.format(txtNumero[-1:],txtNumero[:-1])
        try:
            return float(txtNumero.replace(',', ''))
        except ValueError:
            return 0.0
    return 0.0

def extract_hsbc_table(tabla, fecDefault, content=None):
    '''parsea una tabla generada por el extract de pdf para devolver los campos bien x delimitador de ancho'''
    omitir_txts = [u'- DETALLE DE OPERACIONES -',
                   u'FECHA              REFERENCIA                      NRO           DEBITO          CREDITO               SALDO',
                   u'7510224-7', u'7510224-0']
    stop_iteration = [u'_____________________________________________________________________________________________________________',
                      'NO HUBO NINGUNA ACTIVIDAD DURANTE EL PERIODO DEL EXTRACTO']
    if len(tabla) > 0 and len(tabla[0]) > 1:
        dummy_content = tabla[0][1].strip()
        if dummy_content in stop_iteration:
            return []
    fieldwidths = (8, -1, 40, 14, 9, 18, -10, 10)  # negative widths represent ignored padding fields
    fmtstring = ' '.join('{}{}'.format(abs(fw), 'x' if fw < 0 else 's') for fw in fieldwidths) #bytes para py3
    lenfmt = sum([abs(x) for x in fieldwidths])
    fieldstruct = struct.Struct(fmtstring)
    parse = fieldstruct.unpack_from
    # print('fmtstring: {!r}, recsize: {} chars'.format(fmtstring, fieldstruct.size))
    content = content or []
    i = [x[0] for x in tabla]
    for line in i:
        # print(line)
        stline = line.strip()
        if not stline or stline in omitir_txts or stline.startswith('HOJA') or stline in stop_iteration:
            continue
        if len(line) < lenfmt:
            line += ' ' * (lenfmt - len(line))
        try:
            fields = parse(bytes(line,"utf-8"))
            #print(fields)
            fields = [x.decode("utf-8").strip() for x in fields]
            if all( [ not val for val in fields ] ):
                continue
            if fields[1].startswith('-') or not content:
                fecDefault = parse_date(fields[0], fecDefault)
                fields[0] = fecDefault
                fields[1] = fields[1].replace('-','',1).strip()
                fields[3] = convert_float(fields[3])
                fields[4] = convert_float(fields[4])
                fields[5] = convert_float(fields[5])
                content.append(fields)
            else:
                newdesc = '{} {}'.format(content[-1][1], stline)
                content[-1][1] = newdesc
        except Exception as e:
            print(e)
            raise e
    #pprint.pprint(content)
    return content

def get_cuentas(pt):
    '''Extrae la info de las cuentas de un pdf'''
    detalle_cuentas = {}
    encabezado = pt.extactDocument(0, "EXTRACTO", "CUENTA CORRIENTE EN $ NRO.")
    omitir = [u' PRODUCTO', u'SUC', u'CUENTA', u'CBU', u'SALDO ANTERIOR', u'SALDO ACTUAL']
    cuentas = [re.split(r'\s{2,}', x[0]) for x in encabezado if re.split(r'\s{2,}', x[0]) != omitir]
    for cuenta in cuentas:
        cta_data = { 'nombre': cuenta[0] }
        spcuenta = cuenta[0].split()
        cta_data['moneda'] = spcuenta[-1]
        nomcuenta = ' '.join([x for x in spcuenta if x != cta_data['moneda']])
        cta_data['encabezado'] = u"{} EN {} NRO".format(nomcuenta, cta_data['moneda'])
        cta_data['numero'] = cuenta[2]
        cta_data['cbu'] = cuenta[3]
        cta_data['saldoant'] = cuenta[4]
        cta_data['saldoact'] = cuenta[5]
        detalle_cuentas[cta_data['nombre']] = cta_data
    return detalle_cuentas

def get_default_date(pt):
    '''Extrae el año del resumen'''
    periodo = pt.searchTextLine('EXTRACTO DEL', 0)[0][0].strip()
    periodoSep = periodo.split()
    return datetime.datetime.strptime(periodoSep[2],'%d/%m/%Y').date()

def get_accounts_with_transactions(fileName):
    '''Obtiene las cuentas y transacciones de un archivo'''
    pt = pdfParserTable(fileName)

    cuentas = get_cuentas(pt)

    fin_tabla = {u'CUENTA CORRIENTE EN $ NRO': '- RESUMEN DE ACUERDOS - (*)',
                 u'CAJA DE AHORRO EN u$s NRO': '- DETALLE DE INTERESES -',
                 u'CUENTA SUELDO EN $ NRO': '- DETALLE DE INTERESES -'}

    #cantcuentas = len(cuentas)
    #encabezados = [cuentas[x]['encabezado'] for x in cuentas]
    for cuenta in cuentas:
        fecDefault = get_default_date(pt)
        encabezado = cuentas[cuenta]['encabezado']
        pag_inicio = pt.searchInAllPages(encabezado)
        pag_fin = pt.searchInAllPages(fin_tabla[encabezado], pag_inicio['pag'], pag_inicio['y'])
        pag_next = 0
        if pag_fin is None or pag_inicio is None:
            cuentas[cuenta]['transacciones'] = []
            continue
        try:
            tabla = pt.extactDocument(pag_inicio['pag'], encabezado, fin_tabla[encabezado])
        except ValueError:
            tabla = pt.extactDocument(pag_inicio['pag'], encabezado)
        #print(tabla)
        content = extract_hsbc_table(tabla, fecDefault)
        if (pag_fin['pag'] - pag_inicio['pag']) > 1:
            pag_next = pag_inicio['pag'] + 1
            for page in range(pag_next, pag_fin['pag']):
                tabla = pt.parseRectangle(page)
                #print(tabla)
                content = extract_hsbc_table(tabla, fecDefault, content)
        tabla = pt.extactDocument(pag_fin['pag'], '', fin_tabla[encabezado])
        #print(tabla)
        content = extract_hsbc_table(tabla, fecDefault, content)
        cuentas[cuenta]['transacciones'] = content
    return cuentas

if __name__ == '__main__':
    for f in glob.glob(
            '/home/javier/Documentos/economia/bancos/hsbc/resumenes/resumen_nov_2019.pdf'):
        #    '/home/javier/Documentos/economia/bancos/hsbc/resumenes/resumen*.pdf'):
        print(f)
        allItems = get_accounts_with_transactions(f)
        pprint.pprint(allItems)
        