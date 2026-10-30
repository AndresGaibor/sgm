/*************************************************************************
%**program: a00_00_risk_adjustment_calle.sas
%**purpose: To select and execute sub-callers/macros
%**author: Acumen, LLC
%**date created: 01/17/2025
%**last modified: 02/25/2025
*************************************************************************;
This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the CC0 1.0 Universal public domain dedication as indicated in LICENSE.

************************************************************************/

options obs=max ls=220 ps=max nocenter mprint noxwait validvarname=upcase mergenoby=warn compress=yes fullstimer extendobscounter=no minoperator;

%macro a00_00_risk_adjustment_caller(
                     /** All series parameters **/
                      code_dir            = ,
                      run_date            = 2025_02_12,
                      clinical_logic_date = 2024_06_14,
                      medical_code_list   = 2024_08_19,
                      fy_version          = 24,
                      cy_version          = 24,
                      obs                 = max,
                      import_switch        = 0,

                      ce_start_index  =  21,
                      ce_end_index    =  21,

                     /** a series switches   **/
                      run_a_series = ,
                        run_process_af = ,
                        run_ach_threshold = ,
                        run_mjrle_stage0 = ,

                     /** b series parameters **/

                     /** b series switches   **/
                     run_b_series         = ,
                        import_covariates    = ,

                     run_risk_adjustment  = ,
                        /** Execute one of below switch **/
                        run_tsp_model        = ,
                        run_GLM_model        = );

   options append=(sasautos=("&code_dir."
                     sasautos));

      *call frequently used/supporting macros;
      *Note: always run with other subsequent macros;
      %a00_01_utility_macros();

      %*assign macroglobals;
      *Note: always run with other subsequent macros;
      %a00_02_assign_globals();

      %*import from clinic logic workbook;
      %if &import_switch. %then %do;
         %a00_03_import_logic();
      %end;
      %*assign libs;
      *Note: always run with other subsequent macros;
      %a00_04_assign_libs();

   %if &run_a_series. = 1 %then %do;

      %*generate CE level final episode files;
      %if &run_process_af. = 1 %then %do;

         %*create new variables and check final episodes whether with dependent variable;
         %let create_vars = 1;
         %*output final episodes based on time period and CE groups;
         %let create_partitions = 1;

         %generate_log(log_filename=process_af);

         %a01_01_process_af();

      %end;

      %** Identify ACHs with episode count meeting threshold;
      %if &run_ach_threshold. = 1 %then %do;
         %generate_log(log_filename=ach_threshold);
         %a01_02_ach_threshold();
      %end;

      %** Run Stage 0 regression for THA episodes and assign pseudo OP episodes;
      %if &run_mjrle_stage0. = 1 %then %do;
         %*prepare tha episodes as model input;
         %a02_01_prep_episodes_for_logit();
         %*run logistics regression and calculate OP propensity scores;
         %a02_02_logit_regression();
         %*assign pseudo-OP episodes;
         %a02_03_flag_pseudo_op();

      %end;
   %end;

   %if &run_b_series. = 1 %then %do;

      %*assign macroglobals;
      %b00_01_assign_libs_globals();

      %if &import_covariates. = 1 %then %do;
         %b01_01_prep_risk_adj_covariates(ref_files = 1,
                                          tsp_files = 1);
      %end;

      %*assign covariate for each CE;
      %b01_02_assign_covariate();

      %generate_log(log_filename=ra_ce_&ce_start_index._start_ce._&ce_end_index._end_ce.);

      proc sql noprint;
         select episode_group_id, epi_type into : ce_id_list separated by " ", : ce_epi_type_list separated by " "
         from ref.ce_id_epi_type_all;
      quit;

      %macarray(ce_ids, &ce_id_list.);
      %macarray(epi_types, &ce_epi_type_list.);

      %do ce = &ce_start_index. %to &ce_end_index.;

         %let ce_id = &&ce_ids&ce..;
         %let ce_id_short = %sysfunc(inputn(%sysfunc(substr(&ce_id.,4,2)),8.));
         %let epi_type = &&epi_types&ce..;
         %let ce_id_w_type = ce&ce_id_short._&epi_type.;
         %let obs = max;
         %put &ce_id_w_type.;
            %** Calculate risk adjustment estimates;
            %if &run_risk_adjustment. = 1 %then %do;
               %b02_01_risk_adjustment(run_tsp = &run_tsp_model.,
                                       run_glm = &run_GLM_model.);
            %end;

           %** Use the coef estimates provided by Acumen without running any regression, estimates can be imported from workbook Acumen provided;
            %if &use_acumen_coef. %then %do;
               %*Note: This is only a sample code which may need updated upon format of workbook;
               proc import out= out&ce_id_short..&ce_id_w_type._estimates
                  datafile="&logic_path.\Acumen_calculated_estimates.xlsx"
                  dbms=xlsx replace;
                  sheet="&ce_id_w_type.";
                  DATAROW= 2;
                  getnames=yes;
               run;
            %end;
      %end;

   %end;

%mend;

%a00_00_risk_adjustment_caller(
                     /** All series parameters **/
                      run_date            = 2025_02_12,
                      clinical_logic_date = 2024_06_14,
                      medical_code_list   = 2024_08_19,
                      fy_version          = 24,
                      cy_version          = 24,
                      obs                 = max,
                      import_switch        = 0,

                      ce_start_index  =  21,
                      ce_end_index    =  21,

                     /** a series switches   **/
                      run_a_series        = 1,
                        run_process_af       = 0,
                        run_ach_threshold    = 1,
                        run_mjrle_stage0     = 0,

                     /** b series switches   **/
                     run_b_series         = 0,
                        import_covariates    = 0,

                     run_risk_adjustment  = 1,
                     /** To run risk adjustment, execute one of below switch **/
                           run_tsp_model        = 0,
                           run_GLM_model        = 1,
                     /** **/
                     use_acumen_coef      = 0


);
