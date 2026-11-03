# tteradatatpump

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tteradatatpump  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tteradatatpump -->

# tTeradataTPump

Inserts, updates, or deletes data in the Teradata database with the TPump loading utility which allows near-real-time data to be achieved in the data warehouse.

Use this component particularly for environments where batch windows are shrinking and warehouse maintenance overlaps normal working hours.

## tTeradataTPump Standard properties

These properties are used to configure tTeradataTPump running in the Standard Job framework.

The Standard tTeradataTPump component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | Either Built-In or Repository.<br><br><ul> <li> <p> <span>Built-In</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the            properties are stored.</p>The fields that follow are completed automatically using the data                        retrieved.</li> </ul> |
| Execution platform | Select the Operating System type you use. |
| Host | Host name or IP address of the database server. |
| Database<br>name | Database name. |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | Name of the table to be written. Note that only one table can be<br>written at a time. |
| Schema and Edit<br>Schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><br>Built-In: You create and store the schema locally for this component<br>only.<br><br><br>Repository: You have already created the schema and stored it in the<br>Repository. You can reuse it in various projects and Job designs.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Script generated folder | Browse your directory and select the destination of the file which<br>will be created. |
| Action to data | On the data of the table defined, you can perform:<br><br><br>Insert: Add new entries to the<br>table. If duplicates are found, job stops.<br><br><br>Update: Make changes to existing<br>entries<br><br><br>Insert or<br>update: Insert a new record. If the record with the given reference<br>already exists, an update would be made.<br><br><br>Delete: Remove entries<br>corresponding to the input flow.<br><br>Information noteWarning:<br><br><br>*It is necessary to specify at least one<br>column as a primary key on which the Update and Delete<br>operations are based. You can do that by clicking Edit Schema and selecting the<br>check box(es) next to the column(s) you want to set as<br>primary key(s).* |
| Where condition in case Delete | Type in a condition, which, once verified, will delete the<br>row.<br><br>This field appears only when Delete is selected from the Action to data drop-down list. |
| Load file | Browse your directory and select the file from which you want to<br>load data. |
| Field separator | Character, string, or regular expression to separate fields. |
| Error file | Browse your directory and select the destination of the file where<br>the error messages will be recorded. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Define Log table | This check box is selected to define a log table you want to use<br>in place of the default one that is the database table you defined<br>in Basic settings. The syntax<br>required to define the log table is<br>*databasename.logtablename*. |
| BEGIN LOAD | This field allows you to define your BEGIN LOAD command to<br>initiate or restart a TPump task. You can specify the number of<br>sessions to use, the error limit and any other parameters needed to<br>execute the task. The default value is:<br><br><br>SESSIONS 8 PACK 600 ARRAYSUPPORT ON CHECKPOINT 60 TENACITY 2<br>ERRLIMIT 1000.<br><br>For more information, see *Teradata Parallel Data Pump<br>Reference* documentation. |
| Return tpump error | Select this check box to specify the exit code number to indicate<br>the point at which an error message should display in the<br>console. |
| Define character set | Specify the character encoding you need use for your system |
| tStat<br>Catcher Statistics | Select this check box to collect log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | EXIT\_VALUE: the process exit code. This is an After variable and it<br>returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component offers the flexibility of the DB query and covers<br>all possible SQL queries. |

**Related tasks**

* [Inserting data into a Teradata database table](https://help.qlik.com/talend/en-US/components/8.0/tteradatatpump-trowgenerator-tfileoutputdelimited-tfileoutputdelimited-inserting-data-into-teradata-database-table-standard-component-in-this "In this scenario, you create a Job using tTeradataTPump to insert customer data into a Teradata database table and specify the exit code to be displayed in the event of an exception error.")
