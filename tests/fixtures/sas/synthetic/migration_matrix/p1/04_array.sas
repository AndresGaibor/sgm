/* priority: P1 */
data work.annual; set work.monthly; array m[3] jan feb mar; total=0; do i=1 to 3; total=total+m[i]; end; run;
