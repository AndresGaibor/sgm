Synthetic data dictionary

All names, IDs, amounts, and dates are fictional.

Data/CRM/customer_master.csv (comma)
customer_id: integer; customer_name: text; segment: PREMIUM/RETAIL/SME; region: synthetic region; customer_status: ACTIVE/INACTIVE; monthly_income: decimal.

Data/Core/accounts.tsv (tab)
account_id: text; customer_id: integer; account_type: text; account_status: OPEN/CLOSED; balance and credit_limit: decimal.

Data/Payments/card_settlements.psv (pipe)
payment_id: text; account_id: text; payment_date: ISO date; amount: decimal; channel: text; settlement_status: SETTLED/DECLINED/REFUNDED. PM-8005 is intentionally duplicated.

Data/Digital/digital_events.csv (semicolon)
event_id: text; customer_id: integer; event_date: ISO date; event_type: text; consent: Y/N.

Demo parameters with values: minimum_monthly_income=1800, min_settlement_amount=20, required_consent=Y, snapshot_period=202610.

Program outputs are semicolon-delimited CSV files in Data/Stage and Output.
