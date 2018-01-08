# -*- coding: UTF-8 -*-
from budget_app.models import *
from budget_app.loaders import SimpleBudgetLoader


class MaoBudgetLoader(SimpleBudgetLoader):

    def parse_item(self, filename, line):
        # Type of data
        is_expense = (filename.find('gastos.csv') != -1)
        is_actual = (filename.find('/ejecucion_') != -1)

        # Expenses
        if is_expense:
            # Institutional code
            # We only need the digits for the service (the first two)
            ic_code = line[2].strip()[:2].ljust(3, 'X')

            # Functional code
            # We got decimal values as input, so we normalize them at 4- and add leading zeroes when required
            fc_code = line[3].split('.')[0].rjust(4, '0')

            # Economic code
            # We got decimal values as input, so we normalize them at 7- and add leading zeroes when required
            full_ec_code = line[4].split('.')[0].rjust(7, '0')

            # Concepts are the firts three digits from the economic codes
            ec_code = full_ec_code[:3]

            # Item numbers are the last four digits from the economic codes (digits four to seven)
            item_number = full_ec_code[-4:]

            # Description
            description = line[5].strip().upper()

            # Parse amount
            amount = line[11 if is_actual else 6].strip()
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
            full_ec_code = line[2].split('.')[0].rjust(5, '0')

            # Concepts are the firts three digits from the economic codes
            ec_code = full_ec_code[:3]

            # Item numbers are the last two digits from the economic codes (digits four and five)
            item_number = full_ec_code[-2:]

            # Description
            description = line[3].strip()

            # Parse amount
            amount = line[9 if is_actual else 4].strip()
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
