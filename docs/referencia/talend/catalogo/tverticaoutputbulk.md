# tverticaoutputbulk

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tverticaoutputbulk  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tverticaoutputbulk -->

# tVerticaOutputBulk

Prepares a file to be used by the tVerticaBulkExec component to feed a Vertica database.

The tVerticaOutputBulk component and the tVerticaBulkExec component are generally used together as parts of a two step process. In the first step, an output file is generated. In the second step, the file is used in a bulk load operation to feed a database. These two steps are fused together in the tVerticaOutputBulkExec component. The advantage of using two separate components is that the data can be transformed before it is loaded into the database.

## tVerticaOutputBulk Standard properties

These properties are used to configure tVerticaOutputBulk running in the Standard Job framework.

The Standard tVerticaOutputBulk component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property Type | Select the way the file path and the schema will be set.<br><br><ul> <li> <p> <span>Built-In</span>: The file path and the schema will be                                set locally for this component.</p> </li> <li> <p> <span>Repository</span>: The file details stored centrally                                in <span><span>Repository</span><abbr> &gt; </abbr><span>Metadata</span></span> will be reused by this component.</p> <p>You need to click                                the <span>[...]</span> button next to it and in the pop-up                                    <span>Repository Content</span> dialog box, select the                                file to be reused, and all related properties will be automatically                                filled in.</p> </li> </ul> |
| File Name | The path to the file to be generated.<br><br>This file is generated on the same machine where Talend Studio<br>is installed or where your Job using this component is deployed. |
| Append | Select this check box to add new rows at the end of the file. |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>When the schema to be reused has default values that are<br>integers or functions, ensure that these default values are not enclosed within<br>quotation marks. If they are, you must remove the quotation marks manually.<br><br>For more information, see [Retrieving table schemas](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg).<br><br>Click Edit schema to make changes to<br>the schema. If you make changes, the schema automatically becomes built-in.<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Row Separator | The separator used to identify the end of a row. |
| Include Header | Select this check box to include the column header to the file. |
| Encoding | Select an encoding method from the list, or select<br>CUSTOM and define it manually. This field is<br>compulsory for database data handling. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| NB\_LINE | The number of rows processed. This is an After variable and<br>it returns an integer. |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is more commonly used with the tVerticaBulkExec component. Used together, they<br>offer gains in performance while feeding a Vertica database.<br><br><br>Talend Studio and the<br>Vertica database create very fast and affordable data warehouse and data mart applications.<br>For more information about how to configure *Talend Studio* to connect to Vertica, see [Talend and HP Vertica Tips and<br>Techniques](https://www.vertica.com/kb/Vertica-Integration-with-Talend-Connection-Guide/Content/Partner/Vertica-Integration-with-Talend-Connection-Guide.htm). |
