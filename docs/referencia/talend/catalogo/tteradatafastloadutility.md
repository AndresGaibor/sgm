# tteradatafastloadutility

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tteradatafastloadutility  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tteradatafastloadutility -->

# tTeradataFastLoadUtility

Executes a database query according to a strict order which must be the same as the one in the schema.

tTeradataFastLoad Utility reads a database and extracts fields using queries. The retrieve list of fields is then transferred to the next component, using a connection flow (Main row).

## tTeradataFastLoadUtility Standard properties

These properties are used to configure tTeradataFastLoadUtility running in the Standard Job framework.

The Standard tTeradataFastLoadUtility component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | Either Built-In or Repository.<br><br><ul> <li> <p> <span>Built-In</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the            properties are stored.</p>The fields that follow are completed automatically using the data                           retrieved.</li> </ul> |
| Execution platform | Select the Operating System type you use. |
| Host | Host name or IP address of the database server. |
| Database<br>name | Database name. |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | Name of the table to be written. Note that only one table can be<br>written at a time. |
| Schema and Edit<br>Schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><br>Built-In: You create and store the schema locally for this component<br>only.<br><br><br>Repository: You have already created the schema and stored it in the<br>Repository. You can reuse it in various projects and Job designs.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Script generated folder | Browse your directory and select the destination of the file which<br>will be created. |
| Load file | Browse your directory and select the file from which you want to<br>load data. |
| Field separator | Character, string, or regular expression to separate fields. |
| Error file | Browse your directory and select the destination of the file where<br>the error messages will be recorded. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Define character set | Specify the character encoding you need use for your<br>system. |
| Check point | Enter the check point value. |
| Error files | Enter the file name where the error messages are stored. By<br>default, the code ERRORFILES table\_ERR1, table\_ERR2 is<br>entered, meaning that the two tables *table\_ERR1*<br>and *table\_ERR2* are used to record the error<br>messages. |
| Return fastload error | Select this check box to specify the exit code number to indicate<br>the point at which an error message should display in the<br>console. |
| ERRLIMIT | Enter the limit number of errors detected during the loading<br>phase. Processing stops when the limit is reached.<br><br>The default error limit value is 1000000.<br><br>For more information, see *Teradata FastLoad<br>Reference* documentation. |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component offers the flexibility of the DB query and covers<br>all possible SQL queries. |
