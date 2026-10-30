/* priority: P2 */
data work.enriched; if _n_=1 then do; declare hash h(dataset:'work.reference'); h.definekey('code'); h.definedata('description'); h.definedone(); end; set work.input; h.find(); run;
