/* priority: P1 */
/* Una cadena con elementos repetidos requiere expandir filas; revisar delimitadores vacíos. */
data work.tag_rows; set work.topic_tags; do i=1 to countw(tags,','); tag=strip(scan(tags,i,',')); if not missing(tag) then output; end; keep topic_id tag; run;
