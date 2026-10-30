/* priority: P0 */
%include '/example/macros/common_filters.sas';
%apply_active_filter(input=work.accounts,output=work.active_accounts)
