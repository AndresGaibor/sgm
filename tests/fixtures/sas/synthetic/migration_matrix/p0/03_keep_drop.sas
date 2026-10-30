/* priority: P0 */
data work.customer; set work.raw; keep id name region; drop private_note; run;
