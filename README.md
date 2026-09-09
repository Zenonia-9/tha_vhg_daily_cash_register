# VHG Daily Cash Register

## Overview
Provides a daily cash register for tracking cash balances from selected cash and bank journals. Supports physical denomination counting for Myanmar Kyat (MMK) notes and tracks foreign currency amounts (SGD, THB, USD). Includes QWeb report printing for end-of-day reconciliation.

## Features
- Create daily cash registers linked to one or more cash/bank journals
- Record physical note counts by Kyat denomination (10,000 / 5,000 / 1,000 / 500 / 200 / 100 / 50 / 20 / 10 / 5 / 1 and small notes)
- Track foreign currency totals for SGD, THB, and USD
- Separate receipt and payment line types
- Draft / Confirmed workflow with state tracking
- Auto-generated sequence numbers per register
- QWeb PDF report for printing the daily cash register
- Extends account move lines and journal configuration for cash register integration
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
- Configure cash/bank journals in Accounting > Configuration > Journals
- Cash register settings are available under Accounting > Configuration > Settings

## Usage
1. Navigate to the Daily Cash Register menu
2. Create a new register, select the date and cash journals
3. Enter denomination counts and foreign currency amounts
4. Confirm the register when complete
5. Print the QWeb report for physical reconciliation

## Technical Details
### Models
- `vhg.daily.cash.register` — main register document (inherits `mail.thread`, `mail.activity.mixin`)
- `vhg.daily.cash.register.line` — individual receipt/payment lines
- Extends `account.move.line`, `account.journal`, `res.company`, and `res.config.settings`

### Denomination Structure
Kyat denominations are defined as constants in the model file, from 10,000 down to 1, plus a "small note" row for loose change. USD is tracked numerically without physical note-count columns.

### Reports
- QWeb report action and template in `report/` directory

### Accounting currency handling
When loading posted accounting lines, the move line transaction currency takes
precedence over the journal/company currency for supported SGD, THB, and USD
slots. Foreign-currency lines use `amount_currency`; company-currency lines use
the company balance. Unsupported currencies retain the Kyats fallback.

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