/* priority: P1 */
data work.numeric_values; set work.raw_values; amount_num=input(compress(amount_text,','),best32.); amount_text_out=put(amount_num,comma12.2); run;
