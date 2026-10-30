/* priority: P1 */
data work.merged; merge work.people work.addresses; by person_id; run;
