# thsqldbrow

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/thsqldbrow  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/thsqldbrow -->

# tHSQLDbRow

Acts on the actual DB structure or on the data (although without handling data), depending on the nature of the query and the database.

The SQLBuilder tool helps you write easily your SQL statements.

tHSQLDbRow is the specific component for this database query. It executes the SQL query stated onto the specified database. The row suffix means the component implements a flow in the Job design although it doesn't provide output.

## tHSQLDbRow Standard properties

These properties are used to configure tHSQLDbRow running in the Standard Job framework.

The Standard tHSQLDbRow component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Running Mode | Select on the list the Server Mode corresponding to your DB setup<br>among the four propositions :<br><br><br>HSQLDb Server, HSQLDb WebServer, HSQLDb In Process Persistent, HSQLDb In Memory. |
| Use TLS/SSL sockets | Select this check box to enable the secured mode if<br>required. |
| Host | Database server IP address |
| Port | Listening port number of DB server. |
| Database Alias | Name of the database |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| DB path | Specify the directory to the database you want to connect to. This<br>field is available only to the HSQLDb In<br>Process Persistent running mode.<br><br>Information noteNote:<br><br>By default, if the database you specify in this field does not<br>exist, it will be created automatically. If you want to change<br>this default setting, modify the connection parameter set in the<br>Additional JDBC parameter<br>field in the Advanced settings<br>view |
| Database | Enter the database name that you want to connect to. This field is<br>available only to the HSQLDb In Process<br>Persistent running mode and the HSQLDb In Memory running mode. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-in</span>: The schema is created								and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already								exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Query type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>. </p> </li> <li> <p> <span>Built-in</span>: Fill in manually the								query statement or build it graphically using SQLBuilder</p> </li> <li> <p> <span>Repository</span>: Select the relevant								query stored in the Repository. The Query field gets accordingly								filled in.</p> </li> </ul> |
| Query | Enter your DB query paying particularly attention to properly<br>sequence the fields in order to match the schema definition. |
| Die on error | This check box is selected by default. Clear the check box to skip<br>the row on error and complete the process for error-free rows. If<br>needed, you can retrieve the rows on error via a Row &gt; Rejects link. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC parameters | Specify additional connection properties for the DB connection you<br>are creating. When the running mode is HSQLDb<br>In Process Persistent , you can set the connection<br>property ifexists=true to allow connection to an<br>existing database only and avoid creating a new database. |
| Propagate QUERY's recordset | Select this check box to insert the result of the query into a<br>COLUMN of the current flow. Select this column from the use column list. |
| Commit every | Number of rows to be completed before committing batches of rows<br>together into the DB. This option ensures transaction quality (but<br>not rollback) and above all better performance on executions. |
| tStat<br>Catcher Statistics | Select this check box to collect log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | QUERY: Indicates the query to be<br>processed. This is a Flow variable and it returns a string.<br><br>For further information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables).<br><br>Information noteNote:<br><br>A Flow variable means it functions during the execution of a<br>component while an After variable means it functions after the<br>execution of a component. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component offers the flexibility of the DB query and covers<br>all possible SQL queries. |
| Connections | Outgoing links (from this component to another):<br><br><br>Row: Main; Reject; Iterate<br><br><br>Trigger: Run if; On Component Ok;<br>On Component Error; On Subjob Ok; On Subjob Error.<br><br>Incoming links (from one component to this one):<br><br><br>Row: Main; Iterate<br><br><br>Trigger: Run if; On Component Ok;<br>On Component Error; On Subjob Ok; On Subjob Error.<br><br>For further information regarding connections, see [Using connections in a Job](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/using-connections-in-job). |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |
