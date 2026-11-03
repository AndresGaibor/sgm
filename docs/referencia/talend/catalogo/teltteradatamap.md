# teltteradatamap

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/teltteradatamap  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/teltteradatamap -->

# tELTTeradataMap

Builds the SQL SELECT statement using the table schema(s) provided by one or more tELTTeradataInput components.

The three ELT Teradata components are closely related, in terms of their operating conditions. These components should be used to handle Teradata database table schemas to generate SQL statements, including clauses, which are to be executed in the database output table defined.

## tELTTeradataMap Standard properties

These properties are used to configure tELTTeradataMap running in the Standard Job framework.

The Standard tELTTeradataMap component belongs to the ELT family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| ELT Teradata Map editor | The ELT Map editor allows you to define<br>the output schema as well as build graphically the SQL statement to be<br>executed. The column names of schema can be different from the column<br>names in the database.<br><br>These operators are used: =, &lt;=,<br>&lt;, &gt;=, &gt;, and<br>&lt;&gt;; the corresponding previous operators, including<br>EQ, LE, LT,<br>GE, GT, and NE, are<br>deprecated.<br><br>On the upper left corner of the ELT Map editor, you can click the<br>Setup the configurations of elt map button to open a<br>dialog box Property Settings which contains two<br>options:<br><br><ul> <li> <span>Add quotes in columns when generating query</span>: With                        this check box selected, double quotes will be added for all output column                        names to support delimited identifiers. By default, this check box is                           cleared.<p>This check box is displayed as <span>Delimited                              identifiers</span> if you have not installed the 8.0 R2022-11                              <span>Talend Studio</span> monthly update or a later one provided by <span>Talend</span>.</p> </li> <li> <span>Use alias in output                                    table</span>: With this check box selected, aliases will be                                used for all output columns in the SQL query. By default, this check                                box is cleared.</li> </ul><br><br>You can filter schema columns in an input or output table<br>by clicking the Enable/disable column name filter button in the<br>corresponding table and entering the search keyword in the field displayed. |
| Style link | Select the way in which links are displayed.<br><br><br>Auto: By default, the links between the input and output schemas and the Web service parameters are in the form of curves.<br><br><br>Bezier curve: Links between the schema and the Web service parameters are in the form of curve.<br><br><br>Line: Links between the schema and the Web service parameters are in the form of straight lines.<br><br>This option slightly optimizes performance. |
| Property type | <ul> <li> <p>Either Built-in or Repository. </p> </li> <li> <p> <span>Built-in</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the Repository file where Properties are stored. The following fields are pre-filled in using fetched data.</p> </li> </ul> |
| Host | Database server IP address |
| Database | Name of the database |
| Username and Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Query band | Select this check box to use the Teradata Query Banding feature to add metadata to the query<br>to be processed, such as the user running the query. This can help you, for example,<br>identify the origin of this query.<br><br>Once selecting the check box, the Query Band parameters<br>table is displayed, in which you need to enter the metadata information to be added. This<br>information takes the form of key/value pairs, for example, *DpID* in the Key column and *Finance* in the Value<br>column.<br><br>This check box actually generates the SET QUERY\_BAND FOR SESSION statement with the key/value<br>pairs declared in the Query Band parameters table. For<br>further information about this statement, see the [Teradata documentation](https://docs.teradata.com/search/all?query=End+logging+syntax).<br><br>This check box is not available when you have selected the Using an<br>existing connection check box. In this situation, if you need to use the<br>Query Band feature, set it in the Advanced settings tab of<br>the Teradata connection component to be used. |
| tStatCatcher Statistics | Select this check box to collect log data at the component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | tELTTeradataMap is used along with a tELTTeradataInput and tELTTeradataOutput. Note that the Output link to be used with these components must faithfully reflect the name of the tables.<br><br>Information noteNote:<br><br>The ELT components do not handle actual data flow but only schema information. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |

**Related concepts**

* [Mapping data using a subquery](https://help.qlik.com/talend/en-US/components/8.0/teltteradatainput-teltteradatamap-teltteradataoutput-mapping-data-using-subquery-standard-component "The sample Job described in this scenario maps the data from two input tables, PreferredSubject and CourseScore, to the output table, TotalScoreOfPreferredSubject, using a subquery.")
