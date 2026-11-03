# thsqldbinput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/thsqldbinput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/thsqldbinput -->

# tHSQLDbInput

Executes a DB query with a strictly defined order which must correspond to the schema definition and then it passes on the field list to the next component via a Main row link.

tHSQLDbInput reads a database and extracts fields based on a query.

## tHSQLDbInput Standard properties

These properties are used to configure tHSQLDbInput running in the Standard Job framework.

The Standard tHSQLDbInput component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| ![](https://help.qlik.com/talend/en-US/components/Resources/images/Save_Icon.png) | Click this icon to open a database connection wizard and store the<br>database connection parameters you set in the component Basic settings view.<br><br>For more information about setting up and storing database<br>connection parameters, see [Centralizing database metadata](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/centralizing-database-metadata). |
| Running Mode | Select on the list the Server Mode corresponding to your DB setup<br>among the four propositions :<br><br><br>HSQLDb Server, HSQLDb WebServer, HSQLDb In Process Persistent, HSQLDb In Memory. |
| Use TLS/SSL sockets | Select this check box to enable the secured mode if<br>required. |
| Host | Database server IP address. |
| Port | Listening port number of DB server. |
| Database Alias | Alias name of the database. |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| DB path | Specify the directory to the database you want to connect to. This<br>field is available only to the HSQLDb In<br>Process Persistent running mode.<br><br>Information noteNote:<br><br>By default, if the database you specify in this field does not<br>exist, it will be created automatically. If you want to change<br>this default set­ting, modify the connection parameter set in<br>the Additional JDBC parameter<br>field in the Advanced settings<br>view |
| Db name | Enter the database name that you want to connect to. This field is<br>available only to the HSQLDb In Process<br>Persistent running mode and the HSQLDb In Memory running mode. |
| Schema and Edit<br>schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>This component offers the advantage of the                  dynamic schema feature. This allows you to retrieve unknown columns from source                  files or to copy batches of columns from a source without mapping each column                  individually. For further information about dynamic schemas, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema" target="_blank">Dynamic schema</a>.</p> <p>This            dynamic schema feature is designed for the purpose of retrieving unknown columns of a            table and is recommended to be used for this purpose only; it is not recommended for the            use of creating tables.</p> </li> <li> <p> <span>Built-in</span>: The schema is created								and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already								exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Query type and<br>Query | Enter your DB query paying particularly attention to properly<br>sequence the fields in order to match the schema definition.<br><br><br>*If using the dynamic schema<br>feature, the SELECT query must include the \* wildcard, to retrieve all of the columns from the table<br>selected.* |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC parameters | Specify additional connection properties for the DB connection you<br>are creating. When the running mode is HSQLDb<br>In Process Persistent , you can set the connection<br>property ifexists=true to allow connection to an<br>existing database only and avoid creating a new database. |
| Trim all the String/Char columns | Select this check box to remove leading and trailing whitespace<br>from all the String/Char columns. |
| Trim column | Remove leading and trailing whitespace from defined<br>columns. |
| tStat<br>Catcher Statistics | Select this check box to collect log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: Indicates the number of<br>lines processed. This is an After variable and it returns an<br>integer.<br><br><br>QUERY: Indicates the query to be<br>processed. This is a Flow variable and it returns a string.<br><br>For further information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables).<br><br>Information noteNote:<br><br>A Flow variable means it functions during the execution of a<br>component while an After variable means it functions after the<br>execution of a component. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component covers all possible SQL queries for HSQLDb<br>databases. |
| Connections | Outgoing links (from this component to another):<br><br><br>Row: Main; Iterate<br><br><br>Trigger: Run if; On Component Ok;<br>On Component Error; On Subjob Ok; On Subjob Error.<br><br>Incoming links (from one component to this one):<br><br><br>Row: Iterate;<br><br><br>Trigger: Run if; On Component Ok;<br>On Component Error; On Subjob Ok; On Subjob Error.<br><br>For further information regarding connections, see [Using connections in a Job](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/using-connections-in-job). |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |
