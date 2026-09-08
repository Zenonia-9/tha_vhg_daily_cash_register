# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    cash_register_currency_slot = fields.Selection(
        [
            ("kyats", "Kyats"),
            ("sgd", "SGD"),
            ("baht", "Baht"),
            ("usd", "USD"),
        ],
        string="Cash Register Column",
        help="Which printed column this journal fills. "
        "If empty, company currency → Kyats, SGD/THB/USD by currency code.",
    )
