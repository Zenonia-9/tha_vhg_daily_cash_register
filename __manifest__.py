# -*- coding: utf-8 -*-
{
    "name": "VHG Daily Cash Register",
    "summary": "Daily cash register from cash journals with denomination count and QWeb print.",
    "version": "19.0.1.0.0",
    "category": "Accounting/Accounting",
    "author": "Thein Htoo Aung",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "report/daily_cash_register_report.xml",
        "report/daily_cash_register_templates.xml",
        "views/daily_cash_register_views.xml",
        "views/account_move_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
}
