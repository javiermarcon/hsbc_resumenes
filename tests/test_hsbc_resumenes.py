#!/usr/bin/python
# -*- coding: utf-8 -*-
import unittest
import mock
from src.hsbc_parser import *
from src.table_parse import pdfParserTable

class TableParserTest(unittest.TestCase):
    def test_months(self):
        ''' ests that moths var has 12 months '''
        self.assertEqual(len(meses), 12)

    def test_parse_date(self):
        ''' Testea la conversion de un string con dia y mes a date (tomando el año de la fecha default)
            o la fecha default si el texto esta vacio '''
        parameters_and_expected = [('10-NOV', datetime.date(2019, 6, 15), datetime.date(2019, 11, 10)),
                  ('6-FEB', datetime.date(2020, 6, 15), datetime.date(2020, 2, 6)),
                  ('', datetime.date(2019, 6, 15), datetime.date(2019, 6, 15))]
        for data in parameters_and_expected:
            fecha = parse_date(data[0], data[1])
            self.assertEqual(fecha, data[2])

    def test_parse_wrong_date(self):
        ''' Testea la conversion de un string con dia y mes a date (tomando el año de la fecha default)
            o la fecha default si el texto esta vacio '''
        parameters_and_expected = [('-NOV', datetime.date(2019, 6, 15), ValueError),
                      ('6-asd', datetime.date(2020, 6, 15), KeyError),
                      ('10-NOV', 'hola', AttributeError),
                      ('hola', datetime.date(2019, 6, 15), IndexError)]
        for data in parameters_and_expected:
            with self.assertRaises(data[2]):
                parse_date(data[0], data[1])

    def test_convert_float(self):
        ''' Testea la conversion de un string con un numero a el valor float de ese numero.
            Devuelve 0.0 si no pudo convertirlo '''
        parameters_and_expected = [('3.14', 3.14), ('3.14-', -3.14), ('2,743.14', 2743.14),
                                   ('31', 31.0), ('31-', -31.0), ('5,833.14-', -5833.14),
                                   ('1,645,833.14-', -1645833.14), ('asado', 0.0), ('', 0.0)]
        for data in parameters_and_expected:
            self.assertEqual(convert_float(data[0]), data[1])

    @mock.patch('src.table_parse.fitz')
    @mock.patch('src.hsbc_parser.pdfParserTable.searchInAllPages')
    def test_start_stop_date(self, mock_search_all_pages, mock_fizz):
        search_parameters = [
            # 1 table x page
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 2, 'y': 100.11}, {'pag': 2, 'y': 530.22}],
             [{'pag': 3, 'y': 300.35}, {'pag': 3, 'y': 350}]],
            # 3 tables same page
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 1, 'y': 450.11}, {'pag': 1, 'y': 530.22}],
             [{'pag': 1, 'y': 600.35}, {'pag': 1, 'y': 650}]],
            # 1 table 2 pages
            [[{'pag': 1, 'y': 200.25}, {'pag': 2, 'y': 400.15}],
             [{'pag': 2, 'y': 500.11}, {'pag': 2, 'y': 530.22}],
             [{'pag': 3, 'y': 300.35}, {'pag': 3, 'y': 350}]],
            # 1 table many pages
            [[{'pag': 1, 'y': 200.25}, {'pag': 5, 'y': 400.15}],
             [{'pag': 5, 'y': 100.11}, {'pag': 5, 'y': 530.22}],
             [{'pag': 6, 'y': 300.35}, {'pag': 6, 'y': 350}]],
            # 1 table many pages mid
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 2, 'y': 100.11}, {'pag': 5, 'y': 530.22}],
             [{'pag': 5, 'y': 600.35}, {'pag': 3, 'y': 650}]],
            # 1 table many pages at end
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 2, 'y': 100.11}, {'pag': 2, 'y': 530.22}],
             [{'pag': 2, 'y': 300.35}, {'pag': 6, 'y': 350}]],
            # null at first
            [[{'pag': 1, 'y': 200.25}, None],
             [{'pag': 2, 'y': 100.11}, {'pag': 2, 'y': 330.22}],
             [{'pag': 2, 'y': 600.35}, {'pag': 3, 'y': 350}]],
            # null mid
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 2, 'y': 100.11}, None],
             [{'pag': 2, 'y': 300.35}, {'pag': 3, 'y': 350}]],
            # null end
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 2, 'y': 100.11}, {'pag': 2, 'y': 530.34}],
             [{'pag': 3, 'y': 300.35}, None]],
            # 3 null same page
            [[{'pag': 1, 'y': 200.25}, None],
             [{'pag': 1, 'y': 100.11}, None],
             [{'pag': 1, 'y': 300.35}, None]],
            # table multipe pages followed by null
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 1, 'y': 450.11}, {'pag': 3, 'y': 130.22}],
             [{'pag': 3, 'y': 300.35}, None]],
            # null followed by table multiple pages
            [[{'pag': 1, 'y': 200.25}, None],
             [{'pag': 1, 'y': 250.11}, {'pag': 4, 'y': 330.22}],
             [{'pag': 4, 'y': 500.35}, {'pag': 5, 'y': 350}]],
            # 1 table multiple pages followed and preceeded by null
            [[{'pag': 1, 'y': 200.25}, None],
             [{'pag': 1, 'y': 300.11}, {'pag': 6, 'y': 530.22}],
             [{'pag': 6, 'y': 300.35}, None]]
        ]
        expected = [
            # 1 table x page
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 2, 'y': 100.11}, {'pag': 2, 'y': 530.22}],
             [{'pag': 3, 'y': 300.35}, {'pag': 3, 'y': 350}]],
            # 3 tables same page
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 1, 'y': 450.11}, {'pag': 1, 'y': 530.22}],
             [{'pag': 1, 'y': 600.35}, {'pag': 1, 'y': 650}]],
            # 1 table 2 pages
            [[{'pag': 1, 'y': 200.25}, {'pag': 2, 'y': 400.15}],
             [{'pag': 2, 'y': 500.11}, {'pag': 2, 'y': 530.22}],
             [{'pag': 3, 'y': 300.35}, {'pag': 3, 'y': 350}]],
            # 1 table many pages
            [[{'pag': 1, 'y': 200.25}, {'pag': 5, 'y': 400.15}],
             [{'pag': 5, 'y': 100.11}, {'pag': 5, 'y': 530.22}],
             [{'pag': 6, 'y': 300.35}, {'pag': 6, 'y': 350}]],
            # 1 table many pages mid
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 2, 'y': 100.11}, {'pag': 5, 'y': 530.22}],
             [{'pag': 5, 'y': 600.35}, {'pag': 3, 'y': 650}]],
            # 1 table many pages at end
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 2, 'y': 100.11}, {'pag': 2, 'y': 530.22}],
             [{'pag': 2, 'y': 300.35}, {'pag': 6, 'y': 350}]],
            # null at first
            [[{'pag': 1, 'y': 200.25}, {'pag': 2, 'y': 100.11}],
             [{'pag': 2, 'y': 100.11}, {'pag': 2, 'y': 330.22}],
             [{'pag': 2, 'y': 600.35}, {'pag': 3, 'y': 350}]],
            # null mid
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 2, 'y': 100.11}, {'pag': 2, 'y': 300.35}],
             [{'pag': 2, 'y': 300.35}, {'pag': 3, 'y': 350}]],
            # null end
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 2, 'y': 100.11}, {'pag': 2, 'y': 530.34}],
             [{'pag': 3, 'y': 300.35}, None]],
            # 3 null same page
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 100.11}],
             [{'pag': 1, 'y': 100.11}, {'pag': 1, 'y': 300.35}],
             [{'pag': 1, 'y': 300.35}, None]],
            # table multipe pages followed by null
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 400.15}],
             [{'pag': 1, 'y': 450.11}, {'pag': 3, 'y': 130.22}],
             [{'pag': 3, 'y': 300.35}, None]],
            # null followed by table multiple pages
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 250.11}],
             [{'pag': 1, 'y': 250.11}, {'pag': 4, 'y': 330.22}],
             [{'pag': 4, 'y': 500.35}, {'pag': 5, 'y': 350}]],
            # 1 table multiple pages followed and preceeded by null
            [[{'pag': 1, 'y': 200.25}, {'pag': 1, 'y': 300.11}],
             [{'pag': 1, 'y': 300.11}, {'pag': 6, 'y': 530.22}],
             [{'pag': 6, 'y': 300.35}, None]]
        ]
        pt = pdfParserTable('doc.pdf')
        cuentas = [{'nombre': ' CUENTA CORRIENTE $',
                                           'moneda': '$',
                                           'encabezado': 'CUENTA CORRIENTE EN $ NRO',
                                           'numero': '1001-12345-0',
                                           'cbu': '15000541 00010011234500',
                                           'saldoant': '121.26', 'saldoact': '121.26'},
                   {'nombre': ' CAJA DE AHORRO u$s',
                                           'moneda': 'u$s',
                                           'encabezado': 'CAJA DE AHORRO EN u$s NRO',
                                           'numero': '100-2-23456-6',
                                           'cbu': '15000541 00010022345664',
                                           'saldoant': '1,032.33', 'saldoact': '980.98'},
                   {'nombre': ' CUENTA SUELDO $',
                                        'moneda': '$',
                                        'encabezado': 'CUENTA SUELDO EN $ NRO',
                                        'numero': '100-3-54321-8',
                                        'cbu': '15000541 000100354321182',
                                        'saldoant': '27,958.90',
                                        'saldoact': '50,750.33'}]
        for nroparam, parameters in enumerate(search_parameters):
            if not len(parameters):
                print(parameters)
            flatten_items = [item for sublist in parameters for item in sublist]
            print(len(flatten_items))
            mock_search_all_pages.side_effect = flatten_items
            res = get_pag_inicio_fin(pt, cuentas)
            for nrolin, tabla in enumerate(expected[nroparam]):
                self.assertDictEqual(res[nrolin]['pag_inicio'], tabla[0])
                if tabla[1] and res[nrolin]['pag_fin']:
                    self.assertDictEqual(res[nrolin]['pag_fin'], tabla[1])
                else:
                    print(res[nrolin]['pag_fin'])
                    self.assertIsNone(res[nrolin]['pag_fin'])


if __name__ == '__main__':
    unittest.main()
