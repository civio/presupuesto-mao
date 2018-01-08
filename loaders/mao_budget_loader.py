# -*- coding: UTF-8 -*-
from budget_app.models import *
from budget_app.loaders import SimpleBudgetLoader
import re


class MaoCsvMapper:
    expenses_mapping = {
        '2016': {'ic_code': 2, 'fc_code': 3, 'full_ec_code': 4, 'description': 5, 'forecast_amount': 6, 'actual_amount': 11},
        '2015': {'ic_code': 2, 'fc_code': 3, 'full_ec_code': 4, 'description': 5, 'forecast_amount': 6, 'actual_amount': 9},
    }

    income_mapping = {
        '2016': {'full_ec_code': 2, 'description': 3, 'forecast_amount': 4, 'actual_amount': 9},
        '2015': {'full_ec_code': 2, 'description': 3, 'forecast_amount': 4, 'actual_amount': 8},
    }

    default = '2016'

    def __init__(self, year, is_expense):
        column_mapping = MaoCsvMapper.expenses_mapping

        if not is_expense:
            column_mapping = MaoCsvMapper.income_mapping

        mapping = column_mapping.get(year)

        if not mapping:
            mapping = column_mapping.get(MaoCsvMapper.default)

        self.ic_code = mapping.get('ic_code')
        self.fc_code = mapping.get('fc_code')
        self.full_ec_code = mapping.get('full_ec_code')
        self.description = mapping.get('description')
        self.forecast_amount = mapping.get('forecast_amount')
        self.actual_amount = mapping.get('actual_amount')


class MaoBudgetLoader(SimpleBudgetLoader):
    def parse_item(self, filename, line):
        # Type of data
        is_expense = (filename.find('gastos.csv') != -1)
        is_actual = (filename.find('/ejecucion_') != -1)

        # Year
        year = re.search('municipio/(\d+)/', filename).group(1)

        # Mapper
        mapper = MaoCsvMapper(year, is_expense)

        # Expenses
        if is_expense:
            # Institutional code
            # We only need the digits for the service (the first two)
            ic_code = line[mapper.ic_code].strip()[:2].ljust(3, 'X')

            # Functional code
            # We got decimal values as input, so we normalize them at 4- and add leading zeroes when required
            fc_code = line[mapper.fc_code].split('.')[0].rjust(4, '0')

            # Economic code
            # We got decimal values as input, so we normalize them at 7- and add leading zeroes when required
            full_ec_code = line[mapper.full_ec_code].split('.')[0].rjust(7, '0')

            # Concepts are the firts three digits from the economic codes
            ec_code = full_ec_code[:3]

            # Item numbers are the last four digits from the economic codes (digits four to seven)
            item_number = full_ec_code[-4:]

            # Description
            description = line[mapper.description].strip().upper()

            # Parse amount
            amount = line[mapper.actual_amount if is_actual else mapper.forecast_amount].strip()
            amount = self._parse_amount(amount)

        # Income
        else:
            # Institutional code (all income goes to the root node)
            ic_code = '000'

            # Functional code
            # We don't have a functional code in income
            fc_code = None

            # Economic code
            # We got decimal values as input, so we normalize them at 5- and add leading zeroes when required
            full_ec_code = line[mapper.full_ec_code].split('.')[0].rjust(5, '0')

            # Concepts are the firts three digits from the economic codes
            ec_code = full_ec_code[:3]

            # Item numbers are the last two digits from the economic codes (digits four and five)
            item_number = full_ec_code[-2:]

            # Description
            description = line[mapper.description].strip()

            # Parse amount
            amount = line[mapper.actual_amount if is_actual else mapper.forecast_amount].strip()
            amount = self._parse_amount(amount)

        return {
            'is_expense': is_expense,
            'is_actual': is_actual,
            'fc_code': fc_code,
            'ec_code': ec_code,
            'ic_code': ic_code,
            'item_number': item_number,
            'description': description,
            'amount': amount
        }
