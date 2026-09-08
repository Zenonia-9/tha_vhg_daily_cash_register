# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

DENOM_ROWS = [
    ("small", "Small note", 0.0),
    ("10000", "10,000", 10000.0),
    ("5000", "5,000", 5000.0),
    ("1000", "1,000", 1000.0),
    ("500", "500", 500.0),
    ("200", "200", 200.0),
    ("100", "100", 100.0),
    ("50", "50", 50.0),
    ("20", "20", 20.0),
    ("10", "10", 10.0),
    ("5", "5", 5.0),
    ("1", "1", 1.0),
]

CURRENCY_CODE_SLOT = {
    "SGD": "sgd",
    "THB": "baht",
    "USD": "usd",
}


class VhgDailyCashRegister(models.Model):
    _name = "vhg.daily.cash.register"
    _description = "Daily Cash Register"
    _order = "date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default="New", copy=False, readonly=True)
    date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    journal_ids = fields.Many2many(
        "account.journal",
        "vhg_dcr_journal_rel",
        "register_id",
        "journal_id",
        string="Cash Journals",
        required=True,
        domain="[('company_id', '=', company_id), ('type', 'in', ('cash', 'bank'))]",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    line_ids = fields.One2many(
        "vhg.daily.cash.register.line",
        "register_id",
        string="Lines",
        copy=False,
    )
    receipt_line_ids = fields.One2many(
        "vhg.daily.cash.register.line",
        "register_id",
        domain=[("line_type", "=", "receipt")],
    )
    payment_line_ids = fields.One2many(
        "vhg.daily.cash.register.line",
        "register_id",
        domain=[("line_type", "=", "payment")],
    )
    denom_line_ids = fields.One2many(
        "vhg.daily.cash.register.denom",
        "register_id",
        string="Denominations",
        copy=False,
    )
    notes = fields.Text()

    opening_kyats = fields.Monetary(currency_field="currency_id")
    opening_sgd = fields.Float(string="Opening SGD", digits=(16, 2))
    opening_baht = fields.Float(string="Opening Baht", digits=(16, 2))
    opening_usd = fields.Float(string="Opening USD", digits=(16, 2))

    receipt_kyats = fields.Monetary(
        currency_field="currency_id", compute="_compute_section_totals", store=True
    )
    receipt_sgd = fields.Float(string="Receipt SGD", digits=(16, 2), compute="_compute_section_totals", store=True)
    receipt_baht = fields.Float(string="Receipt Baht", digits=(16, 2), compute="_compute_section_totals", store=True)
    receipt_usd = fields.Float(string="Receipt USD", digits=(16, 2), compute="_compute_section_totals", store=True)

    payment_kyats = fields.Monetary(
        currency_field="currency_id", compute="_compute_section_totals", store=True
    )
    payment_sgd = fields.Float(digits=(16, 2), compute="_compute_section_totals", store=True)
    payment_baht = fields.Float(digits=(16, 2), compute="_compute_section_totals", store=True)
    payment_usd = fields.Float(digits=(16, 2), compute="_compute_section_totals", store=True)

    closing_kyats = fields.Monetary(
        currency_field="currency_id", compute="_compute_closing", store=True
    )
    closing_sgd = fields.Float(digits=(16, 2), compute="_compute_closing", store=True)
    closing_baht = fields.Float(digits=(16, 2), compute="_compute_closing", store=True)
    closing_usd = fields.Float(digits=(16, 2), compute="_compute_closing", store=True)

    denom_total_kyats = fields.Monetary(
        currency_field="currency_id", compute="_compute_denom_totals", store=True
    )
    denom_qty_mmk = fields.Integer(compute="_compute_denom_totals", store=True)
    denom_qty_2 = fields.Integer(compute="_compute_denom_totals", store=True)
    denom_qty_3 = fields.Integer(compute="_compute_denom_totals", store=True)
    denom_mismatch = fields.Boolean(compute="_compute_denom_totals", store=True)

    _sql_constraints = [
        (
            "date_company_uniq",
            "unique(date, company_id)",
            "A cash register already exists for this company and date.",
        ),
    ]

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        company = self.env["res.company"].browse(res.get("company_id")) or self.env.company
        if "journal_ids" in fields_list and company.cash_register_journal_ids:
            res["journal_ids"] = [(6, 0, company.cash_register_journal_ids.ids)]
        return res

    @api.depends(
        "line_ids.line_type",
        "line_ids.amount_kyats",
        "line_ids.amount_sgd",
        "line_ids.amount_baht",
        "line_ids.amount_usd",
    )
    def _compute_section_totals(self):
        for rec in self:
            rec.receipt_kyats = rec.receipt_sgd = rec.receipt_baht = rec.receipt_usd = 0.0
            rec.payment_kyats = rec.payment_sgd = rec.payment_baht = rec.payment_usd = 0.0
            for line in rec.line_ids:
                if line.line_type == "receipt":
                    rec.receipt_kyats += line.amount_kyats
                    rec.receipt_sgd += line.amount_sgd
                    rec.receipt_baht += line.amount_baht
                    rec.receipt_usd += line.amount_usd
                elif line.line_type == "payment":
                    rec.payment_kyats += line.amount_kyats
                    rec.payment_sgd += line.amount_sgd
                    rec.payment_baht += line.amount_baht
                    rec.payment_usd += line.amount_usd

    @api.depends(
        "opening_kyats",
        "opening_sgd",
        "opening_baht",
        "opening_usd",
        "receipt_kyats",
        "receipt_sgd",
        "receipt_baht",
        "receipt_usd",
        "payment_kyats",
        "payment_sgd",
        "payment_baht",
        "payment_usd",
    )
    def _compute_closing(self):
        for rec in self:
            rec.closing_kyats = rec.opening_kyats + rec.receipt_kyats - rec.payment_kyats
            rec.closing_sgd = rec.opening_sgd + rec.receipt_sgd - rec.payment_sgd
            rec.closing_baht = rec.opening_baht + rec.receipt_baht - rec.payment_baht
            rec.closing_usd = rec.opening_usd + rec.receipt_usd - rec.payment_usd

    @api.depends(
        "denom_line_ids.amount",
        "denom_line_ids.qty_mmk",
        "denom_line_ids.qty_2",
        "denom_line_ids.qty_3",
        "closing_kyats",
    )
    def _compute_denom_totals(self):
        for rec in self:
            rec.denom_total_kyats = sum(rec.denom_line_ids.mapped("amount"))
            rec.denom_qty_mmk = sum(rec.denom_line_ids.mapped("qty_mmk"))
            rec.denom_qty_2 = sum(rec.denom_line_ids.mapped("qty_2"))
            rec.denom_qty_3 = sum(rec.denom_line_ids.mapped("qty_3"))
            rec.denom_mismatch = bool(
                rec.denom_line_ids
                and rec.currency_id.compare_amounts(rec.denom_total_kyats, rec.closing_kyats)
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.name == "New":
                rec.name = self.env["ir.sequence"].next_by_code("vhg.daily.cash.register") or rec.date.strftime(
                    "DCR/%Y/%m/%d"
                )
            if not rec.denom_line_ids:
                rec._prepare_denom_rows()
        return records

    def _prepare_denom_rows(self):
        self.ensure_one()
        self.denom_line_ids.unlink()
        self.write(
            {
                "denom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": index,
                            "code": code,
                            "name": label,
                            "face_value": face,
                        },
                    )
                    for index, (code, label, face) in enumerate(DENOM_ROWS, start=1)
                ]
            }
        )

    def _slot_for_journal(self, journal):
        if journal.cash_register_currency_slot:
            return journal.cash_register_currency_slot
        currency = journal.currency_id or journal.company_id.currency_id
        if currency == journal.company_id.currency_id:
            return "kyats"
        return CURRENCY_CODE_SLOT.get(currency.name, "kyats")

    def _cash_account_ids(self, journals):
        accounts = journals.mapped("default_account_id")
        extra = self.env["account.account"].search(
            [
                ("company_ids", "in", [self.company_id.id]),
                ("account_type", "=", "asset_cash"),
            ]
        )
        return accounts | extra

    def _dept_from_aml(self, aml):
        distribution = aml.analytic_distribution or {}
        if not distribution:
            return ""
        analytic_ids = []
        for key in distribution:
            raw = str(key).split(",")[0]
            if raw.isdigit():
                analytic_ids.append(int(raw))
        accounts = self.env["account.analytic.account"].browse(analytic_ids).exists()
        plan = self.company_id.cash_register_analytic_plan_id
        if plan:
            accounts = accounts.filtered(lambda acc: acc.plan_id == plan)
        return ", ".join(accounts.mapped("name"))

    def _particulars_from_aml(self, aml):
        if aml.cash_register_particulars:
            return aml.cash_register_particulars
        parts = [aml.move_id.ref, aml.name]
        return " - ".join(part for part in parts if part)

    def _line_vals_from_aml(self, aml, line_type, sequence):
        slot = self._slot_for_journal(aml.journal_id)
        amount = abs(aml.amount_currency) if aml.currency_id != self.currency_id else abs(aml.balance)
        if slot == "kyats":
            amount = abs(aml.balance)
        vals = {
            "line_type": line_type,
            "sequence": sequence,
            "dept": self._dept_from_aml(aml),
            "particulars": self._particulars_from_aml(aml),
            "move_line_id": aml.id,
            "analytic_account_names": self._dept_from_aml(aml),
            "amount_kyats": 0.0,
            "amount_sgd": 0.0,
            "amount_baht": 0.0,
            "amount_usd": 0.0,
        }
        vals[f"amount_{slot}"] = amount if slot != "kyats" else abs(aml.balance)
        if slot == "kyats":
            vals["amount_kyats"] = abs(aml.balance)
        return vals

    def action_load_accounting(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft registers can be reloaded."))
        if not self.journal_ids:
            raise UserError(_("Select the cash journals first."))

        Line = self.env["account.move.line"]
        cash_accounts = self._cash_account_ids(self.journal_ids)
        if not cash_accounts:
            raise UserError(_("No cash accounts found on the selected journals."))

        base_domain = [
            ("company_id", "=", self.company_id.id),
            ("parent_state", "=", "posted"),
            ("account_id", "in", cash_accounts.ids),
            ("journal_id", "in", self.journal_ids.ids),
        ]

        openings = {"kyats": 0.0, "sgd": 0.0, "baht": 0.0, "usd": 0.0}
        opening_lines = Line.search(base_domain + [("date", "<", self.date)])
        for aml in opening_lines:
            slot = self._slot_for_journal(aml.journal_id)
            if slot == "kyats":
                openings[slot] += aml.balance
            else:
                openings[slot] += aml.amount_currency

        today_lines = Line.search(
            base_domain + [("date", "=", self.date)],
            order="id",
        )
        receipt_vals = []
        payment_vals = []
        for aml in today_lines:
            if self.currency_id.is_zero(aml.balance) and self.currency_id.is_zero(aml.amount_currency):
                continue
            is_receipt = aml.balance > 0 or (
                self.currency_id.is_zero(aml.balance) and aml.amount_currency > 0
            )
            target = receipt_vals if is_receipt else payment_vals
            line_type = "receipt" if is_receipt else "payment"
            target.append(self._line_vals_from_aml(aml, line_type, len(target) + 1))

        self.line_ids.unlink()
        commands = [(0, 0, vals) for vals in receipt_vals + payment_vals]
        self.write(
            {
                "opening_kyats": openings["kyats"],
                "opening_sgd": openings["sgd"],
                "opening_baht": openings["baht"],
                "opening_usd": openings["usd"],
                "line_ids": commands,
            }
        )
        if not self.denom_line_ids:
            self._prepare_denom_rows()
        return True

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                continue
            rec.state = "confirmed"
        return True

    def action_draft(self):
        for rec in self:
            rec.state = "draft"
        return True

    def action_print(self):
        self.ensure_one()
        return self.env.ref(
            "tha_vhg_daily_cash_register.action_report_vhg_daily_cash_register"
        ).report_action(self)

    def action_reset_denominations(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft registers can be edited."))
        self._prepare_denom_rows()
        return True


class VhgDailyCashRegisterLine(models.Model):
    _name = "vhg.daily.cash.register.line"
    _description = "Daily Cash Register Line"
    _order = "line_type, sequence, id"

    register_id = fields.Many2one(
        "vhg.daily.cash.register",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(related="register_id.company_id", store=True)
    currency_id = fields.Many2one(related="register_id.currency_id")
    line_type = fields.Selection(
        [("receipt", "Receipt"), ("payment", "Payment")],
        required=True,
        index=True,
    )
    sequence = fields.Integer(default=1)
    dept = fields.Char(string="Dept")
    particulars = fields.Char(string="Particulars")
    amount_kyats = fields.Monetary(currency_field="currency_id")
    amount_sgd = fields.Float(string="Amount SGD", digits=(16, 2))
    amount_baht = fields.Float(string="Amount Baht", digits=(16, 2))
    amount_usd = fields.Float(string="Amount USD", digits=(16, 2))
    move_line_id = fields.Many2one("account.move.line", ondelete="set null")
    analytic_account_names = fields.Char(string="Analytic")


class VhgDailyCashRegisterDenom(models.Model):
    _name = "vhg.daily.cash.register.denom"
    _description = "Daily Cash Register Denomination"
    _order = "sequence, id"

    register_id = fields.Many2one(
        "vhg.daily.cash.register",
        required=True,
        ondelete="cascade",
        index=True,
    )
    currency_id = fields.Many2one(related="register_id.currency_id")
    sequence = fields.Integer(default=1)
    code = fields.Char(required=True)
    name = fields.Char(string="Type", required=True)
    face_value = fields.Float()
    amount = fields.Monetary(currency_field="currency_id")
    qty_mmk = fields.Integer(string="Qty")
    qty_2 = fields.Integer(string="Qty ")
    qty_3 = fields.Integer(string="Qty  ")

    @api.onchange("qty_mmk", "face_value")
    def _onchange_qty_amount(self):
        for line in self:
            if line.face_value:
                line.amount = line.face_value * line.qty_mmk

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            face = vals.get("face_value")
            qty = vals.get("qty_mmk")
            if face and qty and "amount" not in vals:
                vals["amount"] = face * qty
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if "qty_mmk" in vals or "face_value" in vals:
            for line in self:
                if line.face_value:
                    super(VhgDailyCashRegisterDenom, line).write(
                        {"amount": line.face_value * line.qty_mmk}
                    )
        return res
