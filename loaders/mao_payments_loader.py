# -*- coding: UTF-8 -*-
import datetime

from budget_app.loaders import PaymentsLoader
from budget_app.models import Budget


class MaoPaymentsLoader(PaymentsLoader):

    # Parse an input line into fields
    def parse_item(self, budget, line):
        # For the functional code We got decimal values as input, so we
        # normalize them at 4- and add leading zeroes when required
        fc_code = line[9].split('.')[0].rjust(4, '0')

        # first two digits of the functional code make the policy id
        policy_id = fc_code[:2]

        # but what we want as area is the policy description
        policy = Budget.objects.get_all_descriptions(budget.entity)['functional'][policy_id]

        # We have got dates as numeric values, per XLS convention: integer part
        # stores the number of days since the epoch (Jan 1st 1900 in our case)
        # and the fractional part stores the percentage of the day
        date = line[4].strip()

        # serial number that represents the number of elapsed days since January 1, 1900
        days = int(float(date))

        # actual date taking into account the Excel 1900 leap year bug
        date = datetime.datetime(1899, 12, 30) + datetime.timedelta(days, 0, 0, 0)
        date = date.strftime("%Y-%m-%d")

        # Payee data
        payee = line[12].strip()

        # We haven't got any anonymized entries
        anonymized = False

        # Description
        description = line[13].strip()

        # Parse amount
        amount = line[5].strip()
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