/* priority: P0 */
data work.priced; set work.items; length price_band $8; if missing(price) then price_band='UNKNOWN'; else if price>=1000 then price_band='HIGH'; else price_band='STANDARD'; run;
