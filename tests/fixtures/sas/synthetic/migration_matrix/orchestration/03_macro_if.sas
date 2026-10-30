/* priority: P1 */
%macro choose_source(test=Y); %if &test=Y %then %let source=work.sample; %else %let source=work.production_placeholder; %mend;
%choose_source(test=Y)
