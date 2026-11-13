%let repeticiones = 15;
/* Etiqueta: Crea_Cars */
data WORK.cars_poc;
set sashelp.cars;
run;


/* Etiqueta: Ciclo_Append */
%macro append_all;
%do i=1 %to &repeticiones.;
/* CREA UNA TABLA DE 2 GIGAS Y 14'024.704 DE REGISTROS */
proc append
base=WORK.cars_poc
data=WORK.cars_poc;
run;

%end;
%mend append_all;

%append_all;

proc sql;
select count (*) from WORK.cars_poc;
quit;


/* Etiqueta: ACURA */
%web_drop_table(WORK.ACURA);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL; 
CREATE TABLE WORK.ACURA 
AS 
SELECT CARS_POC.Make, CARS_POC.Model, CARS_POC.Type, CARS_POC.Origin, CARS_POC.DriveTrain, CARS_POC.MSRP, CARS_POC.Invoice, CARS_POC.EngineSize, CARS_POC.Cylinders, CARS_POC.Horsepower, CARS_POC.MPG_City, CARS_POC.MPG_Highway, CARS_POC.Weight, CARS_POC.Wheelbase, CARS_POC.Length 
FROM WORK.CARS_POC CARS_POC 
WHERE 
   ( CARS_POC.Make = 'Acura' ) ; 
QUIT;

%web_open_table(WORK.ACURA);

/* Etiqueta: JAGUAR */
%web_drop_table(WORK.JAGUAR);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL; 
CREATE TABLE WORK.JAGUAR 
AS 
SELECT CARS_POC.Make, CARS_POC.Model, CARS_POC.Type, CARS_POC.Origin, CARS_POC.DriveTrain, CARS_POC.MSRP, CARS_POC.Invoice, CARS_POC.EngineSize, CARS_POC.Cylinders, CARS_POC.Horsepower, CARS_POC.MPG_City, CARS_POC.MPG_Highway, CARS_POC.Weight, CARS_POC.Wheelbase, CARS_POC.Length 
FROM WORK.CARS_POC CARS_POC 
WHERE 
   ( CARS_POC.Make = 'Jaguar' ) ; 
QUIT;

%web_open_table(WORK.JAGUAR);

/* Etiqueta: BMW */
%web_drop_table(WORK.BMW);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL; 
CREATE TABLE WORK.BMW 
AS 
SELECT CARS_POC.Make, CARS_POC.Model, CARS_POC.Type, CARS_POC.Origin, CARS_POC.DriveTrain, CARS_POC.MSRP, CARS_POC.Invoice, CARS_POC.EngineSize, CARS_POC.Cylinders, CARS_POC.Horsepower, CARS_POC.MPG_City, CARS_POC.MPG_Highway, CARS_POC.Weight, CARS_POC.Wheelbase, CARS_POC.Length 
FROM WORK.CARS_POC CARS_POC 
WHERE 
   ( CARS_POC.Make = 'BMW' ) ; 
QUIT;

%web_open_table(WORK.BMW);

/* Etiqueta: CONTADOR_ACURA */
proc sql;
select count (*) from WORK.ACURA;
quit;

/* Etiqueta: CONTADOR_BMW */
proc sql;
select count (*) from WORK.BMW;
quit;

/* Etiqueta: CHEVROLET */
%web_drop_table(WORK.CHEVROLET);

/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL; 
CREATE TABLE WORK.CHEVROLET 
AS 
SELECT CARS_POC.Make, CARS_POC.Model, CARS_POC.Type, CARS_POC.Origin, CARS_POC.DriveTrain, CARS_POC.MSRP, CARS_POC.Invoice, CARS_POC.EngineSize, CARS_POC.Cylinders, CARS_POC.Horsepower, CARS_POC.MPG_City, CARS_POC.MPG_Highway, CARS_POC.Weight, CARS_POC.Wheelbase, CARS_POC.Length 
FROM WORK.CARS_POC CARS_POC 
WHERE 
   ( CARS_POC.Make = 'Chevrolet' ) ; 
QUIT;

%web_open_table(WORK.CHEVROLET);

/* Etiqueta: CONTADOR_CHEVROLET */
proc sql;
select count (*) from WORK.CHEVROLET;
quit;

/* Etiqueta: CONTADOR_JAGUAR */
proc sql;
select count (*) from WORK.JAGUAR;
quit;

