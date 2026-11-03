# teltmysqlinput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/teltmysqlinput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/teltmysqlinput -->

# Building a Job

## Procedure

1. Add the following components from the Palette onto the design workspace. Label these components to best describe their functionality.
   * three tELTMysqlInput components
   * a tELTMysqlMap
   * a tELTMysqlOutput
2. Double-click the first tELTMysqlInput component to display its Basic settings view.

   ![](https://help.qlik.com/talend/en-US/components/Resources/images/Use_Case_tELTMysqlMap1-2.png)
3. Select Repository from the Schema list, click the three dot button preceding Edit schema, and select your DB connection and the desired schema from the Repository Content dialog box.

   The selected schema name appears in the Default Table Name field automatically.

   In this use case, the DB connection is *Talend\_MySQL* and the schema for the first input component is *owners*.
4. Set the second and third tELTMysqlInput components in the same way but select *cars* and *resellers* respectively as their schema names.

   Information noteNote: In this use case, all the involved schemas are stored in the Metadata node of the Repository tree view for easy retrieval. For further information concerning metadata, see [Managing metadata in Talend Studio](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/managing-metadata-in-studio).

   You can also select the three input components by dropping the relevant schemas from the Metadata area onto the design workspace and double-clicking tELTMysqlInput from the Components dialog box. Doing so allows you to skip the steps of labeling the input components and defining their schemas manually.
5. Connect the three tELTMysqlInput components to the tELTMysqlMap component using links named following strictly the actual DB table names: *owners*, *cars* and *resellers*.
6. Connect the tELTMysqlMap component to the tELTMysqlOutput component and name the link *agg\_result*, which is the name of the database table you will save the aggregation result to.
7. Click the tELTMysqlMap component to display its Basic settings view.

   ![](https://help.qlik.com/talend/en-US/components/Resources/images/Use_Case_tELTMysqlMap1-3.png)
8. Select Repository from the Property Type list, and select the same DB connection that you use for the input components.

   All the database details are automatically retrieved.

   Information noteTip: Leave all the other settings as they are.
9. Double-click the tELTMysqlMap component to launch the ELT Map editor to set up joins between the input tables and define the output flow.
10. Add the input tables by clicking the [+] button on the upper left corner of the ELT Map editor and selecting the relevant table names in the pop-up dialog box.
11. Drop the ID\_Owner column from the owners table to the corresponding column of the cars table.
12. In the *cars* table, select the Explicit join check box in front of the *ID\_Owner* column.

    As the default join type, INNER JOIN is displayed on the Join list.
13. Drop the ID\_Reseller column from the cars table to the corresponding column of the resellers table to set up the second join, and define the join as an inner join in the same way.
14. Select the columns to be aggregated into the output table, agg\_result.
15. Drop the ID\_Owner, Name, and ID\_Insurance columns from the owners table to the output table.
16. Drop the Registration, Make, and Color columns from the cars table to the output table.
17. Drop the Name\_Reseller and City columns from the resellers table to the output table.

    With the relevant columns selected, the mappings are displayed in yellow and the joins are displayed in dark violet.
18. Set up a filter in the output table. Click the Add filter row button on top of the output table to display the Additional clauses expression field, drop the *City* column from the *resellers* table to the expression field, and complete a WHERE clause that reads resellers.City ='Augusta'.

    ![](https://help.qlik.com/talend/en-US/components/Resources/images/UseCase_teltmysqlmap-1-5_top.png)
19. Click the Generated SQL Select query tab to display the corresponding SQL statement.

    ![](https://help.qlik.com/talend/en-US/components/Resources/images/use_case-tetlmysqlmap5Half.png)
20. Click OK to save the ELT Map settings.
21. Double-click the tELTMysqlOutput component to display its Basic settings view.

    ![](https://help.qlik.com/talend/en-US/components/Resources/images/Use_Case_tELTMysqlMap1-6.png)
22. Select an action from the Action on data list as needed.
23. Select Repository as the schema type, and define the output schema in the same way as you defined the input schemas. In this use case, select *agg\_result* as the output schema, which is the name of the database table used to store the mapping result.

    Information noteNote: You can also use a built-in output schema and retrieve the schema structure from the preceding component; however, make sure that you specify an existing target table having the same data structure in your database.

    Information noteTip: Leave all the other settings as they are.
