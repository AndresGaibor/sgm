# teltverticamap

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/teltverticamap  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/teltverticamap -->

# tELTVerticaMap

Builds the SQL SELECT statement using the table schema(s) provided by one or more tELTVerticaInput components.

The three ELT Vertica components are closely related, in terms of their operating conditions. These components should be used to handle Vertica database table schemas to generate SQL statements, including clauses, which are to be executed in the database output table defined.

## tELTVerticaMap Standard properties

These properties are used to configure tELTVerticaMap running in the Standard Job framework.

The Standard tELTVerticaMap component belongs to the ELT family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| DB Version | Select the version of the Vertica database<br>being used. |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| ELT Vertica Map Editor | The ELT Map editor allows you to define<br>the output schema as well as build graphically the SQL statement to be<br>executed. The column names of the schema can be different from the<br>column names in the database.<br><br>You can filter schema columns in an input or output table<br>by clicking the Enable/disable column name filter button in the<br>corresponding table and entering the search keyword in the field displayed.<br><br>You can click ![](https://help.qlik.com/talend/en-US/components/Resources/images/button-elt-map-setup-configuration.png) on the upper left<br>corner and in the Property Settings dialog box displayed, select the<br>Add quotes in columns when generating query check box to add<br>quotes for the column names in the generated SQL query. This check box is displayed as<br>Delimited identifiers if you have not installed the 8.0 R2022-11<br>Talend Studio<br>monthly update or a later one provided by Talend. |
| Style link | Select a way in which links are<br>displayed.<br><br><ul> <li> <p> <span>Auto</span>: By default, the links                                    between the input and output schemas and the Web service                                    parameters are in the form of curves. </p> </li> <li> <p> <span>Bezier curve</span>: The links between                                    the schema and the Web service parameters are in the form of                                    curve. </p> </li> <li> <p> <span>Line (fastest)</span>: The links                                    between the schema and the Web service parameters are in the                                    form of straight lines. </p> <p> This option slightly optimizes                                    performance.</p> </li> </ul> |
| Property Type | <ul> <li> <p>Either <span>Built-In</span> or <span>Repository</span>.</p> </li> <li> <p> <span>Built-In</span>: No property data stored                            centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file                            in which the properties are stored. The database connection fields that                            follow are completed automatically using the data retrieved.</p> </li> </ul> |
| Host | Type in the IP address or hostname of the<br>database. |
| Port | Type in the listening port number of the<br>database. |
| Database | Type in the name of the database you want<br>to use. |
| Additional JDBC Parameters | Specify additional connection properties<br>for the database connection you are creating. |
| Username and Password | Type in the database user authentication<br>data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to gather the Job<br>processing metadata at the Job level as well as at each component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | tELTVerticaMap is used along with<br>tELTVerticaInput and tELTVerticaOutput. Note that the Output<br>link to be used with these components must correspond strictly to the<br>syntax of the table name.<br><br>Information noteNote:<br><br>The ELT components do not handle<br>actual data flow but only schema information. |
