Synthetic SAS project: Customer 360 multi-source

All project data are fictitious. No credentials, database connections, or real personal data are included. Four local source files represent CRM, core banking, card settlements, and digital events.

This ZIP contains 8 SAS programs: 7 processing Jobs and 1 orchestrator. Job filenames use the s360 prefix to distinguish them from previous test Jobs. The orchestrator uses fixed, static includes in dependency order; there are no dynamic program names.

Sources:
- Data/CRM/customer_master.csv: comma-delimited CRM export.
- Data/Core/accounts.tsv: tab-delimited core accounts.
- Data/Payments/card_settlements.psv: pipe-delimited card settlement feed.
- Data/Digital/digital_events.csv: semicolon-delimited digital activity.

Flow:
1. s360_load_crm_customers filters active CRM customers.
2. s360_load_core_accounts filters open accounts and deduplicates account IDs.
3. s360_load_card_settlements deduplicates payment IDs and keeps settled payments above the threshold.
4. s360_load_digital_events keeps events with consent.
5. s360_summarize_settlements joins accounts to payments and aggregates by customer.
6. s360_summarize_digital_events aggregates events by customer.
7. s360_build_customer360 joins the summaries, calculates an activity score, and writes a snapshot.
8. s360_run_customer360_multisource includes the seven programs above.

All paths are relative to the extracted project root. Run the orchestrator from that root if executing the SAS sample. The demo parameters have non-empty sample values. Upload this ZIP as a new project, then review its inventory, dependencies, and migration plan before applying anything in Talend. Applying creates or updates Jobs; it does not execute them.

The sample exercises file reads, filters, sort/deduplication, an INNER join, LEFT joins, aggregations, and orchestration. See expected/expected-results.md for manual row-count checks. Talend component compilation still needs to be reviewed in Studio.
