# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    cash_register_account_ids = fields.Many2many(
        "account.account",
        "company_cash_register_account_rel",
        "company_id",
        "account_id",
        string="Daily Cash Accounts",
        domain="[('account_type', 'in', ('asset_cash', 'asset_bank')), "
        "('company_ids', 'in', id)]",
        help="Chart of Accounts liquidity accounts included on the Daily Cash "
        "Register. Load from Accounting uses posted items on these accounts "
        "only, regardless of journal.",
    )
    cash_register_analytic_plan_id = fields.Many2one(
        "account.analytic.plan",
        string="Dept Analytic Plan",
        help="If set, only analytic accounts of this plan are used as Dept. "
        "Leave empty to use any analytic account on the cash line.",
    )
