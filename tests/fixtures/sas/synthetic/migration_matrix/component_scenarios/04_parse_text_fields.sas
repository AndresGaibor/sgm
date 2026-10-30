/* priority: P1 */
data work.parsed; set work.messages; first_word=scan(message,1,' '); prefix=substr(message,1,4); token_count=countw(message); run;
