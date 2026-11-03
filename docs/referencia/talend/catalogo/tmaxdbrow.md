# tmaxdbrow

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tmaxdbrow  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmaxdbrow -->

# tMaxDBRow

Acts on the actual DB structure or on the data (although without handling data), depending on the nature of the query and the database.

tMaxDBRow is the specific component for this database query. It executes the SQL query stated onto the specified database. The row suffix means the component implements a flow in the Job design although it doesn't provide output.

The SQLBuilder tool helps you write easily your SQL statements.

## tMaxDBRow Standard properties

These properties are used to configure tMaxDBRow running in the Standard Job framework.

The Standard tMaxDBRow component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Host | Database server IP address |
| Port | Listening port number of DB server. |
| Database | Name of the database. |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-in</span>: The schema is created								and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already								exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Table name | Type in the table name. |
| Query type | <ul> <li> <p>The query can be <span>Built-in</span> for a particular Job, or for commonly used								query, it can be stored in the <span>Repository</span> to ease the query reuse.</p> </li> <li> <p> <span>Built-in</span>: Fill in manually the query statement or build it graphically								using SQLBuilder.</p> </li> <li> <p> <span>Repository</span>: Select the relevant query stored in the Repository. The								<span>Query</span> field gets accordingly filled in.</p> </li> </ul> |
| Query | Enter your DB query paying particularly attention to properly<br>sequence the fields in order to match the schema definition. |
| Guess Query | Click the Guess Query button to generate the query<br>which corresponds to your table schema in the Query field. |
| Die on error | This check box is selected by default. Clear the check box to skip<br>the row on error and complete the process for error-free rows. If<br>needed, you can retrieve the rows on error via a Row &gt; Rejects link. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Propagate QUERY's recordset | Select this check box to insert the result of the query into a<br>COLUMN of the current flow. Select this column from the use column list. |
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
| Limitation | This component requires installation of its related jar files. |
