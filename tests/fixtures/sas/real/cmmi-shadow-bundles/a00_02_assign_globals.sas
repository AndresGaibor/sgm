/*************************************************************************;
%** PROGRAM: a00_02_assign_globals.sas
%** PURPOSE: To define global variables to be accessed by other macros
%** AUTHOR: Acumen, LLC
%** DATE CREATED: 01/17/2025
%** DATE LAST MODIFIED: 02/25/2025
************************************************************************;
This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the CC0 1.0 Universal public domain dedication as indicated in LICENSE.

************************************************************************/
%macro a00_02_assign_globals();

   %global drg_yr apc_yr lhs_var baseline_st_dt baseline_end_dt cl_data_start_row spinal_fusion_fy dgn_start_row
           ip_tha_anchor_trigger op_tha_anchor_trigger ip_tsa_anchor_trigger op_tsa_anchor_trigger stage_0_cont_covs dependent_var
           op_tha_start_dt op_tha_end_dt op_tsa_start_dt op_tsa_end_dt diag_proc_length low_count_threshold updt_factors_ver
           ach_epi_thrsh MJRLE_id MJRLE_type MJRUE_id MJRUE_type episodes_path code_path logic_path log_path
           out_path model_end_date
           ipps_oper_base_full_2020 ipps_oper_base_full_2021 ipps_oper_base_full_2022 ipps_oper_base_full_2023 ipps_oper_base_full_2024
           model_ip model_op model_ms model_stage1_1_5
           bas_strt_yr bas_end_yr bas_strt_qtr bas_end_qtr
         ;

   %*indicate what year DRG will be used - should be updated with FY updates;
   %*Update based on the model year of interest;
   %let drg_yr = 2024;
   %*indicate what year APC will be used - should be updated with CY updates;
   %*Update based on the model year of interest;
   %let apc_yr = 2024;

   %*define IPPS operating base full rates;
   %let ipps_oper_base_full_2020 = 5796.63;
   %let ipps_oper_base_full_2021 = 5961.31;
   %let ipps_oper_base_full_2022 = 6121.65;
   %let ipps_oper_base_full_2023 = 6375.74;
   %let ipps_oper_base_full_2024 = 6497.77;

   %*clinical logic start row;
   %let cl_data_start_row = 8;
   %*tha covariates dgn codes start row;
   %let dgn_start_row = 8;


   /********** static globals below - do not change **********/

   %*dependent variable;
   %let dependent_var = epi_std_pmt_fctr_win_1_99;

   %*baseline period start date - updated;
   %*Update based on the model year of interest;
   %let baseline_st_dt = 01OCT2019;
   %let bas_strt_yr = 2019;
   %let bas_strt_qtr = 4;
   %*baseline period end date - updated;
   %*Update based on the model year of interest;
   %let baseline_end_dt = 30SEP2023;
   %let bas_end_yr = 2023;
   %let bas_end_qtr = 3;

   %* fiscal year associated with spinal fusion coding update - do not change;
   %let spinal_fusion_fy = 2018;

   %*array length of diagnosis code or procedure codes in the episode files/claim files;
   %let diag_proc_length = 25;
   %let low_count_threshold = 20;

   %*MJRLE epi group id;
   %let MJRLE_id = P0020;
   %let MJRLE_type = MS;

   %*MJRLE epi group id;
   %let MJRUE_id = P0021;
   %let MJRUE_type = MS;

   %*define the trigger code of ip tha;
   %let ip_tha_anchor_trigger = 470;
   %*define the trigger code of op tha;
   %let op_tha_anchor_trigger = 27130;

   %*define the trigger code of ip tsa;
   %let ip_tsa_anchor_trigger = 483;
   %*define the trigger code of op tsa;
   %let op_tsa_anchor_trigger = 23472;

   %*define the continuous covariates in stage 0 logit regression;
   %let stage_0_cont_covs = AGE_50 AGE_50_SQ;

   %*define the start date of the baseline op tha episodes;
   %let op_tha_start_dt = 01JAN2020;
   %*define the end date of the baseline op tha episodes - updated;
   %let op_tha_end_dt = &baseline_end_dt.;

   %*define the start date of the baseline op tsa episodes;
   %let op_tsa_start_dt = 01JAN2021;
   %*define the end date of the baseline op tsa episodes - updated;
   %let op_tsa_end_dt = &baseline_end_dt.;

   %*the threshold of number of episode in baseline for each ach;
   %let ach_epi_thrsh = 40;

   /**************************************
     Parameters related to Model updates
   **************************************/


   %*model for ip episodes;
   %let model_ip = node2_xprop_zcons_qd;

   %*model for op episodes;
   %let model_op = node2_xprop_zcons_qd;

   %*model for op episodes;
   %let model_ms = node2_xprop_zcons_qd;

   %*model CE folder 33 and 22 due to non-convergence issue -- add step 1.5;
   %let model_stage1_1_5 = node2_xprop_zcons_qd_1_5;

   %*location of code path;
   %*change according to data path;
   %let code_path = c:\project\code;
   %*location to store logs;
   %*change according to data path;
   %let log_path = c:\project\log;
   %mkdirs(&log_path.);
   %*input data folder;
   %*change according to data path;
   %let episodes_path = c:\project\episode;
   %*location of clinic logic workbook;
   %*change according to data path;
   %let logic_path = c:\project\clinic_logic_workbook;
   %*output data folder;
      %*change according to data path;
   %let out_path = c:\project\output;

%mend;
