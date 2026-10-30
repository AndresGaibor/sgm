/* priority: P1 */
/* Lookup en memoria; en Talend candidato tMap lookup o tHashInput según volumen. */
data work.product_labels; if _n_=1 then do; declare hash ref(dataset:'work.product_ref'); ref.definekey('product_id'); ref.definedata('product_name'); ref.definedone(); end; set work.sales; ref.find(); run;
