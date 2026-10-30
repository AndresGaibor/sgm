/* priority: P2 */
proc sql noprint; select name into :columns separated by ',' from dictionary.columns where libname='WORK'; quit;
