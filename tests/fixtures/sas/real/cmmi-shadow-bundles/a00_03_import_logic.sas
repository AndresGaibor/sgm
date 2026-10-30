/*************************************************************************;
%** PROGRAM: a00_03_import_logic.sas
%** PURPOSE: To import Clinical Logic workbooks
%** AUTHOR: Acumen, LLC
%** DATE CREATED: 01/17/2025
%** DATE LAST MODIFIED: 02/25/2025
************************************************************************;
This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the CC0 1.0 Universal public domain dedication as indicated in LICENSE.

************************************************************************/
%macro a00_03_import_logic();
   %mkdirs(&out_path.\output,&out_path.\output\ref);
   libname ref "&out_path.\output\ref";

   %*import ip ce_id drg xwalk;
   proc import out=ip_ce_drg
      datafile="&logic_path.\&clinical_logic_date._bpci_a_trigger_list.xlsx"
      dbms=xlsx replace;
      sheet="IP_Anchor_Episode_List";
      DATAROW= &cl_data_start_row.;
      getnames=no;
   run;

   proc sql;
      create table ref.ip_ce_drg as
      select distinct
         d as episode_group_id format=$5. length=5,
         c as ce_description,
         "ip" as anchor_type,
         substr(strip(c),1,2) as epi_type,
         e as drg format=$3. length=3
      from ip_ce_drg
      where not missing(d)
      order by substr(d,4,2);
   quit;

   %*import op ce_id apc xwalk;
   proc import out=op_ce
      datafile="&logic_path.\&clinical_logic_date._bpci_a_trigger_list.xlsx"
      dbms=xlsx replace;
      sheet="OP_Anchor_Episode_List";
      DATAROW= &cl_data_start_row.;
      getnames=no;
   run;

   proc import out=op_apc
      datafile="&logic_path.\&clinical_logic_date._bpci_a_hcpcs_apc_mapping.xlsx"
      dbms=xlsx replace;
      sheet="BPCI_A_Historical_Mapping";
      DATAROW= &cl_data_start_row.;
      getnames=no;
   run;

   proc sql;
      create table ref.op_ce as
      select distinct d as episode_group_id format=$5. length=5,
             c as ce_description format=$70. length=70,
             "op" as anchor_type,
             substr(strip(c),1,2) as epi_type
      from op_ce
      order by d;

      create table ref.op_apc as
      select c as ce_description format=$70. length=70,
             d as year,
             g as apc format=$4. length=4
      from op_apc
      where not missing(g)
      union all
      select c as ce_description format=$70. length=70,
             d as year,
             n as apc format=$4. length=4
      from op_apc
      where not missing(n);

      create table ref.op_ce_apc as
      select distinct a.episode_group_id,
             a.anchor_type,
             a.epi_type,
             b.*
      from ref.op_ce a,
           ref.op_apc b
      where a.ce_description = b.ce_description
      order by substr(episode_group_id,4,2);
   quit;

   data ref.ce_id_epi_type_all;
      set ref.ip_ce_drg (keep = EPISODE_GROUP_ID CE_DESCRIPTION EPI_TYPE )
          ref.op_ce (keep = EPISODE_GROUP_ID CE_DESCRIPTION EPI_TYPE);

      ce_id =substr(strip(EPISODE_GROUP_ID),4,2);
   run;

   proc sort nodupkey data = ref.ce_id_epi_type_all;
      by ce_id EPISODE_GROUP_ID CE_DESCRIPTION EPI_TYPE;
   run;

   *define the columns to be kept from each workbook sheet;
   %macarray(vars, tha
                  ~ tsa
                  , dlm= ~);

   %let keep_cols = C D E F G H;
   %macarray(kept_var, &keep_cols.);

   *define the new column name that each kept column will be renamed to;
   %macarray(rename_var, Covariate ICD_Version Source_DGN_code Code_Specification ICD_Diagnosis_Code Code_Description);

   *define the column length of each kept column;
   %macarray(length_var, $100. $10. $10. $20. $10. $300.);


   %do t = 1 %to &nvars.;
      filename &&vars&t.._dgn "&logic_path.\&clinical_logic_date._Stage_0_&&vars&t.._diagnosis_codes.xlsx";
      *import THA covariates list;
      proc import out = ref.&&vars&t.._covariates_list(keep=C rename=(C=Variables))
         datafile = &&vars&t.._dgn
         dbms = xlsx
         replace;
         sheet = "Covariates";
         datarow = &dgn_start_row.;
         getnames = no;
      run;

      *read in covariates_list and assign as macarray;
      proc sql noprint;
         select
            substr(VARIABLES, 5, lengthn(VARIABLES)),
            case when lengthn(substr(VARIABLES, 5)) > 29 then substr(VARIABLES, 5, 29) else substr(VARIABLES, 5, lengthn(VARIABLES)) end
        into :cov_sheet_name_list separated by "~",
             :cov_ds_name_list separated by "~" from ref.&&vars&t.._covariates_list;
      quit;
      %macarray(ds_names, &cov_ds_name_list., dlm = "~" );
      %macarray(sheet_names, &cov_sheet_name_list., dlm = "~" );

      *import trigger codes from clinical logic workbook;
      %do a = 1 %to &nds_names.;
         proc import out = ref.&&ds_names&a.._&&vars&t.. (keep = &keep_cols. rename = (%do b = 1 %to &nkept_var.; &&kept_var&b.. = &&rename_var&b.. %end;))
            datafile = &&vars&t.._dgn
            dbms = xlsx
            replace;
            sheet = "&&sheet_names&a..";
            datarow = &dgn_start_row.;
            getnames = no;
         run;

         *apply basic formatting edits to imported datasets;
         data ref.&&ds_names&a.._&&vars&t..;
            length %do b = 1 %to &nrename_var.; &&rename_var&b.. &&length_var&b.. %end;;
            set ref.&&ds_names&a.._&&vars&t..;
            %do b = 1 %to &nrename_var.;
                &&rename_var&b.. = strip(&&rename_var&b..);
            %end;
         run;
      %end;
   %end;

   *import THA Procedure Code List;
   filename fname "&logic_path.\&medical_code_list._bpci_medical_code_lists.xlsx";
   proc import out=ref.proc_cd_list(keep=C D E rename=(C=MS_DRG D=ICD10_PCS E=DESCRIPTION))
      datafile=fname dbms=xlsx replace;
      datarow = &cl_data_start_row.;
      getnames=no;
      sheet = "THA_Codes";
   run;

%mend;
