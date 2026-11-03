# tsalesforceeinsteinbulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsalesforceeinsteinbulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsalesforceeinsteinbulkexec -->

# tSalesforceEinsteinBulkExec

Loads data into Salesforce Analytics Cloud from a local file.

## tSalesforceEinsteinBulkExec Standard properties

These properties are used to configure tSalesforceEinsteinBulkExec running in the Standard Job framework.

The Standard tSalesforceEinsteinBulkExec component belongs to the Business and the Cloud families.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property Type | Either Built-In or<br>Repository.<br><br><ul> <li> <span>Built-In</span>: No property data stored                        centrally.</li> <li> <span>Repository</span>: Select the repository file                        in which the properties are stored. The connection fields that follow are                        completed automatically using the data retrieved.</li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Note that when a Job contains the parent Job and the child Job,<br>Component List presents only the<br>connection components in the same Job level. |
| User Name and Password | Enter the Web service authentication details.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| End Point | Enter the WebService URL required to connect to Salesforce. For<br>example, *https://login.salesforce.com/services/Soap/u/37.0*. Note that the<br>version in the URL should be 32.0 or later. |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p>For the fields of numeric type (for example, byte, short,                           int, long, float, double, and BigDecimal), their length and precision                           values need to be specified. The default length and precision values are                              <em>10</em> and <em>2</em>, and you can                           also specify their custom values in the schema editor.</p> </li> <li> <p>For the fields of date type, you need to specify the                           format of the date in the schema editor. For more information about the                           supported date format, see <a href="http://www.salesforce.com/us/developer/docs/bi_dev_guide_ext_data_format/bi_dev_guide_ext_data_format.pdf" target="_blank">Analytics Cloud External Data Format                              Reference</a>.</p> </li> </ul><br><br>The Schema list and the<br>Editor schema button disappear if the<br>Custom JSON Metadata check box is<br>selected.<br><br>This component offers the advantage of the<br>dynamic schema feature. This allows you to retrieve unknown columns from source<br>files or to copy batches of columns from a source without mapping each column<br>individually. For further information about dynamic schemas, see [Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema).<br><br>This<br>dynamic schema feature is designed for the purpose of retrieving unknown columns of a<br>table and is recommended to be used for this purpose only; it is not recommended for the<br>use of creating tables.<br><br><br>Built-In: You create and store the schema locally for this component<br>only.<br><br><br>Repository: You have already created the schema and stored it in the<br>Repository. You can reuse it in various projects and Job designs.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Operation | Select an operation to perform on the dataset:<br><br><ul> <li> <p> <span>Append</span>: Append all data to the                           dataset. Create a dataset if it does not exist.</p> </li> <li> <p> <span>Upsert</span>: Insert or update rows in                           the dataset. Create a dataset if it does not exist.</p> </li> <li> <p> <span>Overwrite</span>: Create a new dataset                           with the given data, and replace dataset if it already exists.</p> </li> <li> <p> <span>Delete</span>: Delete the rows from the                           dataset.</p> </li> </ul><br><br>Information noteNote:<br><br><ul> <li> <p>A metadata JSON file is required for the <span>Append</span>, <span>Upsert</span>, and <span>Delete</span> operations.</p> </li> <li> <p>The data and metadata for the <span>Append</span> and <span>Upsert</span> operations must match the dataset on which the                              operation is happening. All columns, dimensions, and measures must                              match exactly. </p> </li> <li> <p>The <span>Append</span>                              operation is not allowed if you specify any column as the primary                              key.</p> </li> <li> <p>You must specify one (and only one) column as the                              primary key on which the <span>Upsert</span>                              or <span>Delete</span> operation is based.                              You can do that by clicking <span>Edit                                 schema</span> and selecting the check box next to the column                              you want to set as the primary key.</p> </li> <li> <p>The metadata for the <span>Delete</span> operation must be a subset of the dataset                              columns.</p> </li> </ul> |
| Name | Type in the name of the dataset into which the data will be<br>loaded. |
| CSV File | Specify the path to the local CSV file to be loaded. |

## Advanced settings

| Properties | Description |
| --- | --- |
| CSV Encoding | Enter the encoding type of the CSV file.<br><br>This field is not visible when the Custom JSON Metadata check box is selected. |
| Fields Delimiter | Enter the character that separates the field values in the CSV<br>file.<br><br>This field is not visible when the Custom JSON Metadata check box is selected. |
| Fields Enclosed By | Enter the character used to enclose the field values in the CSV<br>file.<br><br>This field is not visible when the Custom JSON Metadata check box is selected. |
| Line Terminated By | Enter the character indicating the end of a line.<br><br>This field is not visible when the Custom JSON Metadata check box is selected. |
| Auto Generate JSON Metadata Description | Select this check box to generate the JSON metadata description<br>automatically. |
| Header | Specify the number of lines to ignore in the CSV file.<br><br>This field is available only when the Auto Generate JSON Metadata Description check<br>box is cleared. |
| Unique API Name | Specify the unique API name for the object in the JSON metadata<br>description.<br><br>This field is available only when the Auto Generate JSON Metadata Description check<br>box is cleared. |
| Label | Specify the display name for the object in the JSON metadata<br>description.<br><br>This field is available only when the Auto Generate JSON Metadata Description check<br>box is cleared. |
| Fully Qualified Name | Specify the full path that uniquely identifies the record in<br>the JSON metadata description.<br><br>This field is available only when the Auto Generate JSON Metadata Description check<br>box is cleared. |
| Custom JSON Metadata | Select this check box to use a customized JSON metadata<br>file.<br><br>This check box is available only when the Auto Generate JSON Metadata Description check<br>box is cleared. |
| JSON Metadata | Specify the path to the customized JSON metadata file.<br><br>This field is available only when the Custom JSON Metadata check box is selected. |
| Generate JSON in File | Select this check box to write the JSON metadata description<br>into a local file.<br><br>This check box is not visible when the Custom JSON Metadata check box is selected. |
| Generated JSON Folder | Specify the directory where you want to store the generated<br>JSON metadata file.<br><br>This field is available only when the Generate JSON in File check box is selected. |
| Retrieve Upload Status | Select this check box to retrieve the status of the data<br>upload. |
| Time to wait for server answer (seconds) | Specify the amount of time in seconds to wait for the upload<br>status response from the server.<br><br>This field is available only when the Retrieve Upload Status check box is<br>selected. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component can be used as a standalone component. |
