# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    cash_register_journal_ids = fields.Many2many(
        "account.journal",
        "company_cash_register_journal_rel",
        "company_id",
        "journal_id",
        string="Daily Cash Journals",
        domain="[('company_id', '=', id), ('type', 'in', ('cash', 'bank'))]",
        help="Cash journals included on the Daily Cash Register. "
        "Use one journal per currency (Kyats, SGD, Baht, USD).",
    )
    cash_register_analytic_plan_id = fields.Many2one(
        "account.analytic.plan",
        string="Dept Analytic Plan",
        help="If set, only analytic accounts of this plan are used as Dept. "
        "Leave empty to use any analytic account on the cash line.",
    )
