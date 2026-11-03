# tbigqueryoutputbulk

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tbigqueryoutputbulk  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tbigqueryoutputbulk -->

# tBigQueryOutputBulk

Creates a .txt or .csv file for the data of large size so that you can process it according to your needs before transferring it to Google BigQuery.

The tBigQueryOutputBulk and tBigQueryBulkExec components are generally used together as parts of a two step process. In the first step, an output file is generated. In the second step, this file is used to feed a dataset. These two steps are fused together in the tBigQueryOutput component, detailed in a separate section. The advantage of using two separate components is that the data can be transformed before it is loaded in the dataset.

This component writes given data into a .txt or .csv file, ready to be transferred to Google BigQuery.

## tBigQueryOutputBulk Standard properties

These properties are used to configure tBigQueryOutputBulk running in the Standard Job framework.

The Standard tBigQueryOutputBulk component belongs to the Big Data family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>Click Edit schema to make changes to<br>the schema. If you make changes, the schema automatically becomes built-in.<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| File name | Browse, or enter the path to the *.txt* or *.csv* file you need to generate. |
| Append | Select the checkbox to write new data at the end of the existing data.<br>Otherwise, the existing data will be overwritten. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use a custom endpoint | Select this check box to use a private endpoint rather than the default one.<br><br>When selected, enter the URL in the following properties:<br><br><ul> <li><span>Google Storage Private API URL</span> by respecting the                           <span>"https://storage.googleapis.com"</span> format.</li> <li><span>Google BigQuery Private API URL</span> by respecting the                           <span>"https://bigquery.googleapis.com"</span> format.</li> </ul><br><br>For more information, see [Access Google APIs through endpoints](https://cloud.google.com/vpc/docs/configure-private-service-connect-apis) in<br>the Google Cloud documentation.<br><br>This property is only available when you<br>authenticate using Service account and<br>Application Default Credentials. |
| Field Separator | Enter a character, a string, or a regular expression to separate<br>fields for the transferred data. |
| Use custom null marker | Select this option to use a specific character as the<br>null marker. You can specify the null marker in double quotation markers<br>in the text frame to the right.<br><br>This option<br>prevents errors caused by fields with null values. |
| Create directory if not exists | Select this checkbox to create the directory you defined in the File field for Google Cloud Storage, if it does not<br>exist. |
| Custom the flush buffer size | Enter the number of rows to be processed before the memory is freed. |
| Check disk space | Select the this checkbox to throw an exception during execution if the disk<br>is full. |
| Encoding | Select the encoding from the list or select Custom<br>and define it manually. This field is compulsory for database data handling. The<br>supported encodings depend on the JVM that you are using. For more information, see<br>[https://docs.oracle.com](https://docs.oracle.com/). |
| tStatCatcher Statistics | Select this checkbox to collect the log data at the component<br>level/ |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| Usage rules | This is an output component which needs the data provided by its preceding component.<br><br>This component automatically detects and supports both<br>multi-regional locations and regional locations. When using the regional locations,<br>the buckets and the datasets to be used must be in the same locations. |
| BigQuery data type limitations | <ul> <li>The Record type of BigQuery is not supported.</li> <li>The columns for table metadata such as the                                Description column or the Mode column cannot be retrieved.</li> <li>The Timestamp data from your BigQuery system is formatted to be String                        data.</li> <li>The numeric data of BigQuery is converted to                                BigDecimal.</li> </ul> |
