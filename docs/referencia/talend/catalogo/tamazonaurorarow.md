# tamazonaurorarow

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tamazonaurorarow  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tamazonaurorarow -->

# tAmazonAuroraRow

Executes query statements on a specified Amazon Aurora database table.

## tAmazonAuroraRow Standard properties

These properties are used to configure tAmazonAuroraRow running in the Standard Job framework.

The Standard tAmazonAuroraRow component belongs to the Cloud and the Databases families.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property Type | Either Built-In or<br>Repository.<br><br><ul> <li> <span>Built-In</span>: No property data stored                                centrally.</li> <li> <span>Repository</span>: Select the repository                                file in which the properties are stored. The database connection fields                                that follow are completed automatically using the data retrieved.</li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Host | Type in the IP address or hostname of the Amazon Aurora<br>database. |
| Port | Type in the listening port number of the Amazon Aurora<br>database. |
| Database | Type in the name of the database you want to use. |
| Username and Password | Type in the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br>This component offers the advantage of the<br>dynamic schema feature. This allows you to retrieve unknown columns from source<br>files or to copy batches of columns from a source without mapping each column<br>individually. For further information about dynamic schemas, see [Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema).<br><br>This<br>dynamic schema feature is designed for the purpose of retrieving unknown columns of a<br>table and is recommended to be used for this purpose only; it is not recommended for the<br>use of creating tables.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Table Name | Type in the name of the table to which the query statements<br>are executed. |
| Query Type and Query | Enter the database query paying particularly attention to the<br>proper sequence of the fields in order to match the schema definition.<br><br><br>*If using the dynamic schema feature, the SELECT query must<br>include the \* wildcard, to retrieve<br>all of the columns from the table selected.* |
| Guess Query | Click the button to generate the query which corresponds to the<br>table schema in the Query field. |
| Die on error | This check box is selected by default. Clear the check box to skip<br>the row on error and complete the process for error-free rows. If<br>needed, you can retrieve the rows on error via a Row &gt; Rejects link. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC parameters | Specify additional connection properties for the database<br>connection you are creating. |
| Propagate QUERY's recordset | Select this check box to insert the result of the query in a<br>COLUMN of the current flow. Select this column from the use column list.<br><br>Information noteNote: This option allows the component to have a different schema<br>from that of the preceding component. Moreover, the column that<br>holds the QUERY's recordset should be set to the type of<br>*Object* and this component<br>is usually followed by tParseRecordSet. |
| Use PreparedStatement | Select this check box if you want to query the database using a<br>PreparedStatement. In the Set<br>PreparedStatement Parameter table, define the<br>parameters represented by "?" in the SQL instruction of the<br>Query field in the Basic Settings tab.<br><br><br>Parameter Index: Enter the<br>parameter position in the SQL instruction.<br><br><br>Parameter Type: Enter the parameter<br>type.<br><br><br>Parameter Value: Enter the<br>parameter value.<br><br>Information noteNote: This option is very useful if you need to execute the same<br>query several times. Performance levels are increased |
| Commit every | Number of rows to be completed before committing batches of<br>rows together into the table. This option ensures transaction quality<br>(but not rollback) and above all better performance on executions. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at the Job<br>level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>QUERY: the query statement<br>being processed. This is a Flow variable and it returns a string.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component offers the flexibility of the DB query. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
