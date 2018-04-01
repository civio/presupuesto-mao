# -*- coding: UTF-8 -*-
from budget_app.loaders import SimpleBudgetLoader


class MaoBudgetCsvMapper:
    expenses_mapping = {
        '2018': {'ic_code': 0, 'fc_code': 1, 'full_ec_code': 3, 'description': 5, 'forecast_amount': 7, 'actual_amount': None},
        '2017': {'ic_code': 3, 'fc_code': 4, 'full_ec_code': 5, 'description': 6, 'forecast_amount': 7, 'actual_amount': 13},
        '2016': {'ic_code': 2, 'fc_code': 3, 'full_ec_code': 4, 'description': 5, 'forecast_amount': 6, 'actual_amount': 11},
        '2015': {'ic_code': 2, 'fc_code': 3, 'full_ec_code': 4, 'description': 5, 'forecast_amount': 6, 'actual_amount': 9},
        '2014': {'ic_code': 1, 'fc_code': 2, 'full_ec_code': 3, 'description': 4, 'forecast_amount': 5, 'actual_amount': 8},
        '2013': {'ic_code': 2, 'fc_code': 3, 'full_ec_code': 4, 'description': 5, 'forecast_amount': 6, 'actual_amount': 9},
        '2012': {'ic_code': 2, 'fc_code': 3, 'full_ec_code': 4, 'description': 5, 'forecast_amount': 6, 'actual_amount': 9},
    }

    income_mapping = {
        '2018': {'full_ec_code': 0, 'description': 2, 'forecast_amount': 4, 'actual_amount': None},
        '2017': {'full_ec_code': 2, 'description': 3, 'forecast_amount': 4, 'actual_amount': 9},
        '2016': {'full_ec_code': 2, 'description': 3, 'forecast_amount': 4, 'actual_amount': 7},
        '2015': {'full_ec_code': 2, 'description': 3, 'forecast_amount': 4, 'actual_amount': 8},
        '2014': {'full_ec_code': 2, 'description': 3, 'forecast_amount': 4, 'actual_amount': 8},
        '2013': {'full_ec_code': 2, 'description': 3, 'forecast_amount': 4, 'actual_amount': 8},
        '2012': {'full_ec_code': 2, 'description': 3, 'forecast_amount': 4, 'actual_amount': 7},
    }

    def __init__(self, year, is_expense):
        column_mapping = MaoBudgetCsvMapper.expenses_mapping

        if not is_expense:
            column_mapping = MaoBudgetCsvMapper.income_mapping

        mapping = column_mapping.get(year)

        self.ic_code = mapping.get('ic_code')
        self.fc_code = mapping.get('fc_code')
        self.full_ec_code = mapping.get('full_ec_code')
        self.description = mapping.get('description')
        self.forecast_amount = mapping.get('forecast_amount')
        self.actual_amount = mapping.get('actual_amount')


class MaoBudgetLoader(SimpleBudgetLoader):
    # Programme codes have changed in 2015, due to new laws. Since the application expects a code-programme
    # mapping to be constant over time, we are forced to amend budget data prior to 2015.
    # See https://github.com/dcabo/presupuestos-aragon/wiki/La-clasificaci%C3%B3n-funcional-en-las-Entidades-Locales
    programme_mapping = {
        # old programme: new programme
        '1550': '1624',     # Vies públiques
        '1620': '1621',     # R.S.U. i neteja viària
        '1690': '1651',     # Serveis comuns de ciutat i medi ambient -> Ciutat i medi ambient
        '1695': '1652',     # Brigada d'obres
        '1720': '1721',     # Medi ambient -> Medi ambient urbà
        '2304': '2310',     # Atenció primària -> Asistència social primaria
        '2305': '2311',     # Mediació social -> R.G.A.
        '3130': '3110',     # Sanitat
        '3131': '3110',     # Servei de Llacer -> Sanitat
        '3233': '3260',     # Escoles municipals
        '3323': '3322',     # Arxiu i patrimoni
        '3390': '3340',     # Serveis comuns del S.M.C. -> Promoció cultural
        '4301': '4310',     # Comerç
        '4302': '4312',     # Mercats
        '4304': '4320',     # Turisme
        '9200': '9250',     # Oficina d’atenció al ciutadà
        '9270': '9260',     # Comunicació
        '9324': '9340',     # Gestió tributària i financera
    }

    # make year data available in the class and call super
    def load(self, entity, year, path, status):
        self.year = year
        SimpleBudgetLoader.load(self, entity, year, path, status)

    # Parse an input line into fields
    def parse_item(self, filename, line):
        # Type of data
        is_expense = (filename.find('gastos.csv') != -1)
        is_actual = (filename.find('/ejecucion_') != -1)

        # Mapper
        mapper = MaoBudgetCsvMapper(self.year, is_expense)

        # Expenses
        if is_expense:
            # Institutional code
            # We only need the one digit to identify the service (the second one)
            ic_code = line[mapper.ic_code].strip()[1:2]
            ic_code = '0' + ic_code + 'X'

            # Functional code
            # We got decimal values as input, so we normalize them at 4- and add leading zeroes when required
            fc_code = line[mapper.fc_code].split('.')[0].rjust(4, '0')

            # For pre 2015 budgets we may need to amend the programme code
            if int(self.year) < 2015:
                fc_code = MaoBudgetLoader.programme_mapping.get(fc_code, fc_code)

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
