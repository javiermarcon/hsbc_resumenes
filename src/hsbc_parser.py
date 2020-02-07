#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from table_parse import pdfParserTable
from categories_and_tags import tagsRegexps
import struct
import datetime
import re
import os
import glob
import csv

meses = { 'ENE': 1, 'FEB': 2, 'MAR': 3, 'ABR': 4, 'MAY': 5, 'JUN': 6, 'JUL': 7, 'AGO': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DIC': 12 }

monedas = {'$': 'ARS', 'u$s': 'USD'}

fin_tabla = {u'CUENTA CORRIENTE EN $ NRO': ['- RESUMEN DE ACUERDOS - (*)'],
                 u'CAJA DE AHORRO EN u$s NRO': ['- SALDO FINAL', '- DETALLE DE INTERESES -'],
                 u'CUENTA SUELDO EN $ NRO': ['- SALDO FINAL', '- DETALLE DE INTERESES -']}

def get_cat_and_tag(trans):
    '''Gets the corresponding category and tag from tagsRegexps
    tagsRegexps = {'search_string': (u'tag', u'category'), ... }
    '''
    res = [val for key, val in tagsRegexps.items() if key in trans[1] and key]
    if res:
        return res[0]
    return ('', '')

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
    skip_starts = ['HOJA', 'EXTRACTO DE']
    #print(tabla)
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
        startSkip = any([ stline.startswith(x) for x in skip_starts])
        if not stline or stline in omitir_txts or startSkip or stline in stop_iteration:
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
    detalle_cuentas = []
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
        detalle_cuentas.append(cta_data)

    return detalle_cuentas

def get_pag_inicio_fin( pt, accounts):
    """

    :rtype: object
    """
    ret = []
    for account in accounts:
        account['pag_inicio'] = pt.searchInAllPages(account['encabezado'])
        account['pag_fin'] = None
        for texto_buscar in fin_tabla[account['encabezado']]:
            account['pag_fin'] = pt.searchInAllPages(texto_buscar, account['pag_inicio']['pag'], account['pag_inicio']['y'])
            if account['pag_fin']:
                break
        ret.append(account)

    pag_ant = None
    reversed_pags = reversed(list(enumerate(ret)))
    for nro, pag in reversed_pags:
        if pag_ant:
            pf = ret[nro]['pag_fin']
            if not pf or pag_ant['pag'] < pf['pag'] or (pag_ant['pag'] == pf['pag'] and pag_ant['y'] < pf['y']):
                ret[nro]['pag_fin'] = pag_ant
        if nro:
            pag_ant = ret[nro]['pag_inicio']
    return ret

def get_default_date(pt):
    '''Extrae el año del resumen'''
    periodo = pt.searchTextLine('EXTRACTO DEL', 0)[0][0].strip()
    periodoSep = periodo.split()
    return datetime.datetime.strptime(periodoSep[2],'%d/%m/%Y').date()

def get_accounts_with_transactions(fileName):
    '''Obtiene las cuentas y transacciones de un archivo'''
    pt = pdfParserTable(fileName)

    cuentas = get_pag_inicio_fin(pt, get_cuentas(pt))


    #cantcuentas = len(cuentas)
    #encabezados = [cuentas[x]['encabezado'] for x in cuentas]
    for cuenta in cuentas:
        fecDefault = get_default_date(pt)
        encabezado = cuenta['encabezado']
        pag_next = 0
        pag_inicio = cuenta['pag_inicio']
        pag_fin = cuenta['pag_fin']
        if pag_fin is None or pag_inicio is None:
            cuenta['transacciones'] = []
            continue
        try:
            tabla = pt.extactDocument(pag_inicio['pag'], encabezado, fin_tabla[encabezado][0])
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
        tabla = pt.extactDocument(pag_fin['pag'], '', fin_tabla[encabezado][0])
        #print(tabla)
        content = extract_hsbc_table(tabla, fecDefault, content)
        cuenta['transacciones'] = content
    return cuentas

def get_transactions(location='/home/javier/Documentos/economia/bancos/hsbc/resumenes', pattern='resumen*.pdf'):
    '''Gets the transactions'''
    transactions = {}
    for f in glob.glob(os.path.join(location, pattern)):
        #print(f)
        allItems = get_accounts_with_transactions(f)
        # pprint.pprint(allItems)
        for item in allItems:
            nomcta = '{encabezado} {numero}'.format(**item)
            moneda = monedas[item['moneda']]
            cta_ing = '{}_ingresos'.format(nomcta)
            cta_gas = '{}_gastos'.format(nomcta)
            if cta_ing not in transactions:
                transactions[cta_ing] = []
                transactions[cta_gas] = []
            for trans in item['transacciones']:
                if trans[3] == 0.0 and trans[4] == 0.0:
                    continue # no hay movimiento
                else:
                    if trans[4] == 0.0:
                        # gasto
                        importe = trans[3]
                        cta = cta_gas
                    else:
                        # ingreso
                        importe = trans[4]
                        cta = cta_ing
                    tag, categoria = get_cat_and_tag(trans)
                    #                              fecha     descr    moneda    nro      importe  categoria, tag
                    transactions[cta].append([trans[0], trans[1], moneda, trans[2], importe, categoria, tag])

    for cta in transactions:
        lc = len(transactions[cta])
        if not lc:
            print('No hay transacciones para {}'.format(cta))
            continue
        print('Generando csv de {} transacciones para {}'.format(lc, cta))
        with open('/tmp/{}.csv'.format(cta), 'a') as outcsv:
            # configure writer to write standard csv file
            writer = csv.writer(outcsv, delimiter=',', lineterminator='\n') # quotechar='|', quoting=csv.QUOTE_MINIMAL,
            writer.writerow(["fecha", "desc", 'moneda', "nro", "importe", 'categoria', 'tag'])
            for item in transactions[cta]:
                # Write item to outcsv
                writer.writerow(item)

    return transactions

if __name__ == '__main__':
    get_transactions()

        