/* priority: P0 | Static parent Job with explicit sequence */
%let batch_period = 202610;

%include "Programs/CRM/s360_load_crm_customers.sas";
%include "Programs/Core/s360_load_core_accounts.sas";
%include "Programs/Payments/s360_load_card_settlements.sas";
%include "Programs/Digital/s360_load_digital_events.sas";
%include "Programs/Analytics/s360_summarize_settlements.sas";
%include "Programs/Analytics/s360_summarize_digital_events.sas";
%include "Programs/Output/s360_build_customer360.sas";
