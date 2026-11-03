# taccessbulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/taccessbulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/taccessbulkexec -->

# tAccessBulkExec

Offers gains in performance when carrying out Insert operations in an Access database.

The tAccessOutputBulk and tAccessBulkExec components are generally used together to output data to a delimited file and then to perform various actions on the file in an Access database, in a two step process. These two steps are fused together in the tAccessOutputBulkExec component, detailed in a separate section. The advantage of using a two step process is that it makes it possible to carry out transformations on the data before loading it in the database.

This component executes an Insert action on the data provided.

## tAccessBulkExec Standard properties

These properties are used to configure tAccessBulkExec running in the Standard Job framework.

The Standard tAccessBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | Either Built-in or<br>Repository<br>.<br><br><ul> <li> <span>Built-in</span>: No property data is							          stored centrally.</li> <li> <span>Repository</span>: Select the repository							          file in which the properties are stored. The fields that follow are							          completed automatically using the data retrieved.</li> </ul> |
| File<br>Name | Browse to the delimited file to be loaded into your<br>database. |
| Create directory if does not exist | Select this check box to have the directories specified in the File Name<br>field created if the directories do not exist. |
| Append | Select this check box to append the data to the file. |
| Schema and Edit<br>Schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <span>Built-in</span>: The schema is created and                        stored locally for this component only. For more information about a                        component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</li> <li> <span>Repository</span>: The schema already exists and is stored in the							                 Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</li> </ul><br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Include header | Select this check box to include the column header. |
| Use text enclosure | Select this check box to enclose the text with characters. You can specify the character used to<br>enclose the text in the Field enclosure field. |
| Encoding | Select the encoding from the list or select Custom and define it manually. This field is<br>compulsory for DB data handling. |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is to be used along with tAccessOutputBulk component. Used together, they can<br>offer gains in performance while feeding an Access database. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | If you are using an ODBC driver, make sure that your JVM and ODBC versions match up: both<br>64-bit or 32-bit. |
