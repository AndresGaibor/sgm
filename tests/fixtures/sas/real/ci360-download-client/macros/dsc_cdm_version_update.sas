/*-----------------------------------------------------------------------------
 Copyright  2020, SAS Institute Inc., Cary, NC, USA.  All Rights Reserved.
 SPDX-License-Identifier: Apache-2.0
-----------------------------------------------------------------------------*/
%macro dsc_cdm_version_update(version_num=);
	%let ver_hist_ds=dsccnfg.cdm_version_hist;
	/* if migrating from old version to schema16 then update the modified tables as per schema16 changes;*/
	%if &version_num. = 16 %then
	%do;
		%if %sysfunc(exist(&ver_hist_ds.)) %then
		%do;
			/* what is the old version num ;*/
			proc sql noprint;
				select max(ver_num) into :cdm_ver_num from &ver_hist_ds. ;
			quit;

			/* if current version is less than 16 that means we need to alter the existing tables ;*/
			%if &cdm_ver_num. < 16 %then
			%do;
				/* modify following datasets to change owner_nm & created_user_nm length to 256 char;*/
				%let dataset_list = CDM_CONTENT_DETAIL CDM_TASK_DETAIL;
			    %local i dataset;
			    %do i = 1 %to %sysfunc(countw(&dataset_list)); /* Loop through the dataset list */
			        %let dataset = %scan(&dataset_list, &i); /* Get the current dataset name */
			        %let table_nm = dscwh.&dataset; /* Set the table name */
					%put updating &table_nm.;
			        %if %sysfunc(exist(&table_nm.)) %then 
					%do; /* Check if dataset exists */
			            data &table_nm._bkp; /* Create backup dataset */
			                set &table_nm.;
			            run;
			            data &table_nm.; /* Modify original dataset */
			                attrib owner_nm FORMAT=$256.
			                    created_user_nm FORMAT=$256.;
			                set &table_nm.;
			            run;
			        %end;
					%else
					%do;
						%put &table_nm. not found ;
					%end;
			    %end;

			    data cdm_version_hist;
					    attrib ver_num length= 8.
			               ver_create_dttm length=8. format=datetime25.6;
			        ver_num =&version_num.;
			        ver_create_dttm =datetime();
			    run;

				proc append base=dsccnfg.cdm_version_hist data=cdm_version_hist;
			    run;
			%end;
		%end;
		%else
		%do;
		    data cdm_version_hist;
				    attrib ver_num length= 8.
		               ver_create_dttm length=8. format=datetime25.6;
		        ver_num =&version_num.;
		        ver_create_dttm =datetime();
		    run;

			proc append base=dsccnfg.cdm_version_hist data=cdm_version_hist;
		    run;
		%end;
	%end;
%EXIT:

%mend dsc_cdm_version_update;
