Expected checks for the included data

- CRM: 10 source rows; 8 ACTIVE customers with monthly income at least 1800.
- Accounts: 12 source rows including one duplicate and one CLOSED row; 10 unique OPEN accounts remain.
- Settlements: 14 source rows including one duplicate; 10 unique rows remain after deduplication and the SETTLED/amount filters.
- Digital events: 14 source rows; 12 have consent=Y.
- Customer 360 snapshot: 8 active customers. LEFT joins keep customers with no qualifying payments or consented events, with their metrics set to zero.
- The orchestrator includes all 7 processing programs in the README order.

These are manual reference counts. The portal analyzes SAS source files but does not run SAS or validate these counts automatically.
