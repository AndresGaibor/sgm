# toraclescd

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/toraclescd  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/toraclescd -->

# tOracleSCD

Reflects and tracks changes in a dedicated Oracle SCD table.

tOracleSCD addresses Slowly Changing Dimension needs, reading regularly a source of data and logging the changes into a dedicated SCD table.

## tOracleSCD Standard properties

These properties are used to configure tOracleSCD running in the Standard Job framework.

The Standard tOracleSCD component belongs to the Business Intelligence and the Databases families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p>Either <span>Built-in</span> or								<span>Repository</span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored							centrally.</p> </li> <li> <p> <span>Repository</span>: Select the Repository							file where properties are stored. The following fields are pre-filled in							using fetched data.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Note that connections that are of<br>WALLET type are for the tCreateTable component, the tOracleInput<br>component, and the tOracleOutput component only. Make sure that the connection selected is<br>not of the WALLET type to prevent possible errors.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Connection type | Drop-down list of available drivers:<br><br><br>Oracle OCI: Select this<br>connection type to use Oracle Call Interface with a set of C-language<br>software APIs that provide an interface to the Oracle database.<br><br><br>Oracle Service Name: Select this<br>connection type to use the TNS alias that you give when you connect to<br>the remote database.<br><br><br>Oracle SID: Select this<br>connection type to uniquely identify a particular database on a<br>system.<br><br><br>Oracle Custom: Select this<br>connection type to access a clustered database. |
| DB Version | Select the Oracle version you are using. |
| Host | Database server IP address. |
| Port | Listening port number of DB server. |
| Database | Name of the database. |
| Schema | Name of the DB schema. |
| Username and Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | Name of the table to be written. Note that only one table<br>can be written at a time. |
| Action on table | Select to perform one of the following operations on the<br>table defined:<br><br>- None: No action is carried out on the table.<br><br>- Create table: A new table is created.<br><br>- Create table if not exists: A table is created if it<br>does not exist. |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-in</span>: The schema is created							and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already							exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul> |
| SCD Editor | The SCD editor helps to build and configure the data flow<br>for slowly changing dimension outputs.<br><br>For more information, see [SCD management methodology](https://help.qlik.com/talend/en-US/components/8.0/scd/scd-management-methodology). |
| Use memory saving Mode | Select this check box to maximize system performance. |
| Source keys include Null | Select this check box to allow the source key columns to<br>have Null values.<br><br>Information noteWarning:<br><br>Special attention should be paid to the uniqueness of<br>the source key(s) values when this option is selected. |
| Die on error | This check box is cleared by default, meaning to skip the<br>row on error and to complete the process for error-free rows. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC parameters | Specify additional connection properties for the DB<br>connection you are creating. This option is not available if you have<br>selected the Use an existing<br>connection check box in the Basic settings. |
| End date time details | Specify the time value of the SCD end date time setting in the<br>format of *HH:mm:ss*. The default<br>value for this field is *12:00:00*.<br><br>This field appears only when SCD Type 2 is used and<br>Fixed year value is selected for creating the SCD<br>end date. |
| tStatCatcher Statistics | Select this check box to collect log data at the<br>component level. |
| Debug mode | Select this check box to display each step during<br>processing entries in a database. |
| Support NLS | Select this option to enable globalization support. See [Overview of Globalization Support](https://docs.oracle.com/en/database/oracle/oracle-database/21/nlspg/overview-of-globalization-support.html) for<br>related information.<br><br>This option is available when the Use an existing<br>connection option is cleared and Oracle 18 and<br>above is selected from the DB Version<br>drop-down list in the Basic settings view.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-09<br>Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE\_UPDATED: the number of rows updated.<br>This is an After variable and it returns an integer.<br><br><br>NB\_LINE\_INSERTED: the number of<br>rows inserted. This is an After variable and it returns an integer.<br><br><br>NB\_LINE\_REJECTED: the number of rows rejected. This is an After<br>variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as Output component. It requires<br>an Input component and Row main link as input. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | This component does not support using SCD type 0 together with other<br>SCD types. |
