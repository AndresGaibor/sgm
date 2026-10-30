/* priority: P2 */
data _null_; set work.tasks; call execute(cats('%include ',quote(trim(path)),';')); run;
