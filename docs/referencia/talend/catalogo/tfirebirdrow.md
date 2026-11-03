# tfirebirdrow

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tfirebirdrow  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfirebirdrow -->

# tFirebirdRow

Executes the stated SQL query on the specified Firebird database.

Depending on the nature of the query and the database, tFirebirdRow acts on the actual DB structure or on the data (although without handling data). The SQLBuilder tool helps you write easily your SQL statements.

tFirebirdRow is the specific component for this database query. The row suffix means the component implements a flow in the Job design although it doesn't provide output.

## tFirebirdRow Standard properties

These properties are used to configure tFirebirdRow running in the Standard Job framework.

The Standard tFirebirdRow component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Host | Database server IP address |
| Database | Name of the database |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-in</span>: The schema is created								and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already								exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Query type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: Fill in manually the								query statement or build it graphically using SQLBuilder</p> </li> <li> <p> <span>Repository</span>: Select the relevant								query stored in the Repository. The Query field gets accordingly								filled in.</p> </li> </ul> |
| Query | Enter your DB query paying particularly attention to properly<br>sequence the fields in order to match the schema definition. |
| Die on error | This check box is selected by default. Clear the check box to skip<br>the row on error and complete the process for error-free rows. If<br>needed, you can retrieve the rows on error via a Row &gt; Rejects link. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional JDBC parameters for the database connection created.<br><br>This property is not available when the Use an existing connection check box in the Basic<br>settings view is selected. |
| Propagate QUERY's recordset | Select this check box to insert the result of the query into a<br>COLUMN of the current flow. Select this column from the use column list.<br><br>Information noteNote:<br><br>This option allows the component to have a different schema<br>from that of the preceding component. Moreover, the column that<br>holds the QUERY's recordset should be set to the type of<br>*Object* and this component<br>is usually followed by tParseRecordSet. |
| Use PreparedStatement | Select this check box if you want to query the database using a<br>PreparedStatement. In the Set<br>PreparedStatement Parameter table, define the<br>parameters represented by "?" in the SQL instruction of the<br>Query field in the Basic Settings tab.<br><br><br>Parameter Index: Enter the<br>parameter position in the SQL instruction.<br><br><br>Parameter Type: Enter the parameter<br>type.<br><br><br>Parameter Value: Enter the<br>parameter value.<br><br>Information noteNote:<br><br>This option is very useful if you need to execute the same<br>query several times. Performance levels are increased |
| Commit every | Number of rows to be completed before committing batches of rows<br>together into the DB. This option ensures transaction quality (but<br>not rollback) and above all better performance on executions. |
| tStat<br>Catcher Statistics | Select this check box to collect log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | QUERY: the query statement<br>being processed. This is a Flow variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component offers the flexibility benefit of the DB query and<br>covers all possible SQL queries. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |
