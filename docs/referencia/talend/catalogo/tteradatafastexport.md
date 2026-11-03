# tteradatafastexport

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tteradatafastexport  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tteradatafastexport -->

# tTeradataFastExport

Exports data batches from a Teradata table to a customer system or to a smaller database.

tTeradataFastExport exports rapidly voluminous data batches from a Teradata table or view.

## tTeradataFastExport Standard properties

These properties are used to configure tTeradataFastExport running in the Standard Job framework.

The Standard tTeradataFastExport component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Use Commandline | Select this check box to enable the Talend CommandLine mode. |
| Use Java API | Select this check box to enable the Java API<br>mode. |
| Property type | Either Built-In or Repository.<br><br><ul> <li> <p> <span>Built-In</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the            properties are stored.</p>The fields that follow are completed automatically using the data                        retrieved.</li> </ul> |
| Execution platform | Select the Operating System type you use.<br><br>Available in the Use Commandline mode. |
| Host | Server name or IP. |
| Database name | Database name. |
| Username and Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | Name of the table to be written. Note that only<br>one table can be written at a time. |
| Schema and Edit Schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Use query | Select this check box to show the Query box where you can enter<br>the SQL statement.<br><br>Available in the Use Commandline mode. |
| Query | Enter the SQL statement in the Query box. |
| Log database | Log database name.<br><br>Available in the Use Commandline mode. |
| Log table | Log table name.<br><br>Available in the Use Commandline mode. |
| Script generated folder | Browse your directory and select the<br>destination of the file which will be created.<br><br>Available in the Use Commandline mode. |
| Exported file | Name and path to the file which will be<br>created. |
| Field separator | Character, string, or regular expression to separate fields. |
| Row separator | String (e.g.: "\n"on Unix) to separate rows.<br><br>Available in the Use Java API mode. |
| Error file | Browse your directory and select the<br>destination of the file where the error messages will be recorded.<br><br>Available in the Use Commandline mode. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Create<br>directories if do not exist | Select this option to have the<br>directories specified in the Basic<br>settings view created before generating files in them if the<br>directories do not exist. |
| Die When<br>Unnormal Terminated | Select this option to stop the<br>execution of the Job when the operation is terminated<br>unexpectedly. |
| Advanced<br>separator (for number) | Select this option to insert thousands<br>separators and decimal separators for numbers. You can set thousands separator<br>and decimal separator in the fields to the right.<br><br>This option is available when Use Java API is selected<br>in the Basic settings view. |
| Include<br>Header | Select this option to insert header<br>line in the output data.<br><br>This option is available when Use<br>Java API is selected in the Basic<br>settings view. |
| tStatCatcher Statistics | Select this check box to collect log data at<br>the component level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component offers the flexibility benefit<br>of the DB query and covers all possible SQL queries. |
| Limitation | If you have selected the Use Commandline mode, you need<br>to install the Teradata client on the machine where there is the Job that<br>involves this component. |
