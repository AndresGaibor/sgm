# tpostgresqloutputbulk

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tpostgresqloutputbulk  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tpostgresqloutputbulk -->

# tPostgresqlOutputBulk

Prepares the file to be used as parameters in the INSERT query to feed the Postgresql database.

The tPostgresqlOutputBulk writes a file with columns based on the defined delimiter and the Postgresql standards.

The tPostgresqlOutputBulk and tPostgresqlBulkExec components are generally used together as part of a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT operation used to feed a database. These two steps are fused together in the tPostgresqlOutputBulkExec component, detailed in a separate section. The advantage of having two separate steps is that it makes it possible to transform data before it is loaded in the database.

## tPostgresqlOutputBulk Standard properties

These properties are used to configure tPostgresqlOutputBulk running in the Standard Job framework.

The Standard tPostgresqlOutputBulk component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

This component supports PostgreSQL vector data types. Use the VECTOR or Dynamic DB type in your schema column definition to store and then query vector embeddings. For more information about pgvector, read [the Amazon documentation](https://aws.amazon.com/about-aws/whats-new/2023/05/amazon-rds-postgresql-pgvector-ml-model-integration/).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | Either Built-in or<br>Repository<br><br><ul> <li> <p> <span>Built-in</span>: No property data stored                           centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository                           file in which the properties are stored. The fields that follow are                           completed automatically using the data retrieved.</p> </li> </ul> |
| File Name | Enter the name of the file to be generated.<br><br>Information noteWarning: This file is generated on the local machine or a shared folder<br>on the LAN. |
| Append | Select this checkbox to add the new rows at the end of the file. |
| Schema and Edit Schema | A schema is a row description, it defines the number of fields to be<br>processed and passed on to the next component. The schema is either Built-in or stored remotely in the Repository<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul><br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> </ul><br><br>This component supports PostgreSQL vector data types. Use the<br>VECTOR or Dynamic DB type in your schema<br>column definition to store and then query vector embeddings. For more information about<br>pgvector, read [the Amazon documentation](https://aws.amazon.com/about-aws/whats-new/2023/05/amazon-rds-postgresql-pgvector-ml-model-integration/). |

## Advanced settings

| Properties | Description |
| --- | --- |
| Row separator | String (ex: "\n"on Unix) to distinguish rows. |
| Field separator | Character, string, or regular expression to separate fields. |
| Include header | Select this checkbox to include the column header to the file. |
| Encoding | Select the encoding from the list or select Custom and define it manually. This field is compulsory for DB<br>data handling. |
| tStatCatcher Statistics | Select this checkbox to collect log data at the component level. |
| Enable parallel execution | Select this check box to perform high-speed data processing, by treating<br>multiple data flows simultaneously. Note that this feature depends on the database or<br>the application ability to handle multiple inserts in parallel as well as the number of<br>CPU affected. In the Number of parallel executions<br>field, either:<br><br><ul> <li>Enter the number of parallel executions desired.</li> <li>Press <span>Ctrl+Space</span> and select               the appropriate context variable from the list. For further information about context               variables, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables" target="_blank">Using contexts and variables</a>. </li> </ul><br><br>Note that when parallel execution is enabled, it is not possible to use global<br>variables to retrieve return values in a subJob.<br><br><ul><li>						            The <span>Action on							table</span> field is not available with the							parallelization function. Therefore, you must use a <span>tCreateTable</span> component if you							want to create a table. 					          </li><li>						            When parallel execution is enabled, it is not							possible to use global variables to retrieve return values in a							subJob.					          </li> </ul> |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is to be used along with tPostgresqlBulkExec component. Used together they offer gains in<br>performance while feeding a PostgreSQL database.<br><br>This component supports<br>PostgreSQL vector data types. |
