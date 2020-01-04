#!/usr/bin/python
# -*- coding: utf-8 -*-
import unittest
from src.hsbc_parser import *

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


if __name__ == '__main__':
    unittest.main()
