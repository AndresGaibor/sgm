# teltmap

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/teltmap  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/teltmap -->

# tELTMap

Uses the tables provided as input to feed the parameter in the built SQL statement. The statement can include inner or outer joins to be implemented between tables or between one table and its aliases.

Information noteWarning: The query order of the built SQL statement is generated the same way as it appears in the GUI, so having the LEFT JOIN clauses prior to the INNER JOIN clauses could result in data loss. However, Talend has no plan to change this behavior from the GUI at this time, as some databases like [PostgreSQL](https://www.postgresql.org/docs/12/explicit-joins.html) consider the query order when generating the execution plan and the order part is necessary for query runtime optimization.

The three ELT components are closely related, in terms of their operating conditions. These components should be used to handle DB schemas to generate Insert statements, including clauses, which are to be executed in the DB output table defined.

## tELTMap Standard properties

These properties are used to configure tELTMap running in the Standard Job framework.

The Standard tELTMap component belongs to the ELT family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| ELT Map Editor | The ELT Map editor allows you to define<br>the output schema and make a graphical build of the SQL statement to be<br>executed. The column names of schema can be different from the column<br>names in the database.<br><br>You can enter a multi-line expression for an output column and access<br>proposals including input columns, output columns, and context variables by<br>pressing Ctrl+Space in a pop-up Expression Builder<br>dialog box.<br><br>You can filter schema columns in an input or output table<br>by clicking the Enable/disable column name filter button in the<br>corresponding table and entering the search keyword in the field displayed.<br><br>You can click ![](https://help.qlik.com/talend/en-US/components/Resources/images/button-elt-map-setup-configuration.png) on the upper<br>left corner of the ELT Map Editor and in the Property<br>Settings dialog box displayed:<br><br>You can click ![](https://help.qlik.com/talend/en-US/components/Resources/images/button-elt-map-setup-configuration.png) on the upper<br>left corner of the ELT Map Editor and in the Property<br>SettingsProperty<br>Settings dialog box displayed:<br><br><ul> <li>Select the <span>Add quotes in columns when generating query</span> check               box to add quotes for the column names in the generated SQL query.<p>This check box                  is displayed as <span>Delimited identifiers</span> if you have not                  installed the 8.0 R2022-11 <span>Talend Studio</span>                  monthly update or a later one provided by <span>Talend</span>.</p> </li> <li>Select the <span>Add quotes in table names when generating query</span>               check box to add quotes for the table and schema names in the generated SQL                  query.<p>This check box is available only if you have installed the 8.0 R2022-11                     <span>Talend Studio</span>                  monthly update or a later one provided by <span>Talend</span>.</p> </li> </ul><br><br>Select the Add quotes in columns when generating query check<br>box to add quotes for the column names in the generated SQL query.<br><br>This check box<br>is displayed as Delimited identifiers if you have not<br>installed the 8.0 R2022-11 Talend Studio<br>monthly update or a later one provided by Talend.<br><br>Select the Add quotes in columns when generating queryAdd quotes in columns when generating query check<br>box to add quotes for the column names in the generated SQL query.<br><br>This check box<br>is displayed as Delimited identifiers if you have not<br>installed the 8.0 R2022-11 Talend Studio<br>monthly update or a later one provided by Talend.<br><br>This check box<br>is displayed as Delimited identifiersDelimited identifiers if you have not<br>installed the 8.0 R2022-11 Talend StudioTalend Studio<br>monthly update or a later one provided by TalendTalend.<br><br>Select the Add quotes in table names when generating query<br>check box to add quotes for the table and schema names in the generated SQL<br>query.<br><br>This check box is available only if you have installed the 8.0 R2022-11<br>Talend Studio<br>monthly update or a later one provided by Talend.<br><br>Select the Add quotes in table names when generating queryAdd quotes in table names when generating query<br>check box to add quotes for the table and schema names in the generated SQL<br>query.<br><br>This check box is available only if you have installed the 8.0 R2022-11<br>Talend Studio<br>monthly update or a later one provided by Talend.<br><br>This check box is available only if you have installed the 8.0 R2022-11<br>Talend StudioTalend Studio<br>monthly update or a later one provided by TalendTalend. |
| Style link | Select the way in which links are displayed.<br><br><br>Auto: By default, the links between the input and output schemas and the Web service parameters are in the form of curves.<br><br><br>Bezier curve: Links between the schema and the Web service parameters are in the form of curve.<br><br><br>Line: Links between the schema and the Web service parameters are in the form of straight lines.<br><br>This option slightly optimizes performance. |
| Property Type | Either Built-In or Repository.<br><br><ul> <li> <p> <span>Built-In</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the            properties are stored.</p> </li> </ul> |
| JDBC URL | The JDBC URL of the database to be used. For example, the JDBC URL for the Amazon Redshift database is jdbc:redshift://endpoint:port/database. |
| Driver JAR | Complete this table to load the driver JARs needed. To do<br>this, click the [+] button under the table to add<br>as many rows as needed, each row for a driver JAR, then select the cell and click the<br>[...] button at the right side of the cell to<br>open the Module dialog box from which you can select the driver JAR<br>to be used. For example, the driver jar RedshiftJDBC41-1.1.13.1013.jar for the Redshift database. |
| Class name | Enter the class name for the specified driver between double<br>quotation marks. For example, for the RedshiftJDBC41-1.1.13.1013.jar driver, the name to be entered is<br>com.amazon.redshift.jdbc41.Driver. |
| Username and Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Mapping | Specify the metadata mapping file<br>for the database to be used. The metadata mapping file is used for the data<br>type conversion between database and Java. For more information about the<br>metadata mapping, see the related documentation for Type mapping.<br><br>Information noteNote: You can use Hive mapping to support Databricks Delta<br>Lake. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Dry run | Select this option to populate the QUERY variable of the ELTOutput component connected to the<br>component while not connecting to the database or executing queries.<br><br>Information noteNote: This option is available only when you have installed the R2022-01 Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Additional JDBC parameters | Specify additional connection properties for the DB connection you are creating. This option is not available if you have selected the Use an existing connection check box in the Basic settings. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | tELTMap is used along with tELTInput and tELTOutput. Note that the Output link to be used with these components must correspond strictly to the syntax of the table name.<br><br>Information noteNote: ELT components do not handle actual data flow but only<br>schema information. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |

**Related concepts**

* [Aggregating Snowflake data using ELT components](https://help.qlik.com/talend/en-US/components/8.0/teltinput-teltmap-tsnowflakeinput-tlogrow-aggregating-snowflake-data-using-context-variables-as-table-and-connection-names "This scenario shows you an example of aggregating Snowflake data from two source tables STUDENT and TEACHER to one target table FULLINFO using the ELT components.")
