# VHG Daily Cash Register

## Overview
Provides a daily cash register for tracking cash balances from selected Chart of Accounts liquidity accounts (cash and bank). Supports physical denomination counting for Myanmar Kyat (MMK) notes and tracks foreign currency amounts (SGD, THB, USD). Includes QWeb report printing for end-of-day reconciliation.

## Features
- Create daily cash registers linked to one or more cash/bank accounts from the Chart of Accounts
- Record physical note counts by Kyat denomination (10,000 / 5,000 / 1,000 / 500 / 200 / 100 / 50 / 20 / 10 / 5 / 1 and small notes)
- Track foreign currency totals for SGD, THB, and USD
- Separate receipt and payment line types
- Draft / Confirmed workflow with state tracking
- Auto-generated sequence numbers per register
- QWeb PDF report for printing the daily cash register (Victoria colours)
- Coloured Excel print matching the paper register (yellow header, blue opening/closing, orange section totals)
- Extends account move lines, accounts, and journal configuration for cash register integration
- Configurable settings via `res.config.settings`
- Chatter integration (mail thread and activities)

## Requirements
- Odoo 19
- Depends on: `account`

## Installation
Install the module from Apps or update via command line:
```bash
docker exec odoo_19 odoo -d THA -u tha_vhg_daily_cash_register --stop-after-init
```

## Configuration
- Select cash/bank accounts under Accounting > Configuration > Settings > Daily Cash Register
- Optional column override remains on the journal: Accounting > Configuration > Journals > Cash Register Column

## Usage
1. Navigate to the Daily Cash Register menu
2. Create a new register, select the date and cash accounts
3. Enter denomination counts and foreign currency amounts
4. Confirm the register when complete
5. Print PDF or Print Excel for physical reconciliation. Excel uses the same columns and Victoria colours as the paper register.

## Technical Details
### Models
- `vhg.daily.cash.register` — main register document (inherits `mail.thread`, `mail.activity.mixin`)
- `vhg.daily.cash.register.line` — individual receipt/payment lines
- Extends `account.move.line`, `account.journal`, `res.company`, and `res.config.settings`

### Denomination Structure
Kyat denominations are defined as constants in the model file, from 10,000 down to 1, plus a "small note" row for loose change. USD is tracked numerically without physical note-count columns.

### Reports
- QWeb report action and template in `report/` directory
- Excel workbook from `action_print_excel` (`models/daily_cash_register_xlsx.py`), built with xlsxwriter (Odoo core dependency). No extra module required.

### Accounting currency handling
Load from Accounting filters posted `account.move.line` records by the selected
cash/bank accounts (`account_ids`), not by journal. Column routing priority:
journal Cash Register Column, then the move line transaction currency, then
account/journal/company currency. Foreign-currency lines use `amount_currency`;
company-currency lines use the company balance. Unsupported currencies retain
the Kyats fallback.

On upgrade from 19.0.1.3.0, selected journals are mapped to their default
accounts so existing Settings and draft registers keep a working CoA selection.

### Data
- IR sequence for auto-numbering registers (`data/ir_sequence.xml`)

## Security
- Multi-company record rule: users can only access registers belonging to their allowed companies
- Access rights defined in `security/ir.model.access.csv`
- Custom security groups defined in `security/security.xml`

## Author
Thein Htoo Aung

## License
LGPL-3