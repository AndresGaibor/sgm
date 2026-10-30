/* priority: P0 */
data work.scored; set work.applications; if score>=600 then band='A'; else band='B'; run;
