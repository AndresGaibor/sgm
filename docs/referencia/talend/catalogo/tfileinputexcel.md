# tfileinputexcel

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tfileinputexcel  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfileinputexcel -->

# tFileInputExcel

Reads an Excel file row by row to split them up into fields using regular expressions and then sends the fields as defined in the schema to the next component.

## tFileInputExcel Standard properties

These properties are used to configure tFileInputExcel running in the Standard Job framework.

The Standard tFileInputExcel component belongs to the File family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | Either Built-in or Repository.<br><br><ul> <li> <p> <span>Built-in</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the properties are                        stored. The fields that follow are completed automatically using the data                        retrieved.</p> </li> </ul> |
| ![](https://help.qlik.com/talend/en-US/components/Resources/images/Save_Icon.png) | Click this icon to open a connection wizard and<br>store the Excel file connection parameters you set in the component Basic settings view.<br><br>For more information about setting up and storing file<br>connection parameters, see [Setting connection parameters](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/setting-connection-parameters). |
| Read excel2007 file format (xlsx) | Select this check box to read the .xlsx or<br>.xlsm file of Excel 2007. |
| File<br>Name/Stream | File<br>name: Name of the file and/or the variable to be processed.<br><br><br>Stream: Data flow to be<br>processed. The data must be added to the flow in order to be collected by<br>tFileInputExcel via<br>the INPUT\_STREAM variable in the auto-completion list<br>(Ctrl+Space).<br><br>For further information about how to define and use a variable<br>in a Job, see [Using variables in a Job or Route](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/using-variables-in-job-or-route).<br><br>Information noteWarning: Use absolute path (instead of relative path) for<br>this field to avoid possible errors. |
| Password | Provide the password set for the Excel file in double<br>quotation marks by clicking the [...] button next to this<br>frame.<br><br>This field is for Excel 2007 (and higher versions) files<br>protected by passwords and is available when Read<br>excel2007 file format(xlsx) is selected.<br><br>This component supports standard encryption and agile<br>encryption. |
| All<br>sheets | Select this check box to process all sheets of<br>the Excel file. |
| Sheet list | Click the plus button to add as many lines as<br>needed to the list of the excel sheets to be processed:<br><br><br>Sheet (name or<br>position): enter the name or position of the excel sheet to be<br>processed.<br><br><br>Use Regex: select this<br>check box if you want to use a regular expression to filter the sheets to<br>process. |
| Header | Enter the number of rows to be skipped in the beginning of file.<br><br>Note that when dynamic schema is used, the first row of<br>the input data is always treated as the header row no matter whether the Header field value is set or not. For more information about<br>dynamic schema, see [Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema). |
| Footer | Number of records to be skipped at the end of<br>the file. |
| Limit | Maximum number of lines to be processed. |
| Affect each sheet(header&footer) | Select this check box if you want to apply the<br>parameters set in the Header and Footer fields to all excel sheets to be processed.<br><br>Information noteNote: This option is only available when you select Memory-consuming (User mode) from the<br>Generation mode drop-down list in<br>the Advanced settings view. |
| Die<br>on error | Select this check box to stop the execution of<br>the Job when an error occurs. Clear the check box to skip the row on error and<br>complete the process for error-free rows. If needed, you can collect the rows<br>on error using a Row<br>&gt; Reject link. |
| First column and Last column | Define the range of the columns to be<br>processed through setting the first and last columns in the First column<br>and Last column fields respectively. |
| Schema and Edit<br>Schema | A schema is a row description, it defines the<br>number of fields to be processed and passed on to the next component. The<br>schema is either Built-in or stored remotely in the Repository.<br><br><ul> <li> <span>Built-in</span>: The schema will be created                        and stored locally for this component only. </li> <li> <span>Repository</span>: The schema already exists                        and is stored in the Repository, hence can be reused in various projects and                        Job flowcharts. </li> </ul><br><br>This component offers the advantage of the<br>dynamic schema feature. This allows you to retrieve unknown columns from source<br>files or to copy batches of columns from a source without mapping each column<br>individually. For further information about dynamic schemas, see [Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema).<br><br>This<br>dynamic schema feature is designed for the purpose of retrieving unknown columns of a<br>table and is recommended to be used for this purpose only; it is not recommended for the<br>use of creating tables.<br><br>Information noteNote: If you are using the dynamic schema feature, make sure date pattern is set<br>for the dynamic column in the Date Pattern field in the<br>schema editor. The default date pattern for the dynamic column is<br>"dd-MM-yyyy".<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Advanced separator | Select this check box to change the used data<br>separators. |
| Trim all columns | Select this check box to remove the leading and trailing whitespaces from all<br>columns. When this check box is cleared, the Check column to<br>trim table is displayed, which lets you select particular columns to<br>trim. |
| Check column to trim | This table is filled automatically with the schema being used. Select the check<br>box(es) corresponding to the column(s) to be trimmed. |
| Convert date column to string | Available when Read excel2007 file format (xlsx) is selected<br>in the Basic settings<br>view.<br><br>Select this check box to show the table<br>Check need convert date<br>column. Here you can parse the string columns that contain date<br>values based on the given date pattern.<br><br><br>Column: all the columns<br>available in the schema of the source .xlsx file.<br><br><br>Convert: select this check box to choose all the columns for<br>conversion (only if they are all of the string type). You can also select the<br>individual check box next to each column for conversion.<br><br><br>Date pattern: set the<br>date format here. |
| Encoding | Select the encoding from the list or select<br>Custom and define it<br>manually. This field is compulsory for DB data handling. |
| Read real values for numbers | Select this check box to read numbers in real<br>values. This check box becomes unavailable when you select Read excel2007 file format<br>(xlsx) in the Basic<br>settings view. |
| Stop reading on encountering empty rows | Select this check box to ignore the empty line<br>encountered and, if there are any, the lines that follow this empty line. This<br>check box becomes unavailable when you select Read excel2007 file format (xlsx) in the<br>Basic settings<br>view. |
| Generation mode | Available when Read excel2007 file format (xlsx) is selected<br>in the Basic settings<br>view. Select the mode used to read the Excel 2007 file.<br><br><ul> <li> <p> <span>Less memory consumed for large excel(Event                              mode)</span>: used for large file. This is a memory-saving mode                           to read the Excel 2007 file as a flow. This option helps prevent Job                           failure with an out-of-memory error due to high memory consumption when                           reading large Excel files.</p> <p>With this mode selected, reference variables will be extracted with the                           format symbol, for example, the percent symbol % and the currency symbol                           $. Moreover, the <span>Include phonetic runs</span> check box                           is selected by default to allow you to use phonetic strings at index. As                           Event mode is a memory-saving mode (main aim), it is supposed to lose                           some cell format to save memory and CPU time.</p> </li> <li> <p> <span>Memory-consuming (User mode)</span>: used for                           small file. It needs much memory. With this mode selected, the pure data                           without the format symbol will be extracted.</p> </li> </ul> |
| Don't validate the cells | Select this check box to in order not to<br>validate data. This check box becomes unavailable when you select Read excel2007 file format<br>(xlsx) in the Basic<br>settings view. |
| Ignore the warning | Select this check box to ignore all warnings<br>generated to indicate errors in the Excel file. This check box becomes<br>unavailable when you select Read<br>excel2007 file format (xlsx) in the Basic settings view. |
| Set minimum inflation rate | Select this option to set the ratio between deflated and inflated bytes to detect zipbomb. Type<br>the new minimum inflation rate in the text box that appears. See<br>***setMinInflateRatio*** at https://poi.apache.org/apidocs/dev/org/apache/poi/openxml4j/util/ZipSecureFile.html for related information.<br><br>An improper minimum inflation rate may result in *Zip bomb detected*<br>exception when you try to open an Excel file. You can eliminate exceptions of<br>this type by setting the minimum inflation rate to a smaller value.<br><br>This option is available when Read excel2007 file format<br>(xlsx) is selected in the Basic settings<br>view.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-10<br>Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| tStatCatcher Statistics | Select this check box to gather the Job<br>processing metadata at a Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>CURRENT\_SHEET: the name of the sheet being processed. This is a Flow<br>variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | Use this component to read an Excel file and<br>to output the data separately depending on the schemas identified in the file.<br>You can use a Row &gt;<br>Reject link to filter the data which doesn't correspond to the<br>type defined. For an example of how to use these two links, see [Procedure](https://help.qlik.com/talend/en-US/components/8.0/processing/textractxmlfield-tlogrow-tfileinputdelimited-tfileoutputdelimited-procedure-standard-component-drop). |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |

**Related concepts**

* [Extracting data from an Excel file using a dynamic schema](https://help.qlik.com/talend/en-US/components/8.0/extracting-data-from-excel-file-using-dynamic-schema-c "This scenario extracts data from an Excel 2007 file. It demonstrates the use of dynamic schema.")
