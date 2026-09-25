# -*- coding: utf-8 -*-

from datetime import date
from io import BytesIO

from odoo.tests.common import TransactionCase

from odoo.addons.tha_vhg_daily_cash_register.models.daily_cash_register_xlsx import (
    COLOR_BALANCE,
    COLOR_HEADER,
    COLOR_TOTAL,
)


def _fill_rgb(cell):
    fill = cell.fill
    color = getattr(fill.fgColor, "rgb", None) or getattr(fill.start_color, "rgb", None)
    if not color:
        return ""
    return str(color).upper()[-6:]


class TestDailyCashRegisterExcel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.register = cls.env["vhg.daily.cash.register"].new(
            {
                "name": "DCR/TEST",
                "date": date(2026, 4, 4),
                "company_id": cls.company.id,
                "opening_kyats": 1029986000.0,
                "opening_sgd": 0.0,
                "opening_baht": 0.0,
                "opening_usd": 0.0,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "line_type": "receipt",
                            "sequence": 1,
                            "dept": "Finance & Account-CC",
                            "particulars": "Cash receive from front office 3 April 26 and 4 April 26 morning",
                            "amount_kyats": 128037698.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "line_type": "payment",
                            "sequence": 1,
                            "dept": "",
                            "particulars": "Commission Fee for Feb 2026 (Opal)",
                            "amount_kyats": 1516850.0,
                        },
                    ),
                ],
            }
        )

    def test_xlsx_layout_and_victoria_colours(self):
        content = self.register._generate_xlsx()
        self.assertTrue(content[:2] == b"PK")

        from openpyxl import load_workbook

        book = load_workbook(BytesIO(content))
        sheet = book["Daily Cash Register"]
        self.assertEqual(sheet["C2"].value, "Daily Cash Register")
        self.assertEqual(sheet["A3"].value, "No")
        self.assertEqual(sheet["C4"].value, "Opening Cash balance")
        self.assertEqual(sheet["D4"].value, 1029986000)
        self.assertEqual(sheet["C5"].value, "Cash receive from front office 3 April 26 and 4 April 26 morning")
        self.assertEqual(sheet["D5"].value, 128037698)
        self.assertEqual(sheet["C6"].value, "Total Cash Receipt")
        self.assertEqual(sheet["C7"].value, "Commission Fee for Feb 2026 (Opal)")
        self.assertEqual(sheet["C8"].value, "Total Cash Payment")
        self.assertEqual(sheet["C9"].value, "Closing Cash balance")

        self.assertEqual(_fill_rgb(sheet["A3"]), COLOR_HEADER.lstrip("#").upper())
        self.assertEqual(_fill_rgb(sheet["C4"]), COLOR_BALANCE.lstrip("#").upper())
        self.assertEqual(_fill_rgb(sheet["C6"]), COLOR_TOTAL.lstrip("#").upper())
        self.assertEqual(_fill_rgb(sheet["C8"]), COLOR_TOTAL.lstrip("#").upper())
        self.assertEqual(_fill_rgb(sheet["C9"]), COLOR_BALANCE.lstrip("#").upper())
