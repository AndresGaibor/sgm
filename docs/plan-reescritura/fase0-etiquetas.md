# Fase 0: etiquetas por región de client_large.sas

Programa: `client_large.sas`. Agrupación: `client_large.agrupacion.yaml`.
Generado por `tools/etiquetas_fase0.py`. Las cifras salen de ese script.

## Resumen

- Regiones: 30.
- Etiquetas totales: 610.
- Etiquetas normalizadas distintas: 282.
- Etiquetas presentes en los tres productos: 21.

## Regiones

| Región | Líneas | Producto | Sufijos contados | Etiquetas |
|---|---|---|---|---|
| 1 | 1-2305 | aho | aho=136, cte=14, nequi=30 | 80 |
| 2 | 2306-2870 | aho | aho=172 | 13 |
| 3 | 2871-4287 | aho | aho=731, cte=41 | 58 |
| 4 | 4288-4821 | cte | cte=117 | 10 |
| 5 | 4822-5386 | cte | cte=172 | 13 |
| 6 | 5387-9651 | cte | aho=108, cte=1038, nequi=527 | 173 |
| 7 | 9652-10166 | aho | aho=34 | 6 |
| 8 | 10167-10746 | aho | aho=32 | 10 |
| 9 | 10747-11059 | aho | aho=4 | 1 |
| 10 | 11060-11425 | aho | aho=45 | 2 |
| 11 | 11426-11983 | aho | aho=56, cte=1 | 9 |
| 12 | 11984-12497 | cte | cte=42 | 6 |
| 13 | 12498-13077 | cte | cte=32 | 10 |
| 14 | 13078-13390 | cte | cte=4 | 1 |
| 15 | 13391-13756 | cte | cte=45 | 2 |
| 16 | 13757-14481 | cte | cte=56, nequi=35 | 15 |
| 17 | 14482-15064 | nequi | nequi=50 | 9 |
| 18 | 15065-16388 | nequi | aho=94, nequi=198 | 35 |
| 19 | 16389-16716 | aho | aho=10 | 2 |
| 20 | 16717-17140 | aho | aho=91 | 5 |
| 21 | 17141-17453 | aho | aho=3 | 1 |
| 22 | 17454-18099 | aho | aho=50 | 10 |
| 23 | 18100-18412 | aho | aho=3 | 1 |
| 24 | 18413-18725 | sin_producto | - | 1 |
| 25 | 18726-19562 | cte | aho=66, cte=94 | 15 |
| 26 | 19563-19890 | cte | cte=10 | 2 |
| 27 | 19891-20314 | cte | cte=97 | 5 |
| 28 | 20315-20627 | cte | cte=4 | 1 |
| 29 | 20628-21188 | cte | cte=56 | 6 |
| 30 | 21189-24801 | cte | aho=349, cte=375, nequi=318 | 108 |

## Productos

| Producto | Regiones | Etiquetas | Etiquetas distintas |
|---|---|---|---|
| aho | 13 | 198 | 157 |
| cte | 14 | 367 | 217 |
| nequi | 2 | 44 | 36 |
| sin_producto | 1 | 1 | 1 |

## Jaccard de etiquetas entre productos

| Par | Jaccard |
|---|---|
| aho-cte | 0.3801 |
| aho-nequi | 0.1221 |
| cte-nequi | 0.1145 |

## Etiquetas presentes en los tres productos

Total: 21.

- calculo dv
- campo apellido
- campo codigo ubicacion
- campo dpto
- campo mun
- campo nombre
- campo pais
- campo razon social
- completar direccion
- completar nombre
- default dir inv
- elimina caracter especial
- escritura sabana_info_cname
- filtro direcciones
- nro registros sabana completa
- organizar campos
- quitar espacios en blanco
- sabana con dir
- sabana final
- sabana unica dir
- validar dir

## Secuencia de la región más grande por producto

### aho (región 1, 80 etiquetas)

1. macrovariables
2. importar homologacion tdoc
3. importar pais
4. formato de campos
5. encriptar clave
6. importar codigos dane
7. importar validacion fecha
8. homologacion tdoc
9. importar clientes
10. filtro master customer
11. validacion ult dia ingestion tabla firmas
12. nombre columnas
13. validacion ult dia ingestion mcd
14. importar depositos corriente
15. convierte nro_cta a numero
16. convierte llave_nombre a numero
17. convierte tipo_doc a numero
18. convierte nro_doc a numero
19. convierte gmf a numero
20. convierte val_cred_mes a texto
21. convierte prom_cred_mes a texto
22. convierte med_cred_mes a texto
23. convierte val_deb_mes a texto
24. convierte prom_deb_mes a texto
25. convierte med_saldo_cta a texto
26. convierte prom_saldo_cta a texto
27. convierte max_saldo_cta a texto
28. convierte min_saldo_cta a texto
29. convierte fin_saldo_cta a texto
30. organizar campos
31. formato fin saldo cuenta
32. suma saldo final corriente
33. saldo final corriente
34. importar ahorros depositos
35. convierte nro_cta a numero
36. convierte llave_nombre a numero
37. convierte tipo_doc a numero
38. convierte nro_doc a numero
39. convierte gmf a numero
40. convierte val_cred_mes a texto
41. convierte prom_cred_mes a texto
42. convierte med_cred_mes a texto
43. convierte val_deb_mes a texto
44. convierte prom_deb_mes a texto
45. convierte med_saldo_cta a texto
46. convierte prom_saldo_cta a texto
47. convierte max_saldo_cta a texto
48. convierte min_saldo_cta a texto
49. convierte fin_saldo_cta a texto
50. organizar campos
51. filtrar cuentas afc
52. cuentas afc y relaciones
53. sabana_sin_afc
54. formato fin saldo cuenta
55. suma saldo final ahorros
56. saldo final ahorros
57. importar
58. form num saldofin dbiftcs
59. nombre columnas
60. suma saldofin dbiftcs
61. suma saldo final corriente 1
62. saldofin dbiftcs
63. saldo final
64. validar_mes_ano
65. conv a texto fecha validacion
66. numero de registros
67. concatenar fecha de validacion
68. condicion continuar ejecucion
69. convertir de texto a numerico
70. escritura columnas_depositos
71. completar tipo y numero doc
72. tipo doc cname
73. campo concat
74. orden campos
75. quita prefijo de extranj
76. organizar campos
77. convertir de texto a numerico
78. orden a campos
79. sabana sin fa
80. escritura reemplazo_nid_ext

### cte (región 6, 173 etiquetas)

1. tit-cot vacios o
2. fa vacios o
3. nro doc no vacio ni cero
4. campo inconsistencia
5. campo inconsistencia
6. frecuencia de registros
7. paq tit- cot
8. cuenta frecuencia
9. firmas autorizadas duplicadas
10. suma duplicados
11. sabana sin vacios o
12. campo inconsistencia
13. tipo doc invalido
14. tipo doc valido
15. tipo doc invalido fa
16. tipo doc invalido tit- cot
17. organizar campos
18. paquete tipo de documento tit- cot
19. incons tipo doc invalido
20. sabana sin tpo doc inv
21. tipo cuenta invalido
22. campo inconsistencia
23. tpo cta con relaciones
24. sabana sin tpo cta invalido
25. codex invalido
26. campo inconsistencia
27. gmf con relaciones
28. sabana sin gmf inv
29. campos vacios
30. campos vacios y relaciones
31. sabana final
32. incons corregidas
33. incons por corregir
34. incons sin campo inco
35. nro inconsistencias corregidas
36. nro registros final
37. incons sin campo inco
38. orden registros
39. nro inconsistencias por corregir
40. inconsistencias coinciden
41. suma saldo sabana final
42. eliminar reg rep
43. nro inconsistencias rep
44. suma saldo sabana incon
45. nro incons duplcados
46. incon rep sin dup
47. suma incons
48. total cuentas
49. calculo conciliacion
50. calculo conciliacion saldos
51. conciliacion final
52. cuenta inicial
53. homologar tpo doc
54. sin nro doc vacios
55. nro doc vacios
56. tpo cta invalido
57. sin tpo cuenta vacios
58. campo inconsistencia
59. campo inconsistencia
60. gmf invalido
61. sin gmf invalido
62. campo inconsistencia
63. tipo doc invalido
64. sin tpo doc invalido
65. campo inconsistencia
66. nro cuenta invalido
67. sin nro cta invalido
68. campo inconsistencia
69. tpo doc 8 invalido
70. tpo doc 7 invalido
71. tpo doc 4 invalido
72. tpo doc 3 invalido
73. tpo doc 2 invalido
74. tpo doc 1 invalido
75. cons doc incorr
76. incons consol
77. sabana valida
78. nro incons
79. nro reg sabana final
80. conciliacion
81. calculo conciliacion reg
82. calculo conciliacion saldo
83. conciliacion final
84. convertir val_cred_mes
85. cambiar form
86. convertir val_cred_mes
87. organizar campos
88. convertir prom_cred_mes
89. campo
90. convertir prom_cred_mes
91. convertir med_cred_mes
92. convertir med_cred_mes
93. convertir val_deb_mes
94. convertir val_deb_mes
95. convertir prom_deb_mes
96. convertir prom_deb_mes
97. convertir med_saldo_cta
98. convertir med_saldo_cta
99. convertir prom_saldo_cta
100. convertir prom_saldo_cta
101. convertir max_saldo_cta
102. convertir max_saldo_cta
103. convertir min_saldo_cta
104. convertir min_saldo_cta
105. convertir fin_saldo_cta
106. convertir fin_saldo_cta
107. organizar campos
108. organizar campos
109. consolidado
110. eliminar negativos en campo val_cred_mes
111. eliminar negativos en campo fin_sal_cta
112. suma saldos
113. cumple norma
114. sabana cumple norma
115. sabana no cumple
116. cumple norma
117. cumple norma corriente
118. cumple norma ahorros
119. campos neg
120. sabana reportar
121. eliminar val negativos
122. campos neg
123. no cumple norma corriente
124. no cumple norma
125. no cumple norma ahorros
126. nro registros no cumplen
127. paq no cumple norma
128. nro incons campos neg
129. eliminar val negativos
130. eliminar val negativos
131. incons campos neg
132. campos neg
133. sabana reportar
134. incons campos neg
135. nro incons campos neg
136. eliminar val negativos
137. eliminar val negativos
138. nro registros no cumplen
139. paq no cumple norma
140. eliminar val negativos
141. eliminar val negativos
142. nro incons campos neg
143. eliminar val negativos
144. eliminar val negativos
145. eliminar val negativos
146. nro registros no cumplen
147. eliminar val negativos
148. eliminar val negativos
149. eliminar val negativos
150. eliminar val negativos
151. eliminar val negativos
152. eliminar val negativos
153. eliminar val negativos
154. nro reg reportar
155. nro reg reportar
156. conciliacion
157. eliminar val negativos
158. campo conciliacion reg
159. conciliacion
160. campo conciliacion saldos
161. eliminar val negativos
162. conciliacion final
163. campo conciliacion reg
164. eliminar val negativos
165. campo conciliacion saldos
166. eliminar val negativos
167. conciliacion final
168. nro reg reportar
169. conciliacion
170. campo conciliacion reg
171. campo conciliacion saldos
172. conciliacion final
173. escritura sabana_final_reportar_ahorros

### nequi (región 18, 35 etiquetas)

1. elimina caracter especial
2. completar direccion
3. crea campo codigo ubicacion
4. quitar espacios en blanco
5. campo nombre
6. validar dir
7. formato nro doc
8. filtro direcciones
9. campo nombre
10. organizar base
11. campo apellido
12. completar info clientes
13. campo apellido
14. calcula dv
15. campo razon social
16. sabana con dir
17. sabana unica dir
18. default dir inv
19. campo dpto
20. campo mun
21. campo pais
22. campo codigo ubicacion
23. organizar campos
24. sabana final
25. nro registros sabana completa
26. validacion tipo doc
27. validacion tipo doc
28. validacion tipo doc
29. validacion tipo doc
30. validacion tipo doc
31. validacion tipo doc
32. cons doc incorr
33. doc incorr fa y cot
34. doc incorr titulares
35. escritura sabana_completa

## Similitud de secuencias entre regiones mayores (SequenceMatcher)

| Par | Ratio |
|---|---|
| aho-cte | 0.0237 |
| aho-nequi | 0.0174 |
| cte-nequi | 0.0288 |

## Conclusión

Pregunta: ¿las regiones de un mismo producto son etapas consecutivas de un proceso (vocabulario común y secuencia parecida) o piezas sin relación?

Hay vocabulario compartido: la mayor coincidencia es aho-cte (Jaccard 0.3801), y 21 de 282 etiquetas distintas aparecen en los tres productos.

La secuencia de las regiones mayores casi no coincide (similitud máxima 0.0288), así que no hay un orden parecido entre productos.

Lectura honesta: las cifras no demuestran que las regiones sean etapas de un proceso. Las etiquetas compartidas son genéricas (p. ej. «organizar campos», «sabana final», «campo apellido»), lo que describe operaciones repetidas y no una secuencia. Además, las regiones grandes mezclan tablas de varios productos, así que la asignación por sufijo no separa limpiamente los procesos. Con estos datos la pregunta queda sin respuesta concluyente: hace falta leer el orden de ejecución de cada región.
