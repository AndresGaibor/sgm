# tteradatatptutility

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tteradatatptutility  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tteradatatptutility -->

# tTeradataTPTUtility

Writes the incoming data to a file and then loads the data from the file to a Teradata database.

As the combination of tTeradataFastLoad, tTeradataMultiLoad, tTeradataTPump, and tTeradataFastExport, tTeradataTPTUtility writes the incoming data to a file and then loads the data from the file to a Teradata database.

## tTeradataTPTUtility Standard properties

These properties are used to configure tTeradataTPTUtility running in the Standard Job framework.

The Standard tTeradataTPTUtility component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings Data file

| Property<br>Type | Either Built-In or Repository.<br><br><ul> <li> <p> <span>Built-In</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the            properties are stored.</p>The <span>Filename</span> field is completed automatically using                        the data retrieved.</li> </ul> |
| --- | --- |
| Filename | Specify the file to save the incoming data. |
| Append | Select this check<br>box to append the incoming data in the file specified in the Filename<br>field. |
| Property<br>Type | Either Built-In or Repository.<br><br><ul> <li> <span>Built-In</span>: No property data stored                        centrally.</li> <li> <span>Repository</span>: Select the repository file                        in which the properties are stored. The database connection related fields                        that follow are completed automatically using the data retrieved.</li> </ul> |
| Execution<br>platform | Select the Operating<br>System that will be used to run the Job, either Windows or Unix. |
| TDPID | Specify the Teradata<br>director program identifier. It can be either the name or the IP address<br>of the Teradata database system being accessed. |
| Database<br>name | Specify the name of<br>the Teradata database. |
| Username and Password | Specify the username<br>and the password for the Teradata database authentication.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Schema and Edit<br>Schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br>Information noteNote:<br><br>Avoid using a Teradata database keyword as a<br>Db Column<br>name in the schema. If you have to, be sure to enclose the column<br>name in a pair of *\"*. For<br>example, when the keyword *id*<br>is used as a database column name, the Db Column should be filled with *\"id\"*.<br><br><br>Built-In: You create and store the schema locally for this component<br>only.<br><br><br>Repository: You have already created the schema and stored it in the<br>Repository. You can reuse it in various projects and Job designs.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Consumer<br>Operator | Select a consumer<br>operator from the drop-down list.<br><br><ul> <li> <p> <span>Load</span>: writes data into an empty Teradata table                                    using the Teradata FastLoad utility protocol.</p> </li> <li> <p> <span>Inserter</span>: inserts data into Teradata tables                                    with SQL sessions.</p> </li> <li> <p> <span>Update</span>: performs Insert, Update, or Delete                                    operations using the Teradata MultiLoad utility                                protocol.</p> </li> <li> <p> <span>Stream</span>: loads data continuously into Teradata                                    tables using the Teradata TPump utility.</p> </li> </ul><br><br>For more information about Teradata<br>consumer operators, see [Teradata consumer<br>operators](https://docs.teradata.com/reader/j9~8T4F8ZcLkW7Ke0mxgZQ/xK9jh89gpz2RRqnRwV5Deg). |
| Action On<br>Data | Select an action<br>to be performed on the data from the drop-down list.<br><br><ul> <li> <p> <span>Insert</span>: inserts new records to the table.                                        If duplicates are found, the Job stops.</p> </li> <li> <p> <span>Update</span>: updates existing records in the                                        table.</p> </li> <li> <p> <span>InsertOrUpdate</span>: inserts new records or                                        updates existing records based on the given reference                                        key.</p> </li> <li> <p> <span>Delete</span>: removes records corresponding to                                        the input flow.</p> </li> </ul><br><br>Information noteNote:<br><br>You must specify at least one column as the primary<br>key on which the Update or Delete operation is based. You can<br>do that by clicking the [...] button next to Edit schema and selecting the check<br>box(es) next to the column(s) you want to set as primary<br>key(s).<br><br>This list field<br>appears only when the Update or Stream operator is selected from the Consumer Operator<br>drop-down list. |
| Producer<br>Operator | Select a producer<br>operator from the drop-down list. Currently, only the DataConnector operator<br>is supported.<br><br><br>DataConnector: accesses<br>files either directly or through an access module, and then writes it to<br>the data stream.<br><br>For more<br>information about Teradata producer operators, see [Teradata producer<br>operators](https://docs.teradata.com/reader/j9~8T4F8ZcLkW7Ke0mxgZQ/hMTd8FATzhUyis_IGAVB2w). |
| Table | Specify the name<br>of the table to be written into the Teradata database. Note that only<br>one table can be written at a time. |
| Script generated<br>folder | Specify the<br>directory under which the Teradata Parallel Transporter script file will<br>be created during the Job execution. This script file will be deleted at<br>the end of the Job execution. |
| Error<br>file | Specify the file<br>in which log messages will be recorded. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Row<br>separator | Character, string, or regular expression to separate rows. |
| Field<br>separator | Character, string, or regular expression to separate<br>fields. |
| Include<br>header | Select this check<br>box to include the column header to the file. |
| Encoding | Select the<br>encoding from the list or select Custom and define it manually. This<br>field is compulsory for database data handling. |
| Set Script<br>Parameters | Select this check<br>box to define script parameters, which will be used when generating a<br>script during the Job execution. If you do not specify them manually,<br>the system will use their default values. |
| Enforce database name on Log, Work, and Error<br>tables | Select this option to use a<br>database other than the default database for the work table, log table,<br>and the error table.<br><br>With this option selected,<br>provide the new database name for the work table, log table, and the<br>error table in the Option<br>attributes table under the Apply TPT consumer operator optional attributes<br>option.<br><br>This option is available when Inserter is not selected from the<br>Consumer Operator drop-down<br>list in the Basic settings<br>view. |
| Load<br>Operator | Specify the load<br>operator.<br><br>This field appears only<br>when the Set Script<br>Parameters check box is selected. |
| Data<br>Connector | Specify the data<br>connector.<br><br>This field appears<br>only when the Set Script<br>Parameters check box is selected. |
| Job Name | Specify the name<br>of a Teradata Parallel Transporter Job which is defined using the<br>Teradata *tbuild* command.<br><br>For further information about the *tbuild* command, see [tbuild](https://docs.teradata.com/r/yxBNqiK9WZh15WoRzMnBrw/pTFncWq01yte_hXC8TesYQ).<br><br>This field appears only when the<br>Set Script<br>Parameters check box is selected. |
| Layout Name<br>(schema) | Specify a schema<br>for the data to be loaded.<br><br>This<br>field appears only when the Set Script Parameters check box is<br>selected. |
| Define Log<br>table | Select this check<br>box to specify a log table so that log messages recorded in the log file<br>will also be written into the log table.<br><br>This<br>option is available when Inserter is not selected from the Consumer Operator drop-down list in the<br>Basic settings<br>view. |
| Return mload<br>error | Select this check<br>box to specify the exit code number to indicate the point at which an<br>error message should display in the console. |
| Define character<br>set | Select this check<br>box to specify the character encoding to be used in your<br>system. |
| Apply TPT consumer operator<br>optional attributes | Select this check<br>box to define optional attribute(s) for the consumer operator that you<br>have selected.<br><br>For more information about optional attributes of each consumer<br>operator, see [Teradata Parallel Transporter<br>Reference](https://docs.teradata.com/r/yxBNqiK9WZh15WoRzMnBrw/root). |
| Optional<br>attributes | Click the<br>[+] button<br>below the table to add as many rows as needed, each row for an optional<br>attribute, and set the following two parameters for each<br>attribute:<br><br><ul> <li> <p> <span>Name</span>: click the cell and select an optional                                    attribute from the drop-down list. The list of optional                                    attributes may vary depending on the consumer operator you have                                    selected. For details about supported optional attributes for                                    each consumer operator, see <a href="https://help.qlik.com/talend/en-US/components/8.0/teradata/supported-optional-attributes-for-each-consumer-operator" target="_blank">Supported optional attributes for each consumer operator</a>.</p> </li> <li> <p> <span>Value</span>: enter the value for the corresponding                                    optional attribute.</p> </li> </ul><br><br>For more information about the attribute value definition, see<br>[Teradata Parallel Transporter<br>Reference](https://docs.teradata.com/r/yxBNqiK9WZh15WoRzMnBrw/root).<br><br>This table appears only when the<br>Apply TPT consumer<br>operator optional attributes check box is<br>selected. |
| tStatCatcher<br>Statistics | Select this check<br>box to collect the log data at the component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global<br>Variables | EXIT\_VALUE: the process exit code. This is an After variable and it<br>returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage<br>rule** | Preceded by an input component, tTeradataTPTUtility writes the incoming<br>data to a file and then loads the data from the file to the Teradata<br>Database. High performance is provided during this process. For further<br>information about the usage of this component, see [tbuild](https://docs.teradata.com/r/yxBNqiK9WZh15WoRzMnBrw/pTFncWq01yte_hXC8TesYQ). |
| Limitation | The Teradata<br>client tool with the Teradata Parallel Transporter Base and Teradata<br>Parallel Transporter Stream features needs to be installed on the<br>machine where Jobs using this component are executed. |
