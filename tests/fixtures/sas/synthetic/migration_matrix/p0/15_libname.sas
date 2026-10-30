/* priority: P0 */
libname src '/example/not-mounted';
data work.active; set src.members; where status='ACTIVE'; run;
