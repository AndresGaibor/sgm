/* priority: P1 */
data work.checked; set work.scores; if missing(score) then flag='MISSING'; else flag='VALID'; run;
