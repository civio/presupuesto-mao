# -*- coding: UTF-8 -*-
from budget_app.loaders import PaymentsLoader
from budget_app.models import Budget

import datetime


class MaoPaymentsCsvMapper:
    column_mapping = {
        '2017': {'fc_code': 12, 'date': 4, 'payee': 15, 'description': 16, 'amount': 8},
        '2016': {'fc_code': 9, 'date': 4, 'payee': 12, 'description': 13, 'amount': 5},
        '2015': {'fc_code': 12, 'date': 4, 'payee': 15, 'description': 16, 'amount': 8},
        '2014': {'fc_code': 12, 'date': 4, 'payee': 14, 'description': 15, 'amount': 8},
        '2013': {'fc_code': 12, 'date': 4, 'payee': 14, 'description': 15, 'amount': 8},
        '2012': {'fc_code': 11, 'date': 3, 'payee': 13, 'description': 14, 'amount': 7},
    }

    def __init__(self, year):
        column_mapping = MaoPaymentsCsvMapper.column_mapping
        mapping = column_mapping.get(year)

        self.fc_code = mapping.get('fc_code')
        self.date = mapping.get('date')
        self.payee = mapping.get('payee')
        self.description = mapping.get('description')
        self.amount = mapping.get('amount')


class MaoPaymentsLoader(PaymentsLoader):
    # make year data available in the class and call super
    def load(self, entity, year, path):
        self.year = year
        PaymentsLoader.load(self, entity, year, path)

    # Parse an input line into fields
    def parse_item(self, budget, line):
        # Mapper
        mapper = MaoPaymentsCsvMapper(self.year)

        # For the functional code we may get decimal values as input, so we
        # normalize them at 4- and add leading zeroes when required
        fc_code = line[mapper.fc_code].split('.')[0].rjust(4, '0')

        # We ignore rows with incomplete data
        if fc_code == '0000':
            return

        # first two digits of the functional code make the policy id
        policy_id = fc_code[:2]

        # but what we want as area is the policy description
        policy = Budget.objects.get_all_descriptions(budget.entity)['functional'][policy_id]

        # We have got dates as numeric values, per XLS convention: integer part
        # stores the number of days since the epoch (Jan 1st 1900 in our case)
        # and the fractional part stores the percentage of the day
        date = line[mapper.date].strip()

        # serial number that represents the number of elapsed days since January 1, 1900
        days = int(float(date))

        # actual date taking into account the Excel 1900 leap year bug
        date = datetime.datetime(1899, 12, 30) + datetime.timedelta(days, 0, 0, 0)
        date = date.strftime("%Y-%m-%d")

        # Payee data
        payee = line[mapper.payee].strip()

        # Some rows doesn't include payee data, so we asign an arbitrary value
        if not payee:
            payee = "ALTRES"

        # We haven't got any anonymized entries
        anonymized = False

        # Description
        description = line[mapper.description].strip()

        # Parse amount
        amount = line[mapper.amount].strip()
        amount = self._read_english_number(amount)

        return {
            'area': policy,
            'programme': None,
            'fc_code': None,  # We don't try (yet) to have foreign keys to existing records
            'ec_code': None,
            'date': date,
            'contract_type': None,
            'payee': payee,
            'anonymized': anonymized,
            'description': description,
            'amount': amount
        }