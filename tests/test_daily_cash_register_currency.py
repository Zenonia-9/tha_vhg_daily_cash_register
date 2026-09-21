from odoo.tests.common import TransactionCase


class TestDailyCashRegisterCurrency(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.register_model = cls.env["vhg.daily.cash.register"]
        cls.journal = cls.env["account.journal"].search(
            [
                ("company_id", "=", cls.company.id),
                ("type", "=", "cash"),
            ],
            limit=1,
        )
        cls.usd = cls.env["res.currency"].search([("name", "=", "USD")], limit=1)

    def test_foreign_transaction_currency_precedes_journal_currency(self):
        self.assertTrue(self.journal)
        self.assertTrue(self.usd)
        register = self.register_model.new({"company_id": self.company.id})
        aml = self.env["account.move.line"].new(
            {
                "journal_id": self.journal.id,
                "currency_id": self.usd.id,
                "amount_currency": 100.0,
                "balance": 420000.0,
            }
        )

        values = register._line_vals_from_aml(aml, "receipt", 1)

        self.assertEqual(values["amount_kyats"], 0.0)
        self.assertEqual(values["amount_usd"], 100.0)

    def test_company_currency_transaction_uses_company_balance(self):
        self.assertTrue(self.journal)
        register = self.register_model.new({"company_id": self.company.id})
        aml = self.env["account.move.line"].new(
            {
                "journal_id": self.journal.id,
                "currency_id": self.company.currency_id.id,
                "amount_currency": 100.0,
                "balance": 420000.0,
            }
        )

        values = register._line_vals_from_aml(aml, "payment", 1)

        self.assertEqual(values["amount_kyats"], 420000.0)
        self.assertEqual(values["amount_usd"], 0.0)

    def test_account_column_override_precedes_transaction_currency(self):
        self.assertTrue(self.journal)
        self.assertTrue(self.usd)
        account = self.env["account.account"].new(
            {"cash_register_currency_slot": "kyats"}
        )
        register = self.register_model.new({"company_id": self.company.id})
        aml = self.env["account.move.line"].new(
            {
                "journal_id": self.journal.id,
                "currency_id": self.usd.id,
                "amount_currency": 100.0,
                "balance": 420000.0,
            }
        )
        aml.account_id = account

        values = register._line_vals_from_aml(aml, "receipt", 1)

        self.assertEqual(values["amount_kyats"], 420000.0)
        self.assertEqual(values["amount_usd"], 0.0)
