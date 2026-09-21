# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)


def _table_exists(cr, name):
    cr.execute("SELECT to_regclass(%s)", (f"public.{name}",))
    return bool(cr.fetchone()[0])


def _snapshot_journal_rels(cr):
    """Keep journal→account mappings before Odoo drops the old M2M tables."""
    if _table_exists(cr, "company_cash_register_journal_rel"):
        cr.execute("DROP TABLE IF EXISTS _dcr_mig_company_accounts")
        cr.execute(
            """
            CREATE TABLE _dcr_mig_company_accounts AS
            SELECT rel.company_id, journal.default_account_id AS account_id
              FROM company_cash_register_journal_rel rel
              JOIN account_journal journal ON journal.id = rel.journal_id
             WHERE journal.default_account_id IS NOT NULL
            """
        )
        _logger.info("DCR: snapshotted company journal defaults for account migration")
    if _table_exists(cr, "vhg_dcr_journal_rel"):
        cr.execute("DROP TABLE IF EXISTS _dcr_mig_register_accounts")
        cr.execute(
            """
            CREATE TABLE _dcr_mig_register_accounts AS
            SELECT rel.register_id, journal.default_account_id AS account_id
              FROM vhg_dcr_journal_rel rel
              JOIN account_journal journal ON journal.id = rel.journal_id
             WHERE journal.default_account_id IS NOT NULL
            """
        )
        _logger.info("DCR: snapshotted register journal defaults for account migration")


def _apply_account_rels(cr):
    if _table_exists(cr, "_dcr_mig_company_accounts") and _table_exists(
        cr, "company_cash_register_account_rel"
    ):
        cr.execute(
            """
            INSERT INTO company_cash_register_account_rel (company_id, account_id)
            SELECT DISTINCT company_id, account_id
              FROM _dcr_mig_company_accounts
             WHERE account_id IS NOT NULL
            ON CONFLICT DO NOTHING
            """
        )
        _logger.info("DCR: migrated %s company cash-register account(s)", cr.rowcount)
        cr.execute("DROP TABLE IF EXISTS _dcr_mig_company_accounts")
    if _table_exists(cr, "_dcr_mig_register_accounts") and _table_exists(
        cr, "vhg_dcr_account_rel"
    ):
        cr.execute(
            """
            INSERT INTO vhg_dcr_account_rel (register_id, account_id)
            SELECT DISTINCT register_id, account_id
              FROM _dcr_mig_register_accounts
             WHERE account_id IS NOT NULL
            ON CONFLICT DO NOTHING
            """
        )
        _logger.info("DCR: migrated %s register cash-register account(s)", cr.rowcount)
        cr.execute("DROP TABLE IF EXISTS _dcr_mig_register_accounts")


def pre_init_hook(env):
    _snapshot_journal_rels(env.cr)


def post_init_hook(env):
    """Copy journal default accounts onto the new Chart of Accounts fields."""
    _apply_account_rels(env.cr)
