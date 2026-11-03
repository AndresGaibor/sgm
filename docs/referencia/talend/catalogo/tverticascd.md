# tverticascd

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tverticascd  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tverticascd -->

# tVerticaSCD

Tracks and reflects data changes in a dedicated Vertica SCD table.

## tVerticaSCD Standard properties

These properties are used to configure tVerticaSCD running in the Standard Job framework.

The Standard tVerticaSCD component belongs to the Business Intelligence and the Databases families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property Type | Select the way the connection details<br>will be set.<br><br><ul> <li> <p> <span>Built-In</span>: The connection details will be set                                locally for this component. You need to specify the values for all                                related connection properties manually.</p> </li> <li> <p> <span>Repository</span>: The connection details stored                                centrally in <span><span>Repository</span><abbr> &gt; </abbr><span>Metadata</span></span> will be reused by this component. </p> <p>You need to click                                the <span>[...]</span> button next to it and in the pop-up                                    <span>Repository Content</span> dialog box, select the                                connection details to be reused, and all related connection                                properties will be automatically filled in.</p> </li> </ul> |
| DB Version | Select the version of the database. |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>When a Job contains the parent Job and the child Job, if you need to<br>share an existing connection between the two levels, for example, to share the<br>connection created by the parent Job with the child Job, you have to:<br><br><ol> <li> <p>In the parent level, register the database connection to be shared                in the <span>Basic settings</span> view of the connection                component which creates that very database connection.</p> </li> <li> <p>In the child level, use a dedicated connection component to read                that registered database connection.</p> </li> </ol><br><br>For an example about how to share a database connection across Job levels, see<br>[Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Host | Enter the IP address or hostname of the database. |
| Port | Enter the listening port number of the database. |
| Database | Enter the name of the database. |
| Schema | Enter the schema of the database. |
| Username and Password | Enter the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | Enter the name of the table into<br>which data will be written. |
| Action on table | Select an operation to be performed on the table defined.<br><br><ul> <li> <p> <span>None</span>: No operation is carried out.</p> </li> <li> <p> <span>Create table</span>: The table does not exist and            gets created.</p> </li> <li> <p> <span>Create table if does not exist</span>: The table is            created if it does not exist.</p> </li> </ul> |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>Click Edit schema to make changes to<br>the schema. If you make changes, the schema automatically becomes built-in.<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| SCD Editor | Click the [...] button and in the<br>SCD component editor dialog box displayed,<br>configure the data flow for slowly changing dimension outputs.<br><br>For more information, see [SCD management methodology](https://help.qlik.com/talend/en-US/components/8.0/scd/scd-management-methodology). |
| Use memory saving mode | Select this check box to maximize system<br>performance. |
| Die on error | Select the checkbox to stop the execution of the Job when an error<br>occurs.<br><br>Clear the checkbox to skip any rows on error and complete the<br>process for error-free rows.<br><br>When errors are skipped, you can collect the rows on error<br>using a Row &gt; Reject connection. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional JDBC parameters for the database connection created.<br><br>This property is not available when the Use an existing connection check box in the Basic<br>settings view is selected. |
| End date time details | Specify the time value of the SCD end date time setting in the format<br>of HH:mm:ss. The default value is 12:00:00.<br><br>This property is available only when the SCD Type 2 method is used and<br>Fixed year value is selected for creating the<br>SCD Type 2 end date in the SCD editor. |
| Debug mode | Select this check box to display each step during processing entries in a database. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| NB\_LINE\_INSERTED | The number of rows inserted. This is an After variable and<br>it returns an integer. |
| NB\_LINE\_UPDATED | The number of rows updated. This is an After variable and it<br>returns an integer. |
| NB\_LINE\_REJECTED | The number of rows rejected. This is an After variable and<br>it returns an integer. |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is usually used as an end component of a Job or<br>subJob and it always needs an input link.<br><br><br>Talend Studio and the<br>Vertica database create very fast and affordable data warehouse and data mart applications.<br>For more information about how to configure *Talend Studio* to connect to Vertica, see [Talend and HP Vertica Tips and<br>Techniques](https://www.vertica.com/kb/Vertica-Integration-with-Talend-Connection-Guide/Content/Partner/Vertica-Integration-with-Talend-Connection-Guide.htm). |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | This component does not support using SCD type 0 together with other<br>SCD types. |
