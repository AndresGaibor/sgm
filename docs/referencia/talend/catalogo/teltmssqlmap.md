# teltmssqlmap

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/teltmssqlmap  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/teltmssqlmap -->

# tELTMSSqlMap

Uses the tables provided as input to feed the parameter in the built statement. The statement can include inner or outer joins to be implemented between tables or between one table and its aliases.

The three ELT MSSql components are closely related, in terms of their operating conditions. These components should be used to handle MSSql DB schemas to generate Insert statements, including clauses, which are to be executed in the DB output table defined.

Helps you to build the SQL statement graphically, using the table provided as input.

## tELTMSSqlMap Standard properties

These properties are used to configure tELTMSSqlMap running in the Standard Job framework.

The Standard tELTMSSqlMap component belongs to the ELT family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| JDBC Provider | Select the provider of the JDBC driver to be used, either Microsoft (the default, recommended) or Open<br>source JTDS.<br><br>When Microsoft is selected, you need to download the<br>Microsoft JDBC Driver for SQL Server on [Microsoft Download<br>Center](https://www.microsoft.com/en-us/download/details.aspx?id=11774), unpack the downloaded zip file, choose a jar in the<br>unzipped folder based on your JRE version, rename the jar to *mssql-jdbc.jar* and install it manually. For more<br>information about choosing the jar, see the System Requirements<br>information on [Microsoft Download<br>Center](https://www.microsoft.com/en-us/download/details.aspx?id=11774).<br><br>When using this component with Datasource in Talend Runtime, you need<br>to use the Open source JTDS driver. |
| ELT MSSql Map Editor | The ELT Map editor allows you to define<br>the output schema and make a graphical build of the SQL statement to be<br>executed. The column names of schema can be different from the column<br>names in the database.<br><br>You can filter schema columns in an input or output table<br>by clicking the Enable/disable column name filter button in the<br>corresponding table and entering the search keyword in the field displayed.<br><br>You can click ![](https://help.qlik.com/talend/en-US/components/Resources/images/button-elt-map-setup-configuration.png) on the upper left<br>corner and in the Property Settings dialog box displayed, select the<br>Add quotes in columns when generating query check box to add<br>quotes for the column names in the generated SQL query. This check box is displayed as<br>Delimited identifiers if you have not installed the 8.0 R2022-11<br>Talend Studio<br>monthly update or a later one provided by Talend. |
| Style link | Select the way in which links are displayed.<br><br><br>Auto: By default, the links between the input and output schemas and the Web service parameters are in the form of curves.<br><br><br>Bezier curve: Links between the schema and the Web service parameters are in the form of curve.<br><br><br>Line: Links between the schema and the Web service parameters are in the form of straight lines.<br><br>This option slightly optimizes performance. |
| Property type | Either Built-in or Repository.<br><br><ul> <li> <span>Built-in</span>: No property data stored                        centrally.</li> <li> <span>Repository</span>: Select the Repository                        file where Properties are stored. The following fields are pre-filled in                        using fetched data.</li> </ul> |
| Host | Enter the database server IP address. |
| Port | Enter the listening port number of DB server. |
| Database | Enter the name of the database. |
| Username and Password | Enter the DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Dry run | Select this option to populate the QUERY variable of the ELTOutput component connected to the<br>component while not connecting to the database or executing queries.<br><br>Information noteNote: This option is available only when you have installed the R2022-01 Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Additional JDBC parameters | Specify additional connection properties for the DB connection you are<br>creating. This option is not available if you have selected the Use an existing connection checkbox in the<br>Basic settings. |
| Authenticate using Azure Active Directory | When selected, this option allows you pick the authentication mode to use<br>from the Azure Active Directory authentication mode<br>dropdown list:<br><br><ul> <li><span>Service principal (client secret)</span>: use the service                        principal credentials (client ID and client secret) to authenticate.</li> <li><span>User password</span>: use the Azure Active Directory user                        credentials (username and password) to authenticate.</li> </ul><br><br>This option is only available when<br>Microsoft is selected from the JDBC<br>Provider dropdown list in the Basic<br>settings view. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at a Job level as<br>well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | tELTMSSqlMap is used along with a<br>tELTMSSqlInput and tELTMSSqlOutput. Note that the Output link to be<br>used with these components must correspond strictly to the syntax of the table<br>name.<br><br>Information noteNote: The ELT components do not handle actual data flow but<br>only schema information. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
