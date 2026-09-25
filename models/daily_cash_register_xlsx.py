# -*- coding: utf-8 -*-

import base64
import io
from datetime import date

from odoo import models

try:
    import xlsxwriter
except ImportError:  # pragma: no cover - Odoo ships xlsxwriter
    xlsxwriter = None


# Victoria layout colours from the paper register.
COLOR_HEADER = "#FFFF00"
COLOR_BALANCE = "#9BC2E6"
COLOR_TOTAL = "#F4B183"
COLOR_DENOM_HL = "#CFCFCF"
COLOR_DENOM_TOTAL = "#D9D9D9"


def _fmt_date(value):
    if not value:
        return ""
    if isinstance(value, date):
        return value.strftime("%-d-%b-%y")
    return str(value)


class VhgDailyCashRegisterXlsx(models.Model):
    _inherit = "vhg.daily.cash.register"

    def action_print_excel(self):
        """Download the coloured Daily Cash Register workbook."""
        self.check_access("read")
        content = self._generate_xlsx()
        if len(self) == 1:
            filename = "Daily Cash Register - %s.xlsx" % _fmt_date(self.date)
        else:
            filename = "Daily Cash Register.xlsx"
        attachment_vals = {
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(content),
            "res_model": self._name,
            "res_id": self[:1].id,
            "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self[:1].id),
                ("name", "=", filename),
            ],
            limit=1,
        )
        if attachment:
            attachment.write(attachment_vals)
        else:
            attachment = self.env["ir.attachment"].create(attachment_vals)
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % attachment.id,
            "target": "self",
        }

    def _generate_xlsx(self):
        if xlsxwriter is None:
            raise ImportError("xlsxwriter is required to print the Daily Cash Register Excel file.")
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True, "strings_to_numbers": False})
        formats = self._xlsx_formats(workbook)
        records = self or self.browse()
        if not records:
            sheet = workbook.add_worksheet("Daily Cash Register")
            sheet.write(0, 0, "No register selected", formats["title"])
        elif len(records) == 1:
            records._xlsx_write_sheet(workbook, formats, "Daily Cash Register")
        else:
            used = set()
            for rec in records:
                raw = _fmt_date(rec.date) or rec.name or "DCR"
                name = raw[:31]
                suffix = 2
                while name.lower() in used:
                    tail = "-%s" % suffix
                    name = ("%s%s" % (raw[: 31 - len(tail)], tail))[:31]
                    suffix += 1
                used.add(name.lower())
                rec._xlsx_write_sheet(workbook, formats, name)
        workbook.close()
        return output.getvalue()

    def _xlsx_formats(self, workbook):
        base = {
            "font_name": "Arial",
            "font_size": 10,
            "border": 1,
            "border_color": "#000000",
            "valign": "vcenter",
        }
        num = dict(base, num_format="#,##0", align="right")
        return {
            "title": workbook.add_format(
                {"font_name": "Arial", "font_size": 13, "bold": True, "align": "center"}
            ),
            "subtitle": workbook.add_format(
                {"font_name": "Arial", "font_size": 13, "bold": True, "align": "center"}
            ),
            "date": workbook.add_format(
                {"font_name": "Arial", "font_size": 12, "bold": True, "align": "right"}
            ),
            "header": workbook.add_format(
                dict(base, bold=True, align="center", bg_color=COLOR_HEADER)
            ),
            "cell": workbook.add_format(dict(base, align="left", text_wrap=True)),
            "cell_center": workbook.add_format(dict(base, align="center", text_wrap=True)),
            "num": workbook.add_format(num),
            "opening": workbook.add_format(
                dict(base, bold=True, align="center", bg_color=COLOR_BALANCE)
            ),
            "opening_num": workbook.add_format(dict(num, bold=True, bg_color=COLOR_BALANCE)),
            "total": workbook.add_format(
                dict(base, bold=True, align="center", bg_color=COLOR_TOTAL)
            ),
            "total_num": workbook.add_format(dict(num, bold=True, bg_color=COLOR_TOTAL)),
            "closing": workbook.add_format(
                dict(base, bold=True, align="center", bg_color=COLOR_BALANCE)
            ),
            "closing_num": workbook.add_format(dict(num, bold=True, bg_color=COLOR_BALANCE)),
            "denom_title": workbook.add_format(
                {"font_name": "Arial", "font_size": 12, "bold": True, "underline": True}
            ),
            "denom_header": workbook.add_format(
                {"font_name": "Arial", "font_size": 10, "bold": True, "align": "right"}
            ),
            "denom_label": workbook.add_format(
                {"font_name": "Arial", "font_size": 10, "align": "right"}
            ),
            "denom_num": workbook.add_format(
                {"font_name": "Arial", "font_size": 10, "align": "right", "num_format": "#,##0"}
            ),
            "denom_hl": workbook.add_format(
                {
                    "font_name": "Arial",
                    "font_size": 10,
                    "align": "right",
                    "num_format": "#,##0",
                    "bg_color": COLOR_DENOM_HL,
                }
            ),
            "denom_total_label": workbook.add_format(
                {
                    "font_name": "Arial",
                    "font_size": 10,
                    "bold": True,
                    "bg_color": COLOR_DENOM_TOTAL,
                }
            ),
            "denom_total_num": workbook.add_format(
                {
                    "font_name": "Arial",
                    "font_size": 10,
                    "bold": True,
                    "align": "right",
                    "num_format": "#,##0",
                    "bg_color": COLOR_DENOM_TOTAL,
                }
            ),
            "sign": workbook.add_format(
                {"font_name": "Arial", "font_size": 11, "bold": True, "valign": "top"}
            ),
        }

    def _xlsx_write_sheet(self, workbook, formats, sheet_name):
        self.ensure_one()
        sheet = workbook.add_worksheet(sheet_name)
        sheet.set_landscape()
        sheet.set_paper(9)  # A4
        sheet.set_margins(0.3, 0.3, 0.3, 0.4)
        sheet.fit_to_pages(1, 0)
        sheet.set_column("A:A", 6)
        sheet.set_column("B:B", 22)
        sheet.set_column("C:C", 72)
        sheet.set_column("D:D", 16)
        sheet.set_column("E:G", 11)
        sheet.set_row(0, 18)
        sheet.set_row(1, 18)

        sheet.merge_range("A1:G1", self.company_id.name or "", formats["title"])
        sheet.merge_range("A2:F2", "Daily Cash Register", formats["subtitle"])
        sheet.write("G2", _fmt_date(self.date), formats["date"])

        headers = ["No", "Dept:", "Particulars", "Kyats", "SGD", "Baht", "USD"]
        for col, label in enumerate(headers):
            sheet.write(2, col, label, formats["header"])
        sheet.set_row(2, 18)

        row = 3
        row = self._xlsx_write_balance_row(
            sheet,
            formats,
            row,
            "Opening Cash balance",
            self.opening_kyats,
            self.opening_sgd,
            self.opening_baht,
            self.opening_usd,
            label_fmt=formats["opening"],
            num_fmt=formats["opening_num"],
            show_zero=True,
        )
        receipts = self.receipt_line_ids or self.line_ids.filtered(
            lambda line: line.line_type == "receipt"
        )
        payments = self.payment_line_ids or self.line_ids.filtered(
            lambda line: line.line_type == "payment"
        )
        row = self._xlsx_write_lines(sheet, formats, row, receipts)
        row = self._xlsx_write_balance_row(
            sheet,
            formats,
            row,
            "Total Cash Receipt",
            self.receipt_kyats,
            self.receipt_sgd,
            self.receipt_baht,
            self.receipt_usd,
            label_fmt=formats["total"],
            num_fmt=formats["total_num"],
            show_zero=False,
        )
        row = self._xlsx_write_lines(sheet, formats, row, payments)
        row = self._xlsx_write_balance_row(
            sheet,
            formats,
            row,
            "Total Cash Payment",
            self.payment_kyats,
            self.payment_sgd,
            self.payment_baht,
            self.payment_usd,
            label_fmt=formats["total"],
            num_fmt=formats["total_num"],
            show_zero=False,
        )
        row = self._xlsx_write_balance_row(
            sheet,
            formats,
            row,
            "Closing Cash balance",
            self.closing_kyats,
            self.closing_sgd,
            self.closing_baht,
            self.closing_usd,
            label_fmt=formats["closing"],
            num_fmt=formats["closing_num"],
            show_zero=True,
        )

        row += 2
        sheet.write(row, 0, "No", formats["denom_title"])
        sheet.write(row, 1, "Cash Denomination", formats["denom_title"])
        row += 1
        denom_headers = ["No", "Type", "Amount", "Qty", "Qty", "Qty", "Qty"]
        for col, label in enumerate(denom_headers):
            sheet.write(row, col, label, formats["denom_header"])
        row += 1
        for dline in self.denom_line_ids:
            amount_fmt = formats["denom_hl"] if dline.code == "small" else formats["denom_num"]
            sheet.write(row, 0, dline.sequence or "", formats["denom_label"])
            sheet.write(row, 1, dline.name or "", formats["denom_label"])
            if dline.amount:
                sheet.write_number(row, 2, dline.amount, amount_fmt)
            else:
                sheet.write(row, 2, "", amount_fmt)
            sheet.write(row, 3, dline.qty_mmk or "", formats["denom_label"])
            sheet.write(row, 4, dline.qty_sgd or "", formats["denom_label"])
            sheet.write(row, 5, dline.qty_baht or "", formats["denom_label"])
            sheet.write(row, 6, dline.qty_usd or "", formats["denom_label"])
            row += 1
        sheet.write(row, 0, "Sum Total", formats["denom_total_label"])
        sheet.write(row, 1, "", formats["denom_total_label"])
        sheet.write_number(row, 2, self.denom_total_kyats or 0.0, formats["denom_total_num"])
        sheet.write(row, 3, self.denom_qty_mmk or "", formats["denom_total_num"])
        sheet.write(row, 4, self.denom_qty_sgd or "", formats["denom_total_num"])
        sheet.write(row, 5, self.denom_qty_baht or "-", formats["denom_total_num"])
        sheet.write(row, 6, self.denom_qty_usd or "", formats["denom_total_num"])
        row += 2
        sheet.write(row, 0, "Checked", formats["sign"])
        row += 2
        sheet.set_row(row, 48)
        sheet.write(row, 0, "Confirmed by;\n\nOther Department", formats["sign"])
        sheet.write(row, 2, "Checked By;\n\nDCA/ACA", formats["sign"])
        sheet.write(row, 4, "Prepared by:\n\nChief Cashier/Asst; Chief Cashier", formats["sign"])
        sheet.print_area(0, 0, row, 6)
        return row

    def _xlsx_write_balance_row(
        self,
        sheet,
        formats,
        row,
        label,
        kyats,
        sgd,
        baht,
        usd,
        label_fmt,
        num_fmt,
        show_zero,
    ):
        sheet.write(row, 0, "", label_fmt)
        sheet.write(row, 1, "", label_fmt)
        sheet.write(row, 2, label, label_fmt)
        self._xlsx_write_amount(sheet, row, 3, kyats, num_fmt, show_zero=True)
        self._xlsx_write_amount(sheet, row, 4, sgd, num_fmt, show_zero=show_zero)
        self._xlsx_write_amount(sheet, row, 5, baht, num_fmt, show_zero=show_zero)
        self._xlsx_write_amount(sheet, row, 6, usd, num_fmt, show_zero=show_zero)
        sheet.set_row(row, 18)
        return row + 1

    def _xlsx_write_lines(self, sheet, formats, row, lines):
        for line in lines:
            particulars = line.particulars or ""
            extra = max(0, particulars.count("\n"))
            height = 16 + extra * 12
            if len(particulars) > 80:
                height = max(height, 28)
            sheet.set_row(row, height)
            sheet.write(row, 0, line.sequence or "", formats["cell_center"])
            sheet.write(row, 1, line.dept or "", formats["cell_center"])
            sheet.write(row, 2, particulars, formats["cell"])
            self._xlsx_write_amount(sheet, row, 3, line.amount_kyats, formats["num"], show_zero=False)
            self._xlsx_write_amount(sheet, row, 4, line.amount_sgd, formats["num"], show_zero=False)
            self._xlsx_write_amount(sheet, row, 5, line.amount_baht, formats["num"], show_zero=False)
            self._xlsx_write_amount(sheet, row, 6, line.amount_usd, formats["num"], show_zero=False)
            row += 1
        return row

    def _xlsx_write_amount(self, sheet, row, col, value, fmt, show_zero=False):
        if value:
            sheet.write_number(row, col, value, fmt)
        elif show_zero:
            sheet.write_number(row, col, 0, fmt)
        else:
            sheet.write(row, col, "", fmt)
