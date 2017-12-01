# -*- coding: UTF-8 -*-
from budget_app.models import *
from budget_app.loaders import SimpleBudgetLoader
from decimal import *
import csv
import os
import re

class MaoBudgetLoader(SimpleBudgetLoader):

    def parse_item(self, filename, line):
        # Programme codes have changed in 2015, due to new laws. Since the application expects a code-programme
        # mapping to be constant over time, we are forced to amend budget data prior to 2015.
        # See https://github.com/dcabo/presupuestos-aragon/wiki/La-clasificaci%C3%B3n-funcional-en-las-Entidades-Locales
        programme_mapping = {
            # old programme: new programme
            '1340': '1350',     # Protección Civil
            '1350': '1360',     # Extinción de incendios
            '1550': '1532',     # Vías públicas
            '1620': '1621',     # Recogida de residuos
            '3130': '3110',     # Protección de la salud
            '3210': '3219',     # Educación preescolar y primaria
            '3220': '3229',     # Enseñanza secundaria
            '3230': '3239',     # Promoción educativa
            '3240': '3260',     # Servicios complementarios de educación
            '3340': '3341',     # Promoción cultural
            '4410': '4411',     # Promoción, mantenimiento y desarrollo del transporte
            '4940': '4911',     # URBAN- Arona 2007-2013
        }
        programme_mapping_2015 = {
            '3340': '3341',     # Promoción cultural
        }

        # Some dirty lines in input data
        if line[0]=='':
            return None

        is_expense = (filename.find('gastos.csv')!=-1)
        is_actual = (filename.find('/ejecucion_')!=-1)
        if is_expense:
            # The input data combines functional and economic codes in a very unusual way
            match = re.search('^ *(\d+) +(\d+) *', line[0])
            # We got 3- or 4- digit functional codes as input, so add a trailing zero
            fc_code = match.group(1).ljust(4, '0')
            ec_code = match.group(2)

            # For years before 2015 we check whether we need to amend the programme code
            year = re.search('municipio/(\d+)/', filename).group(1)
            if int(year) < 2015:
                fc_code = programme_mapping.get(fc_code, fc_code)
            elif int(year) == 2015:
                fc_code = programme_mapping_2015.get(fc_code, fc_code)

            return {
                'is_expense': True,
                'is_actual': is_actual,
                'fc_code': fc_code,
                'ec_code': ec_code[:-2],        # First three digits (everything but last two)
                'ic_code': '000',
                'item_number': ec_code[-2:],    # Last two digits
                'description': line[1],
                'amount': self._parse_amount(line[5 if is_actual else 2])
            }

        else:
            return {
                'is_expense': False,
                'is_actual': is_actual,
                'ec_code': line[0][:-2],        # First three digits
                'ic_code': '000',               # All income goes to the root node
                'item_number': line[0][-2:],    # Fourth and fifth digit; careful, there's trailing dirt
                'description': line[1],
                'amount': self._parse_amount(line[5 if is_actual else 2])
            }
