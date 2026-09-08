# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cash_register_particulars = fields.Char(
        string="Cash Register Particulars",
        help="Text printed on the Daily Cash Register. "
        "If empty, the journal item label is used.",
        copy=False,
    )
