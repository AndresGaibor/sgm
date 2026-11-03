# tmap (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tmap  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap -->

# tMap

### In this section

* [tMap component](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-component)
* [tMap scenarios](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-scenario)
* [tMap related topics](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-other)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-component -->

# tMap component

| [tMap](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap) | Transforms and routes data from single or multiple sources to single or multiple<br>destinations. |
| --- | --- |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-scenario -->

# tMap scenarios

* [Advanced mapping with lookup reload at each row](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tmysqlinput-tmysqloutput-tmysqlcommit-advanced-mapping-with-lookup-reload-at-each-row-standard-component-the)
* [Converting a UNIX timestamp to a readable date](https://help.qlik.com/talend/en-US/components/8.0/tmap/converting-a-unix-timestamp-to-a-readable-date)
* [Mapping data using a filter and a simple explicit join](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-mapping-data-using-filter-and-simple-explicit-join-standard-component-the-job)
* [Mapping with join output tables](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tlogrow-tfileinputdelimited-tfileinputdelimited-mapping-with-join-output-tables-standard-component-the)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-other -->

# tMap related topics

### In this section

* [The differences between Unique match, First match and All matches](https://help.qlik.com/talend/en-US/components/8.0/tmap/differences-between-unique-match-first-match-and-all-matches)
* [Similarities and differences between a tJoin and a tMap component?](https://help.qlik.com/talend/en-US/components/8.0/tmap/similarities-and-differences-between-tjoin-and-tmap-component)
* [tMap expression syntax](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-expression-syntax)
* [tMap lookup models](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-lookup-models)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap -->

# tMap

Transforms and routes data from single or multiple sources to single or multiple destinations.

tMap is an advanced component, which integrates itself as plugin to Talend Studio.

Information noteTip:

There is no order among the output flows of tMap. To make the output flows to be executed one by one, you can output them to temporary files or memory, and then read and insert them into files or databases using different subJobs linked by Trigger &gt; OnSubjobOK connections.

### In this section

* [tMap Standard properties](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-standard-properties)
* [tMap properties for Apache Spark Batch](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-properties-for-apache-spark-batch)
* [tMap properties for Apache Spark Streaming (deprecated)](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-properties-for-apache-spark-streaming)
* [tMap properties for Apache Spark Structured Streaming](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-properties-for-apache-spark-structured-streaming)

**Related concepts**

* [Mapping data using a filter and a simple explicit join](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-mapping-data-using-filter-and-simple-explicit-join-standard-component-the-job)

**Related tasks**

* [Advanced mapping with lookup reload at each row](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tmysqlinput-tmysqloutput-tmysqlcommit-advanced-mapping-with-lookup-reload-at-each-row-standard-component-the)
* [Converting a UNIX timestamp to a readable date](https://help.qlik.com/talend/en-US/components/8.0/tmap/converting-a-unix-timestamp-to-a-readable-date "A Unix timestamp is a series of numbers non-human readable such as 13959.583,1330578363. This scenario shows how to convert it to a readable date or map it to the target system format.")
* [Mapping with join output tables](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tlogrow-tfileinputdelimited-tfileinputdelimited-mapping-with-join-output-tables-standard-component-the "The following scenario describes a Job that processes reject flows without separating them from the main flow.")


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tmysqlinput-tmysqloutput-tmysqlcommit-advanced-mapping-with-lookup-reload-at-each-row-standard-component-the -->

# Advanced mapping with lookup reload at each row

The following scenario describes a Job that retrieves people details from a lookup database, based on a join on the age. The main flow source data is read from a MySQL database table called *people\_age* that contains people details such as numeric id, alphanumeric first name and last name and numeric age. The people age is either 40 or 60. The number of records in this table is intentionally restricted.

The reference or lookup information is also stored in a MySQL database table called *large\_data\_volume*. This lookup table contains a number of records including the city where people from the main flow have been to. For the sake of clarity, the number of records is restricted but, in a normal use, the usefulness of the feature described in the example below is more obvious for very large reference data volume.

To optimize performance, a database connection component is used in the beginning of the Job to open the connection to the lookup database table in order not to do that every time you want to load a row from the lookup table.

An Expression Filter is applied to this lookup source flow in order to select only data from people whose age is equal to 60 or 40. This way only the relevant rows from the lookup database table are loaded for each row from the main flow.

Therefore this Job shows how, from a limited number of main flow rows, the lookup join can be optimized to load only results matching the expression key.

Information noteNote:

Generally speaking, as the lookup loading is performed for each main flow row, this option is mainly interesting when a limited number of rows is processed in the main flow while a large number of reference rows are to be looked up to.

The join is solved on the *age* field. Then, using the relevant loading option in the tMap component editor, the lookup database information is loaded for each main flow incoming row.

For this Job, the metadata has been prepared for the source and connection components. For more information on how to set up the DB connection schema metadata, see [Centralizing database metadata](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/centralizing-database-metadata).

This Job is formed with five components, four database components and a mapping component.

## Linking the components

### Procedure

1. Place the DB Connection under the Metadata node of the Repository to the design workspace. In this example, the source table is called *people\_age*.
2. Select tMysqlInput from the list that pops up when dropping the component.

   ![Choose one component to create. window.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap6-2-1-1.png)
3. Place the lookup DB connection table from the Metadata node to the design workspace selecting tMysqlInput from the list that pops up. In this Job, the lookup is called *large\_data\_volume*.
4. Place the DB connection from the Metadata node to the design workspace selecting tMysqlConnection from the list that pops up.

   This component creates a permanent connection to the lookup database table in order not to do that every time you want to load a row from the lookup table.
5. Pick the tMap component from the Processing family, and the tMysqlOutput and tMysqlCommit components from the Database family in the Palette to the right hand side of the editor.
6. To connect all the components together, right-click the tMysqlInput component corresponding to the *people* table and drag the link towards tMap.
7. Release the link over the tMap component, the main row flow is automatically set up.
8. Rename the Main row link to *people*, to identify more easily the main flow data.
9. Perform the same operation to connect the lookup table (*large\_data\_volume*) to the tMap component and the tMap to the tMysqlOutput component.

   A dialog box prompts for a name to the output link. In this example, the output flow is named: people\_mixandmatch
10. Rename the lookup row connection link to *large\_volume,* to help identify the reference data flow.
11. Connect tMysqlConnection to tMysqlInput using the trigger link OnSubjobOk.
12. Connect the tMysqlInput component to the tMysqlCommit component using the trigger link OnSubjobOk.

    ![Connection of components.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap6-1.png)

## Configuring the components

### Procedure

1. Double-click the tMap component to open the graphical mapping editor.

   ![Graphical mapping editor.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap6-3.png)

   The Output table (that was created automatically when you linked the tMap to the tMysqlOutput) will be formed by the matching rows from the lookup flow (large\_data\_volume) and the main flow (people\_age).
2. Select the main flow rows that are to be passed on to the output and drag them over to paste them in the Output table (to the right hand side of the mapping editor).

   Select the main flow rows that are to be passed on to the output and drag them over to paste them in the Output table (to the right hand side of the mapping editor).

   In this example, the selection from the main flow include the following fields: *id*, *first\_name*, *last\_Name* and *age*.

   From the lookup table, the following column is selected: *city*.
3. Place the selected columns from the input tables (*people* and *large\_volume*) to the output table.
4. Set up the join between the main and lookup flows.

   Select the *age* column of the main flow table (on top) and drag it towards the *age* column of the lookup flow table (*large\_volume* in this example).

   A key icon appears next to the linked expression on the lookup table. The join is now established.
5. Click the tMap settings button, click the [...] button corresponding to Lookup Model, and select the Reload at each row option from the Options dialog box in order to reload the lookup for each row being processed.

   ![Graphical mapping editor.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap6-4.png)
6. Set Match Model to All matches in the Lookup table in order to gather all instances of *age* matches in the output flow.
7. Implement the filtering, based on the *age* column, in the Lookup table. The GlobalMapKey field is automatically created when you selected the Reload at each row option. Indeed, you can use this expression to dynamically filter the reference data to load only the relevant information when joining with the main flow.

   As mentioned in the introduction of the scenario, the main flow data contains only people whose age is either 40 or 60. To avoid the pain of loading all lookup rows, including ages that are different from 40 and 60, you can use the main flow age as global variable to feed the lookup filtering.

   ![Graphical mapping editor.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap6-5.png)
8. Place the *Age* column from the main flow table to the Expr. field of the lookup table.
9. In the globalMap Key field, put in the variable name, using the expression. In this example, it reads: "people.Age"

   Click OK to save the mapping setting and go back to the design workspace.
10. To finalize the implementation of the dynamic filtering of the lookup flow, add a WHERE clause in the query of the database input.

    ![Query.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap6-6.png)
11. At the end of the Query field, following the Select statement, type in the following WHERE clause: WHERE AGE ='"+((Integer)globalMap.get("people.Age"))+"'"
12. Make sure that the type corresponds to the column used as variable. In this use case, *Age* is of *Integer* type. Use the variable the way you set in the globalMap key field of the map editor.
13. Double-click the tMysqlOutput component to define its properties.

    ![Basic settings view.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap6-7.png)
14. Select the Use an existing connection check box to leverage the created DB connection.

    Define the target table name and relevant DB actions.

## Executing the Job

### Procedure

1. Press Ctrl+S to save the Job.
2. Click the Run tab at the bottom of the design workspace, to display the Job execution tab.
3. From the Debug Run view, click the Traces Debug button to view the data processing progress.

   For more comfort, you can maximize the Job design view while executing by simply double-clicking on the Job name tab.

   ![Job design.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap6-9.png)

   The lookup data is reloaded for each of the main flow's rows, corresponding to the age constraint. All *age* matches are retrieved in the lookup rows and grouped together in the output flow.

   Therefore if you check out the data contained in the newly created *people\_mixandmatch* table, you will find all the *age* duplicates corresponding to different individuals whose age equals to 60 or 40 and the city where they have been to.

   ![Result table.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap6-10.png)

   For examples of how to use dynamic schemas with tMap, see:
   * [Writing dynamic columns from a database to an output file](https://help.qlik.com/talend/en-US/components/8.0/dynamic-schema/tmysqlinput-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-writing-dynamic-columns-from-database-to-output-file-standard-component-enterprise-in-this).

   * [Writing dynamic columns from a source file to a database](https://help.qlik.com/talend/en-US/components/8.0/mysql/writing-dynamic-columns-from-source-file-to-database).

**Related concepts**

* [tMap](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap "Transforms and routes data from single or multiple sources to single or multiple destinations.")

**Related information**

* [tMysqlInput](https://help.qlik.com/talend/en-US/components/8.0/mysql/tmysqlinput)
* [tMysqlOutput](https://help.qlik.com/talend/en-US/components/8.0/mysql/tmysqloutput)
* [tMysqlConnection](https://help.qlik.com/talend/en-US/components/8.0/mysql/tmysqlconnection)
* [tMysqlCommit](https://help.qlik.com/talend/en-US/components/8.0/mysql/tmysqlcommit)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-mapping-data-using-filter-and-simple-explicit-join-standard-component-the-job -->

# Mapping data using a filter and a simple explicit join

The Job described below aims at reading data from a csv file with its schema stored in the Repository, looking up at a reference file, the schema of which is also stored in the Repository, then extracting data from these two files based on a defined filter to an output file and reject files.

### In this section

* [Linking the components](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-linking-components-standard-component-drop)
* [Configuring how to map the data](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-configuring-how-to-map-data-standard-component)
* [Executing the Job](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-executing-job-simple-join-press)
* [Mapping data using inner join rejections](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-mapping-data-using-inner-join-rejections-standard-component-this)
* [Advanced mapping using filters, explicit joins and rejections](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-advanced-mapping-using-filters-explicit-joins-and-rejections-standard-component-this)
* [Advanced mapping with filters and different rejections](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-advanced-mapping-with-filters-and-different-rejections-standard-component-this)

**Related concepts**

* [tMap](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap "Transforms and routes data from single or multiple sources to single or multiple destinations.")

**Related information**

* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited)
* [tFileOutputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tlogrow-tfileinputdelimited-tfileinputdelimited-mapping-with-join-output-tables-standard-component-the -->

# Mapping with join output tables

The following scenario describes a Job that processes reject flows without separating them from the main flow.

## Linking the components

### Before you begin

You have created two file metadata connections under Metadata &gt; File delimited in the Repository view for the following two files.

* states.csv
* customers.csv

For more information about centralizing metadata, see [Managing metadata in Talend Studio](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/managing-metadata-in-studio).

### Procedure

1. In the Repository tree view, click Metadata &gt; File delimited. Place the customers metadata onto the workspace.

   The customers metadata contains information about customers, such as their ID, their name or their address, etc.
2. In the dialog box that asks you to choose which component type you want to use, select tFileInputDelimited and click OK.
3. Place the states metadata onto the design workspace. Select the same component in the dialog box and click OK.

   The states metadata contains the ID of the state, and its name.
4. Place a tMap and two tLogRow components from the Palette onto the design workspace.
5. Connect the customers component to the tMap, using a Row &gt; Main connection.
6. Connect the states component to the tMap, using a Row &gt; Main connection. This flow will automatically be defined as Lookup.

   ![Components connection.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap7-1.png)

## Configuring the components

### Procedure

1. Double-click the tMap component to open the Map Editor.

   Place the idState column from the main input table to the idState column of the lookup table to create a join.

   Click the tMap settings button and set Join Model to Inner Join.
2. Click the Property Settings button at the top of the input area to open the Property Settings dialog box, and clear the Die on error check box in order to handle the execution errors.

   The ErrorReject table is automatically created.

   ![Property Settings dialog box](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap7-2_TIS.png)
3. Select the id, idState, RegTime and RegisterTime in the input table and drag them to the ErrorReject table.

   ![ErrorReject table.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap7-3.png)
4. Click the [+] button at the top right of the editor to add an output table. In the dialog box that opens, select New output. In the field next to it, type in the name of the table, out1. Click OK.
5. Drag the following columns from the input tables to the out1 table: id, CustomerName, idState, and LabelState.

   Add two columns, RegTime and RegisterTime, to the end of the out1 table and set their date formats: "dd/MM/yyyy HH:mm" and "yyyy-MM-dd HH:mm:ss.SSS" respectively.
6. Click in the Expression field for the RegTime column, and press Ctrl+Space to display the auto-completion list. Find and double-click TalendDate.parseDate. Change the pattern to ("dd/MM/yyyy HH:mm",row1.RegTime).
7. Do the same thing for the RegisterTime column, but change the pattern to ("yyyy-MM-dd HH:mm:ss.SSS",row1.RegisterTime).

   ![RegisterTime column.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap7-4.png)
8. Click the [+] button at the top of the output area to add an output table. In the dialog box that opens, select Create join table from, choose Out1, and name itrejectInner. Click OK.
9. Click the tMap settings button and set Catch lookup inner join reject to true in order to handle rejects.
10. Drag the id, CustomerName, and idState columns from the input tables to the corresponding columns of the rejectInner table.

    Click in the Expression field for the LabelState column, and type in "UNKNOWN".
11. Click in the Expression field for the RegTime column, press Ctrl+Space, and select TalendDate.parseDate. Change the pattern to ("dd/MM/yyyy HH:mm",row1.RegTime).
12. Click in the Expression field for the RegisterTime column, press Ctrl+Space, and select TalendDate.parseDate, but change the pattern to ("yyyy-MM-dd HH:mm:ss.SSS",row1.RegisterTime).

    If the data from row1 has a wrong pattern, it will be returned by the ErrorReject flow.

    ![Expression field.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap7-4.png)

    Click OK to validate the changes and close the editor.
13. Double-click the first tLogRow component to display its Component view.

    Click Sync columns to retrieve the schema structure from the mapper if needed.

    In the Mode area, select Table.

    Do the same thing with the second tLogRow.

## Executing the Job

### Procedure

1. Press Ctrl+S to save your Job.
2. Press F6 to execute it.

### Results

The Run console displays the main out flow and the ErrorReject flow. The main output flow unites both valid data and inner join rejects, while the ErrorReject flow contains the error information about rows with unparseable date formats.

![Job results.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap7-5.png)

For examples of how to use dynamic schemas with tMap, see:

* [Writing dynamic columns from a database to an output file](https://help.qlik.com/talend/en-US/components/8.0/dynamic-schema/tmysqlinput-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-writing-dynamic-columns-from-database-to-output-file-standard-component-enterprise-in-this).

* [Writing dynamic columns from a source file to a database](https://help.qlik.com/talend/en-US/components/8.0/mysql/writing-dynamic-columns-from-source-file-to-database).

**Related concepts**

* [tMap](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap "Transforms and routes data from single or multiple sources to single or multiple destinations.")

**Related information**

* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)
* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-expression-syntax -->

# tMap expression syntax

This article introduces the syntax to use in the Expression Builder, to help you understand and use the tMap component.

tMap is one of the core components of Talend Studio and is used very often in Jobs. The tMap component is primarily used for mapping input fields to output fields and transforming the input data in the Expression Builder of the corresponding output column.

The Expression Builder allows you to type in a mapping expression for each column in each output table. This article presents the following syntax examples:

* [Basic mapping](https://help.qlik.com/talend/en-US/components/8.0/tmap/basic-mapping)
* [Concatenating fields](https://help.qlik.com/talend/en-US/components/8.0/tmap/concatenating-fields)
* [Setting output column with a constant](https://help.qlik.com/talend/en-US/components/8.0/tmap/setting-output-column-with-constant)
* [Outputting blank values as null or fixed values](https://help.qlik.com/talend/en-US/components/8.0/tmap/outputting-blank-values-as-null-or-fixed-values)
* [Arithmetic operation](https://help.qlik.com/talend/en-US/components/8.0/tmap/arithmetic-operation)
* [Calling a Java class method](https://help.qlik.com/talend/en-US/components/8.0/tmap/calling-java-class-method)
* [Calling a Routine](https://help.qlik.com/talend/en-US/components/8.0/tmap/calling-talend-routine)
* [If/else statement](https://help.qlik.com/talend/en-US/components/8.0/tmap/if-else-statement)
* [Filter expressions](https://help.qlik.com/talend/en-US/components/8.0/tmap/filter-expressions)

### In this section

* [Basic mapping](https://help.qlik.com/talend/en-US/components/8.0/tmap/basic-mapping)
* [Concatenating fields](https://help.qlik.com/talend/en-US/components/8.0/tmap/concatenating-fields)
* [Setting output column with a constant](https://help.qlik.com/talend/en-US/components/8.0/tmap/setting-output-column-with-constant)
* [Outputting blank values as null or fixed values](https://help.qlik.com/talend/en-US/components/8.0/tmap/outputting-blank-values-as-null-or-fixed-values)
* [Arithmetic operation](https://help.qlik.com/talend/en-US/components/8.0/tmap/arithmetic-operation)
* [Calling a Java class method](https://help.qlik.com/talend/en-US/components/8.0/tmap/calling-java-class-method)
* [Calling a Talend Routine](https://help.qlik.com/talend/en-US/components/8.0/tmap/calling-talend-routine)
* [If/else statement](https://help.qlik.com/talend/en-US/components/8.0/tmap/if-else-statement)
* [Filter expressions](https://help.qlik.com/talend/en-US/components/8.0/tmap/filter-expressions)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-lookup-models -->

# tMap lookup models

To help you select the most adapted model according to your needs, this article details each model.

Three types of lookup loading models are provided suiting various types of business requirement:

* Load once
* Reload at each row
* Reload at each row (cache)

![Options dialog box.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/190513496_lookup_models.png)

When implementing a join (including **Inner Join** and **Left Outer Join**) in a **tMap** between different data sources, there is always only one main flow and one or more lookup flows connected to the **tMap** . All the records of the lookup flow need to be loaded before processing each record of the main flow.

**Description**

**Load once:** before processing each record of the main flow, this option loads once (and only once) all the records from the lookup flow either in the memory or in a local file in case the **Store temp data** option is set to true. This is the default setting for join and the best option if you have a large set of records in the main flow to be processed using a join to the lookup flow.

**Reload at each row:** all the records of the lookup flow are loaded again for each record of the main flow. Generally, this option increases the Job execution time due to the repeated loading of the lookup flow for each main flow record. However, this option should preferred in the following two situations:

1. The lookup data flow is constantly updated and you want to load the newest lookup data for each record of main flow in order to get the new data after the join execution.
2. You have less rows in your main flow and have a large dataset that comes from a database table in the lookup flow. It might cause an *OutOfMemory* exception if you use the Load once option. In this situation, the Reload at each row option will be considered.

The procedure in the following section explains how to use the **Reload at each row** model.

**Reload at each row (cache):** this model functions like the **Reload at each row** model, all the records of the lookup flow are loaded again for each record of the main flow. However, this model can't be used with **Store temp data on disk** option. The lookup data is cached in memory, and when a new loading occurs, only the records that do not already exist in the cache will be loaded in order to avoid loading the same records twice.

**Procedure**

This procedure explains how to use the **Reload at each row** model. To gain in processing performance, it is recommended to use global variables in order to filter the main data flow and only process what needs to be processed.

1. Set the value of one column of the main flow to a global variable (**tSetGlobalVar** component), then use this variable in a WHERE condition in the lookup query in order to only load the matched data from the table based on one or more values of the main flow, rather than loading the entire data.

   ![Variables table.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/190513496_job_design.png)

2. In the **tMap** component, select the **Reload at each row** model for the **Lookup Model** column:

   ![Reload at each row model.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/190513496_tMap_setting.png)

3. Use the global variable you have set in Step 1, in the lookup query to only load the matched data from the table.

   ![Basic settings view.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/190513496_tmysqlInput_settings.png)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-standard-properties -->

# tMap Standard properties

These properties are used to configure tMap running in the Standard Job framework.

The Standard tMap component belongs to the Processing family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Map editor | It allows you to define the tMap<br>routing and transformation properties.<br><br>If needed, click the ![Property Settings button](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/tmap_properties_config_button.png) button at the top of the input area to open the Property Settings dialog box, which provides the<br>following options:<br><br><ul> <li> <p> <span>Die on error</span>: Select this									check box if you want to kill the Job if there is an error. This									check box is selected by default.</p> </li> <li> <p> <span>Lookup in parallel</span>: Select									this check to maximize the data transformation performance in a									Job that handles multiple lookup input flows with large amounts									of data.</p> </li> <li> <p> <span>Enable Auto-Conversion of										types</span>: If your input and output columns across a									mapping are of different data types, select this check box to									enable automatic type conversion at the run time to avoid									compiling errors. </p> <p>This option is enabled by default if the <span>Enable Auto-Conversion of types</span> check box                           is selected in the <span>Project                              Settings</span> view when this component is added. You can also                           override the default conversion behavior of this component by setting                           conversion rules in the <span>Project                              Settings</span> view. For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/defining-rules-to-override-default-conversion-behavior" target="_blank">Defining rules to override the default conversion behavior</a>. </p> <p>Note that auto conversion between Date and BigDecimal is not									supported.</p> </li> <li> <p> <span>Store on disk</span>: The options									provided in this area are identical to the relevant options									provided on the <span>Basic settings</span>									and <span>Advanced settings</span> tabs									respectively. Settings made in the <span>Property Settings</span> dialog box are reflected in									the respective tab views and vice versa.</p> </li> </ul><br><br>This component offers the advantage of the<br>dynamic schema feature. This allows you to retrieve unknown columns from source<br>files or to copy batches of columns from a source without mapping each column<br>individually. For further information about dynamic schemas, see [Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema).<br><br>This<br>dynamic schema feature is designed for the purpose of retrieving unknown columns of a<br>table and is recommended to be used for this purpose only; it is not recommended for the<br>use of creating tables. |
| Mapping links display as | Auto: the default setting is curves<br>links<br><br><br>Curves: the mapping display as curves<br><br><br>Lines: the mapping displays as straight<br>lines. This last option allows to slightly enhance performance. |
| Temp data directory path | Enter the path where you want to store the temporary data<br>generated for lookup loading. For more information on this folder, see [Solving memory limitation issues in tMap use](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/solving-memory-limitation-issues-in-tmap-use). |
| Preview | The preview is an instant shot of the Mapper data. It becomes<br>available when Mapper properties have been filled in with data. The<br>preview synchronization takes effect only after saving changes. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Max buffer size (nb of rows) | Type in the size of physical memory, in number of rows, you<br>want to allocate to processed data. |
| Ignore trailing zeros for BigDecimal | Select this check box to ignore trailing zeros for<br>BigDecimal data. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at the Job<br>level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | Possible uses are from a simple reorganization of fields to the<br>most complex Jobs of data multiplexing or demultiplexing transformation,<br>concatenation, inversion, filtering, and more. |
| Limitation | The use of tMap supposes minimum Java<br>knowledge in order to fully exploit its functionalities.<br><br>This component is a junction step, and for this reason cannot be a<br>start nor end component in the Job. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-properties-for-apache-spark-batch -->

# tMap properties for Apache Spark Batch

These properties are used to configure tMap running in the Spark Batch Job framework.

The Spark Batch tMap component belongs to the Processing family.

The component in this framework is available in all subscription-based Talend products with Big Data and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Map editor | It allows you to define the tMap routing and transformation properties but note<br>that only the Load once lookup<br>model is supported by the Spark Batch Jobs.<br><br>For further information about this Load once lookup model, see the related<br>description of Handling Lookups.<br><br>When you click the Property Settings<br>button at the top of the input area, a Property<br>Settings dialog box is displayed in which you can set the<br>following parameters:<br><br><ul> <li> <p>If you do not want to handle execution errors, select the                <span>Die on error </span>check box                (selected by default). It will kill the Job if there is an                error.</p> </li> <li> <p>To maximize the data transformation performance in a Job that                handles multiple lookup input flows with large amounts of data,                you can select the <span>Lookup in                    parallel</span> check box.</p> </li> <li> <p> <span>Temp data directory path</span>: enter the path where you          want to store the temporary data generated for lookup loading. For more information on          this folder, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/solving-memory-limitation-issues-in-tmap-use" target="_blank">Solving memory limitation issues in tMap use</a>.</p> </li> <li> <p>Max buffer size (nb of rows): enter the size of physical                memory, in number of rows, you want to allocate to processed                data.</p> </li> </ul> |
| Mapping links display as | Auto: the default setting is curves<br>links<br><br><br>Curves: the mapping display as curves<br><br><br>Lines: the mapping displays as straight<br>lines. This last option allows to slightly enhance performance. |
| Preview | The preview is an instant shot of the Mapper data. It becomes<br>available when Mapper properties have been filled in with data. The<br>preview synchronization takes effect only after saving changes. |
| Use replicated join | Select this check box to perform a replicated join between the input<br>flows. By replicating each lookup table into memory, this type of join<br>doesn't require an additional shuffle-and-sort step, thus speeding up<br>the whole process.<br><br>You need to ensure that the entire lookup tables fit in memory. |
| Max buffer size (nb of rows) | Type in the size of physical memory, in number of rows, you<br>want to allocate to processed data. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate step.<br><br>This component, along with the Spark Batch component Palette it belongs to,<br>appears only when you are creating a Spark Batch Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a<br>scenario presents only Standard Jobs, that is to<br>say traditional<br>Talend<br>data integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-properties-for-apache-spark-streaming -->

# tMap properties for Apache Spark Streaming (deprecated)

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

These properties are used to configure tMap running in the Spark Streaming Job framework.

Information noteDeprecation: Spark Streaming is deprecated beginning with the R2026-09 release. Use Spark Structured Streaming instead.

The Spark Streaming tMap component belongs to the Processing family.

This component is available in Talend Real-Time Big Data Platform and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Map editor | It allows you to define the tMap<br>routing and transformation properties.<br><br>When you click the Property Settings<br>button at the top of the input area, a Property<br>Settings dialog box is displayed in which you can set the<br>following parameters:<br><br><ul> <li> <p>If you do not want to handle execution errors, select the                <span>Die on error </span>check box                (selected by default). It will kill the Job if there is an                error.</p> </li> <li> <p>To maximize the data transformation performance in a Job that                handles multiple lookup input flows with large amounts of data,                you can select the <span>Lookup in                    parallel</span> check box.</p> </li> <li> <p> <span>Temp data directory path</span>: enter the path where you          want to store the temporary data generated for lookup loading. For more information on          this folder, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/solving-memory-limitation-issues-in-tmap-use" target="_blank">Solving memory limitation issues in tMap use</a>.</p> </li> <li> <p>Max buffer size (nb of rows): enter the size of physical                memory, in number of rows, you want to allocate to processed                data.</p> </li> </ul> |
| Mapping links display as | Auto: the default setting is curves<br>links<br><br><br>Curves: the mapping display as curves<br><br><br>Lines: the mapping displays as straight<br>lines. This last option allows to slightly enhance performance. |
| Preview | The preview is an instant shot of the Mapper data. It becomes<br>available when Mapper properties have been filled in with data. The<br>preview synchronization takes effect only after saving changes. |
| Use replicated join | Select this check box to perform a replicated join between the input<br>flows. By replicating each lookup table into memory, this type of join<br>doesn't require an additional shuffle-and-sort step, thus speeding up<br>the whole process.<br><br>You need to ensure that the entire lookup tables fit in memory. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | It usually works with a Lookup Input component such as tMongoDBLookupInput to construct and consume a lookup flow. In this situation,<br>you must use Reload at each row or Reload at each row (cache) to read data from the lookup flow. This approach ensures that no redundant records are stored in memory before being sent to tMap. For a use case in which tMap<br>is used with a Lookup Input component, see [Reading and writing data in MongoDB using a Spark Streaming Job](https://help.qlik.com/talend/en-US/components/8.0/mongodb/tmongodblookupinput-tmongodbconfiguration-ts3configuration-reading-and-writing-data-in-mongodb-using-spark-streaming-job-spark-stream-component-in-this). Note that Reload at each row or Reload at each row (cache) in a streaming Job is supported by the Lookup Input components<br>only. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-properties-for-apache-spark-structured-streaming -->

# tMap properties for Apache Spark Structured Streaming

[Preview](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/feature-preview-program-overview.htm)

Use these properties to configure tMap running in the Spark Structured Streaming Job framework.

The Spark Structured Streaming tMap component belongs to the Processing family.

This component is available in Talend Real-Time Big Data Platform and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Map editor | Use the map editor to define the tMap<br>routing and transformation properties.<br><br>When you click the Property Settings<br>button at the top of the input area, a Property<br>Settings dialog box is displayed in which you can set the<br>following parameters:<br><br><ul> <li> <p>If you do not want to handle execution errors, select the                <span>Die on error </span>check box                (selected by default). It will kill the Job if there is an                error.</p> </li> <li> <p>To maximize the data transformation performance in a Job that                handles multiple lookup input flows with large amounts of data,                you can select the <span>Lookup in                    parallel</span> check box.</p> </li> <li> <p> <span>Temp data directory path</span>: enter the path where you          want to store the temporary data generated for lookup loading. For more information on          this folder, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/solving-memory-limitation-issues-in-tmap-use" target="_blank">Solving memory limitation issues in tMap use</a>.</p> </li> <li> <p>Max buffer size (nb of rows): enter the size of physical                memory, in number of rows, you want to allocate to processed                data.</p> </li> </ul> |
| Mapping links display as | Select how mapping links are displayed:<br><br><ul> <li><span>Auto</span>: the default setting displays                        links as curves.</li> <li><span>Curves</span>: the mapping displays as                        curves.</li> <li><span>Lines</span>: the mapping displays as                        straight lines. The Lines option can slightly improve performance.</li> </ul> |
| Use replicated join (when all lookup tables can fit in memory) | Select this check box to perform a replicated join between the input flows.<br>By replicating each lookup table into memory, this type of join does not require an<br>additional shuffle-and-sort step, thus speeding up the whole process.<br><br>Ensure that all lookup tables fit in memory. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate step.<br><br>This component, along with the Spark Structured Streaming component Palette it belongs to,<br>appears only when you are creating a Spark Structured Streaming Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a scenario presents<br>only Standard Jobs, that is to say traditional<br>Talend<br>data<br>integration Jobs. |
| Spark Connection | You need to use the Structured Streaming Configuration<br>tab in the Run view to define the connection to a Spark cluster for<br>the whole Job.<br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-linking-components-standard-component-drop -->

# Linking the components

## Procedure

1. Place two tFileInputDelimited components, tMap and three tFileOutputDelimited components onto the design workspace.
2. Rename the two tFileInputDelimited components as *Cars* and *Owners*, either by double-clicking the label in the design workspace or using the View tab of the Component view.
3. Connect the two input components to tMap using Row &gt; Main connections and label the connections as *Cars\_data* and *Owners\_data* respectively.
4. Connect tMap to the three output components using Row &gt; New Output (Main) connections and name the output connections as *Insured*, *Reject\_NoInsur* and *Reject\_OwnerID* respectively.

   ![Component connections.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap2-1-1.png)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-configuring-how-to-map-data-standard-component -->

# Configuring how to map the data

## Procedure

1. Double-click the tFileInputDelimited component labeled *Cars* to display its Basic settings view.

   ![Basic settings view for tFileInputDelimited.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap2-1-2.png)
2. Select Repository from the Property type list and select the component's schema, *cars* in this scenario, from the Repository Content dialog box. The rest fields are automatically filled.
3. Double-click the component labeled *Owners* and repeat the setting operation. Select the appropriate metadata entry, *owners* in this scenario.

   Information noteNote:

   In this scenario, the input schemas are stored in the Metadata node of the Repository tree view for easy retrieval. For further information regarding metadata creation in the Repository, see [Managing metadata in Talend Studio](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/managing-metadata-in-studio).
4. Double-click the tMap component to open the Map Editor.

   Note that the input area is already filled with the defined input tables and that the top table is the main input table, and the respective row connection labels are displayed on the top bar of the table.
5. Create a join between the two tables on the *ID\_Owner* column by simply dropping the *ID\_Owner* column from the *Cars\_data* table onto the *ID\_Owner* column in the *Owners\_data* table.
6. Define this join as an inner join by clicking the tMap settings button, clicking in the Value field for Join Model, clicking the small button that appears in the field, and selecting Inner Join from the Options dialog box.

   ![Inner join.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap2-1-3.png)
7. Drag all the columns of the *Cars\_data* table to the *Insured* table.
8. Drag the *ID\_Owner*, *Registration*, and *ID\_Reseller* columns of the *Cars\_data* table and the *Name* column of the *Owners\_data* table to the *Reject\_NoInsur* table.
9. Drag all the columns of the *Cars\_data* table to the *Reject\_OwnerID* table.

   For more information regarding data mapping, see [Mapping data flows](https://help.qlik.com/talend/r/Lfrx8uSM~Ud8zWd9BsWB5g/Z~DS5lkZdvVq6IJPXFZeZA).
10. Click the plus arrow button at the top of the *Insured* table to add a filter row.

    Drag the *ID\_Insurance* column of the *Owners\_data* table to the filter condition area and enter the formula meaning 'not undefined': Owners\_data.ID\_Insurance != null.

    With this filter, the *Insured* table will gather all the records that include an insurance ID.

    ![Insured table.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap2-1-4.png)
11. Click the tMap settings button at the top of the *Reject\_NoInsur* table and set Catch output reject to true to define the table as a standard reject output flow to gather the records that do not include an insurance ID.

    ![Reject_NoInsur table.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tmap2-1-5halftop.png)
12. Click the tMap settings button at the top of the *Reject\_OwnerID* table and set Catch lookup inner join reject to true so that this output table will gather the records from the *Cars\_data* flow with missing or unmatched owner IDs.

    ![Reject_OwnerID table.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tmap2-1-5halfbot.png)

    Click OK to validate the mappings and close the Map Editor.
13. Double-click each of the output components, one after the other, to define their properties.

    If you want a new file to be created, browse to the destination output folder, and type in a file name including the extension.

    ![Basic settings view.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tMap2-1-6.png)

    Select the Include header check box to reuse the column labels from the schema as header row in the output file.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-executing-job-simple-join-press -->

# Executing the Job

## Procedure

1. Press Ctrl+S to save your Job.
2. Press F6 to run the Job.

   The output files are created, which contain the relevant data as defined.

   ![Job results: Output files creation.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap2-1-7.png)

   For examples of how to use dynamic schemas with tMap, see:
   * [Writing dynamic columns from a database to an output file](https://help.qlik.com/talend/en-US/components/8.0/dynamic-schema/tmysqlinput-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-writing-dynamic-columns-from-database-to-output-file-standard-component-enterprise-in-this).

   * [Writing dynamic columns from a source file to a database](https://help.qlik.com/talend/en-US/components/8.0/mysql/writing-dynamic-columns-from-source-file-to-database).


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-mapping-data-using-inner-join-rejections-standard-component-this -->

# Mapping data using inner join rejections

This scenario, based on scenario 1, adds one input file containing details about resellers and extra fields in the main output table. Two filters on inner joins are added to gather specific rejections.

## Linking the components

### Procedure

1. Place a tFileInputDelimited component and a tFileOutputDelimited component to the design workspace, and label the components as Resellers and No\_Reseller\_ID respectively.
2. Connect it to the Mapper using a Row &gt; Main connection, and label the connection as Resellers\_data.
3. Connect the tMap component to the new tFileOutputDelimited component by using the Row connection named Reject\_ResellerID.

   ![Components connection.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap2-2-2.png)

## Configuring the inner join

### Procedure

1. Double-click the Resellers component to display its Basic settings view.

   ![Basic settings view.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap2-2-1.png)
2. Select Repository from the Property type list and select the component's schema, Resellers in this scenario, from the Repository Content dialog box. The rest fields are automatically filled.

   Information noteNote:

   In this scenario, the input schemas are stored in the Metadata node of the Repository tree view for easy retrieval. For further information regarding metadata creation in the Repository, see [Managing metadata in Talend Studio](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/managing-metadata-in-studio).
3. Double-click the tMap component to open the Map Editor.

   The schema of the new input component is already added in the Input area.
4. Create a join between the main input flow and the new input flow by dropping the ID\_Reseller column of the Cars\_data table to the ID\_Reseller column of the Resellers\_data table.
5. Click the tMap settings button at the top of the Resellers\_data table and set Join Model to Inner Join.

   ![Inner join.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap2-2-3.png)
6. Drag all the columns except ID\_Reseller of the Resellers\_data table to the main output table Insured.

   ![Insured table.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap2-2-4.png)

   Information noteNote:

   When two inner joins are defined, you either need to define two different inner join reject tables to differentiate the two rejections or, if there is only one inner join reject output, both inner join rejections will be stored in the same output.
7. Click the [+] button at the top of the output area to add a new output table, and name this new output table Reject\_ResellerID.
8. Drag all the columns of the Cars\_data table to the Reject\_ResellerID table.
9. Click the tMap settings button and select Catch lookup inner join reject to true to define this new output table as an inner join reject output.

   If the defined inner join cannot be established, the information about the relevant cars will be gathered through this output flow.

   ![Catch lookup inner join reject property.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap2-2-5.png)
10. Apply filters on the two Inner Join reject outputs in order for to distinguish the two types of rejection.

    In the first Inner Join output table, Reject\_OwnerID, click the plus arrow button to add a filter line and fill it with the following formula to gather only owner ID related rejection: Owners\_data.ID\_Owner==null
11. In the second Inner Join output table, Reject\_ResellerID, repeat the same operation using the following formula: Resellers\_data.ID\_Reseller==null

    ![Reject_ResellerID table.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap2-2-6.png)

    Click OK to validate the map settings and close the Mapper Editor.
12. Double-click the No\_Reseller\_ID component to display its Basic settings view.

    ![Basic settings view.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap2-2-7.png)

    Specify the output file path and select the Include Header check box, and leave the other parameters as they are.
13. To demonstrate the work of the Mapper, in this example, remove reseller IDs 5 and 8 from the input file Resellers.csv.

## Executing the Job

### Procedure

1. Press Ctrl+S to save your Job.
2. Press F6 to run the Job.

### Results

The four output files are all created in the specified folder, containing information as defined. The output file No\_Reseller\_ID.csv contains the *cars* information related to reseller IDs 5 and 8, which are missing in the input file Resellers.csv.

![Output files creation.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap2-2-8.png)

For examples of how to use dynamic schemas with tMap, see:

* [Writing dynamic columns from a database to an output file](https://help.qlik.com/talend/en-US/components/8.0/dynamic-schema/tmysqlinput-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-writing-dynamic-columns-from-database-to-output-file-standard-component-enterprise-in-this).

* [Writing dynamic columns from a source file to a database](https://help.qlik.com/talend/en-US/components/8.0/mysql/writing-dynamic-columns-from-source-file-to-database).

As third advanced use scenario, based on the scenario 2, add a new Input table containing Insurance details for example.

Set up an Inner Join between two lookup input tables (Owners and Insurance) in the Mapper to create a cascade lookup and hence retrieve Insurance details using the Owners table data.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-advanced-mapping-using-filters-explicit-joins-and-rejections-standard-component-this -->

# Advanced mapping using filters, explicit joins and rejections

This scenario introduces a Job that allows you to find BMW owners who have two to six children (inclusive), for sales promotion purpose for example.

## Linking the components

### Procedure

1. Place three tFileInputDelimited components, a tMap component, and two tFileOutputDelimited components from the Palette onto the design workspace, and label them to best describe their functions.
2. Connect the input components to the tMap using Row &gt; Main connections.

   Pay attention to the file you connect first as it will automatically be set as Main flow, and all the other connections will be Lookup flows. In this example, the connection for the input component Owners is the Main flow.

   ![Components connection.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap4-1.png)

## Configuring the components

### Procedure

1. Define the properties of each input components in the respective Basic settings view. Define the properties of Owners.

   ![Basic settings view.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap4-2.png)
2. Select Repository from the Property type list and select the component's schema, *owners* in this scenario, from the Repository Content dialog box. The rest fields are automatically filled.

   Information noteNote:

   In this scenario, the input schemas are stored in the Metadata node of the Repository tree view for easy retrieval. For further information regarding metadata creation in the Repository, see [Managing metadata in Talend Studio](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/managing-metadata-in-studio).

   In the same way, set the properties of the other input components: Cars and Resellers. These two Lookup flows will fill in secondary (lookup) tables in the input area of the Map Editor.
3. Double-click the tMap component to launch the Map Editor and define the mappings and filters.

   Set an explicit join between the Main flow Owner and the Lookup flow Cars by dropping the ID\_Owner column of the Owners table to the ID\_Owner column of the Cars table.

   The explicit join is displayed along with a hash key.

   ![ID_Owner column.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tmap4-3cut2.png)
4. In the Expr. Key field of the Make column, type in a filter. In this use case, simply type in "BMW" as the search is focused on the owners of this particular make.

   ![Make column.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tmap4-3cut3top.png)
5. Implement a cascading join between the two lookup tables Cars and Resellers on the ID\_Reseller column in order to retrieve resellers information.
6. As you want to reject the null values into a separate table and exclude them from the standard output, click the tMap settings button and set Join Model to Inner Join in each of the Lookup tables.

   ![Lookup table.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tmap4-3cut3.png)
7. In the tMap settings, you can set Match Model to Unique match, First match, or All matches. In this use case, the All matches option is selected. Thus if several matches are found in the Inner Join, rows matching the explicit join as well as the filter, all of them will be added to the output flow (either in rejection or the regular output).

   Information noteNote:

   The Unique match option functions as a Last match. The First match and All matches options function as named.
8. On the output area of the Map Editor, click the plus button to add two tables, one for the full matches and the other for the rejections.
9. Drag all the columns of the Owners table, the Registration, Make and Color columns of the Cars table, and the ID\_Reseller and Name\_Reseller columns of the Resellers table to the main output table.
10. Drag all the columns of the Owners table to the reject output table.
11. Click the Filter button at the top of the main output table to display the Filter expression area.

    Type in a filter statement to narrow down the number of rows loaded in the main output flow. In this use case, the statement reads: Owners.Children\_Nr &gt;= 2 && Owners.Children\_Nr &lt;= 6.
12. In the reject output table, click the tMap settings button and set the reject types.

    Set Catch output reject to true to collect data about BMW car owners who have less than two or more than six children.

    Set Catch lookup inner join reject to true to collect data about owners of other car makes and owners for whom the reseller information is not found.

    ![Rejects table.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap4-3.png)

    Click OK to validate the mappings and close the Map Editor.

    On the design workspace, right-click the tMap and pull the respective output link to the relevant output components.
13. Define the properties of the output components in their respective Basic settings view.

    In this use case, simple specify the output file paths and select the Include Header check box, and leave the other parameters as they are.

    ![Basic settings view.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap4-4.png)

## Executing the Job

### Procedure

1. Press Ctrl+S to save your Job.
2. Press F6 to run it.

   The main output file contains the information related to BMW owners who have two to six children, and the reject output file contains the information about the rest of the car owners.

   ![Output file creation.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap4-5.png)

   For examples of how to use dynamic schemas with tMap, see:
   * [Writing dynamic columns from a database to an output file](https://help.qlik.com/talend/en-US/components/8.0/dynamic-schema/tmysqlinput-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-writing-dynamic-columns-from-database-to-output-file-standard-component-enterprise-in-this).

   * [Writing dynamic columns from a source file to a database](https://help.qlik.com/talend/en-US/components/8.0/mysql/writing-dynamic-columns-from-source-file-to-database).


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-advanced-mapping-with-filters-and-different-rejections-standard-component-this -->

# Advanced mapping with filters and different rejections

This scenario is a modified version of the preceding scenario. It describes a Job that applies filters to limit the search to BMW and Mercedes owners who have two to six children and divides unmatched data into different reject output flows.

## Linking the components

### Procedure

1. Take the same Job as in [Advanced mapping using filters, explicit joins and rejections](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-advanced-mapping-using-filters-explicit-joins-and-rejections-standard-component-this).
2. Place a new tFileOutputDelimited component from the Palette on the design workspace, and name it Rejects\_BMW\_Mercedes to reflect its function.
3. Connect the tMap component to the new output component using a Row connection and label the connection according to the output component function.

   This connection label will appear as the name of the new output table in the Map Editor.
4. Relabel the existing output connections and output components to reflect their function.

   The existing output tables in the Map Editor will be automatically renamed according to the connection labels. In this example, relabel the existing output connections BMW\_Mercedes\_withChildren and Owners\_Other\_Makes respectively.

   ![Components connection.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap5-1.png)

## Configuring the components

### Procedure

1. Double-click the tMap component to launch the Map Editor to change the mappings and the filters.

   The output area contains a new, empty output table named Rejects\_BMW\_Mercedes. You can adjust the position of the table by selecting it and clicking the Up or Down arrow button at the top of the output area.
2. Remove the Expr. key filter ("BMW") from the Cars table in the input area.
3. Click the Filters button to display the Filter field, and type in a new filter to limit the search to BMW or Mercedes car makes. The statement reads as follows: Cars.Make.equals("BMW") || Cars.Make.equals("Mercedes")

   ![Filter field.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tmap5-2cut2.png)
4. Select all the columns of the main output table and drop them down to the new output table.

   Alternatively, you can also drag the corresponding columns from the relevant input tables to the new output table.
5. Click the tMap settings button at the top of the new output table and set Catch output reject to true to collect data about BMW and Mercedes owners who have less than two or more than six children.
6. In the Owners\_Other\_Makes table, set Catch lookup inner join reject to true to collect data about owners of other car makes and owners for whom the reseller information is not found.

   ![Owners_Other_Makes table.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap5-2.png)
7. Click OK to validate the mappings and close the Map Editor.
8. Define the properties of the output components in their respective Basic settings view.

   In this use case, simple specify the output file paths and select the Include Header check box, and leave the other parameters as they are.

   ![Basic settings view.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap5-3.png)

## Executing the Job

### Procedure

1. Press Ctrl+S to save the Job.
2. Press F6 to run it.

   The output files contain content of the main output flow shows that the filtered rows have correctly been passed on.

   ![Output files creation.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tmap5-4.png)

   For examples of how to use dynamic schemas with tMap, see:
   * [Writing dynamic columns from a database to an output file](https://help.qlik.com/talend/en-US/components/8.0/dynamic-schema/tmysqlinput-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-writing-dynamic-columns-from-database-to-output-file-standard-component-enterprise-in-this).

   * [Writing dynamic columns from a source file to a database](https://help.qlik.com/talend/en-US/components/8.0/mysql/writing-dynamic-columns-from-source-file-to-database).
