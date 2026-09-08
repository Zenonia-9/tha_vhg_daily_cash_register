# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cash_register_journal_ids = fields.Many2many(
        related="company_id.cash_register_journal_ids",
        readonly=False,
    )
    cash_register_analytic_plan_id = fields.Many2one(
        related="company_id.cash_register_analytic_plan_id",
        readonly=False,
    )
