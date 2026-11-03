# teltoraclemap

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/teltoraclemap  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/teltoraclemap -->

# tELTOracleMap

Builds the SQL SELECT statement using the table schema(s) provided by one or more tELTOracleInput components.

The three ELT Oracle components are closely related, in terms of their operating conditions. These components should be used to handle Oracle database table schemas to generate SQL statements, including clauses, which are to be executed in the database output table defined.

## tELTOracleMap Standard properties

These properties are used to configure tELTOracleMap running in the Standard Job framework.

The Standard tELTOracleMap component belongs to the ELT family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Note that connections that are of<br>WALLET type are for the tCreateTable component, the tOracleInput<br>component, and the tOracleOutput component only. Make sure that the connection selected is<br>not of the WALLET type to prevent possible errors.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| ELT Oracle Map Editor | The ELT Map editor allows you to define<br>the output schema and make a graphical build of the SQL statement to be<br>executed. The column names of schema can be different from the column<br>names in the database.<br><br>On the upper left corner of the ELT Map editor, you can click the<br>Setup the configurations of elt map button to open a<br>dialog box Property Settings which contains two<br>options:<br><br><ul> <li> <span>Add quotes in columns when generating query</span>: With                        this check box selected, double quotes will be added for all output column                        names to support delimited identifiers. By default, this check box is                           cleared.<p>This check box is displayed as <span>Delimited                              identifiers</span> if you have not installed the 8.0 R2022-11                              <span>Talend Studio</span> monthly update or a later one provided by <span>Talend</span>.</p> </li> <li> <span>Automatic                                    alias</span>: With this check box selected, if a schema                                column has a different name than its database column, an alias will                                be automatically created in the SQL query for that column. By                                default, this check box is selected.</li> </ul><br><br>You can filter schema columns in an input or output table<br>by clicking the Enable/disable column name filter button in the<br>corresponding table and entering the search keyword in the field displayed. |
| Style link | Auto: By default, the links between the input and output schemas and the Web service parameters are in the form of curves.<br><br><br>Bezier curve: Links between the schema and the Web service parameters are in the form of curve.<br><br><br>Line: Links between the schema and the Web service parameters are in the form of straight lines.<br><br>This option slightly optimizes performance. |
| Property type | <ul> <li> <p>Either Built-in or Repository. </p> </li> <li> <p> <span>Built-in</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the Repository file where Properties are stored. The following fields are pre-filled in using fetched data.</p> </li> </ul> |
| Connection type | Drop-down list of the available drivers. |
| DB Version | Select the Oracle version you are using. |
| Host | Database server IP address |
| Port | Listening port number of DB server. |
| Database | Name of the database |
| Username and Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Mapping | Automatically set mapping parameter. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Dry run | Select this option to populate the QUERY variable of the ELTOutput component connected to the<br>component while not connecting to the database or executing queries.<br><br>Information noteNote: This option is available only when you have installed the R2022-01 Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Additional JDBC Parameters | Specify additional connection properties for the DB connection you are creating. This option is not available if you have selected the Use an existing connection check box in the Basic settings. |
| Use Hint Options | Select this check box to activate the hint configuration area to help you optimize a query's execution. In this area, parameters are:<br><br>- HINT: specify the hint you need, using the syntax /\*+ \*/. - POSITION: specify where you put the hint in a SQL statement.<br><br>- SQL STMT: select the SQL statement you need to use. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | tELTOracleMap is used along with a tELTOracleInput and tELTOracleOutput. Note that the Output link to be used with these components must correspond strictly to the syntax of the table name.<br><br>Information noteNote:<br><br>Note that the ELT components do not handle actual data flow but only schema information. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |

**Related concepts**

* [Updating Oracle database entries](https://help.qlik.com/talend/en-US/components/8.0/teltoracleoutput-teltoraclemap-teltoracleinput-updating-oracle-database-entries-standard-component-this)
* [Managing data using the Oracle MERGE function](https://help.qlik.com/talend/en-US/components/8.0/teltoraclemap-teltoracleinput-teltoracleoutput-managing-data-using-oracle-merge-function-standard-component-the)
