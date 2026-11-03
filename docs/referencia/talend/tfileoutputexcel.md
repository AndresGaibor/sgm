# tfileoutputexcel (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tfileoutputexcel  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfileoutputexcel -->

# tFileOutputExcel

Writes an MS Excel file with separated data values according to a defined schema.

## tFileOutputExcel Standard properties

These properties are used to configure tFileOutputExcel running in the Standard Job framework.

The Standard tFileOutputExcel component belongs to the File family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | Either Built-in or<br>Repository<br>.<br><br><ul> <li> <span>Built-in</span>: No property data stored                        centrally.</li> <li> <span>Repository</span>: Select the repository                        file in which the properties are stored. The fields that follow are                        completed automatically using the data retrieved.</li> </ul> |
| Write excel 2007 file format (xlsx /<br>xlsm) | Select this check box to write the processed data into the .xlsx or .xlsm<br>format of Excel 2007. |
| Use Output Stream | Select this check box to process the data flow of interest. Once you have<br>selected it, the Output Stream field<br>displays and you can type in the data flow of interest.<br><br>The data<br>flow to be processed must be added to the flow in order for this component to<br>fetch these data via the corresponding representative variable.<br><br>This variable can be already pre-defined in Talend Studio or provided by the context or the components you are using along with this<br>component; otherwise, you can define it manually and use it according to the<br>design of your Job, for example, using tJava or tJavaFlex.<br><br>In order to avoid the inconvenience of writing manually, you<br>could select the variable of interest from the auto-completion list (Ctrl+Space) to fill the current field on<br>condition that this variable has been properly defined.<br><br>For further information about how to use a stream, see [Reading data from a remote file in streaming mode](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfilefetch-tsleep-tlogrow-reading-data-from-remote-file-in-streaming-mode-standard-component-this). |
| File Name | Enter the name or path to the output file.<br><br>This field<br>becomes unavailable once you have selected the Use<br>Output Stream check box.<br><br>For further<br>information about how to define and use a variable in a Job, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables).<br><br>Information noteWarning: Use absolute path (instead of relative path) for<br>this field to avoid possible errors. |
| Sheet name | Enter the name of the XSL sheet.<br><br>Information noteWarning: If a subJob contains<br>multiple tFileOutputExcel components that write the same excel file (that is,<br>the File Name options of these components point to the<br>same file), these components overwrite the same xsl sheet and only the data of<br>the tFileOutputExcel component that is the last one to write the excel file<br>remains. To avoid data lost, make sure that these tFileOutputExcel components<br>are in different subJobs. |
| Include header | Select this check box to include a header row to the output file. |
| Append existing file | Select this check box to add the new lines at the end of the file.<br><br><br>Append existing sheet: Select this check<br>box to add the new lines at the end of the Excel sheet. |
| Is absolute Y pos. | Select this check box to add information in specified cells:<br><br><br>First cell X: cell position on the<br>X-axis (X-coordinate or Abcissa).<br><br><br>First cell Y: cell position on the<br>Y-axis (Y-coordinate).<br><br><br>Keep existing cell format: select this<br>check box to retain the original layout and format of the cell you want to<br>write into. |
| Font | Select in the list the font you want to use. |
| Define all columns auto size | Select this check box if you want the size of all your columns to be defined<br>automatically. Otherwise, select the Auto<br>size check boxes next to the column names you want their size to be<br>defined automatically. |
| Protect file | Select this check box and enter the password in the<br>Password field to protect the file using a password.<br><br>This component encrypts files using agile encryption (which currently uses<br>the AES 128 algorithm). For more information about agile encryption, see [Apache POI - Encryption support](https://poi.apache.org/encryption.html) and [Encryption](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-offcrypto/2d1c4f2c-7a2a-4133-998f-f3373f00d542).<br><br>This option is<br>available when Write excel2007 file format(xlsx) is<br>selected and Use Output Stream is not<br>selected. |
| Schema and Edit Schema | A schema is a row description, it defines the number of fields to be<br>processed and passed on to the next component. The schema is either Built-in or stored remotely in the Repository.<br><br>This component offers the advantage of the<br>dynamic schema feature. This allows you to retrieve unknown columns from source<br>files or to copy batches of columns from a source without mapping each column<br>individually. For further information about dynamic schemas, see [Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema).<br><br>This<br>dynamic schema feature is designed for the purpose of retrieving unknown columns of a<br>table and is recommended to be used for this purpose only; it is not recommended for the<br>use of creating tables.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Create directory if does not exist | This check box is selected by default. This option creates the directory<br>that will hold the output files if it does not already exist. |
| Custom the flush buffer<br>size | Select this check box to set the maximum number of rows in the Row number field that are allowed in the buffer.<br><br>Available when Write excel2007 file<br>format (xlsx) is selected in the Basic settings view. |
| Advanced separator (for numbers) | Select this check box to modify the separators you want to use for<br>numbers:<br><br><br>Thousands separator: define separators<br>for thousands.<br><br><br>Decimal separator: define separators for<br>decimals. |
| Truncate characters exceeding max cell length | Select this option to truncate a string that is more than 32767 characters<br>in length to the maximum length allowed by an cell (that is, 32767 characters)<br>before exporting the string to a cell. This option prevents Job failures caused by<br>exporting large amount of data to single excel cells. Also note that this option<br>may result in data losses.<br><br>This option is for Excel 2007 (and higher versions)<br>files and is available when Write excel2007 file format<br>(xlsx) is selected in the Basic settings<br>view.<br><br>This option is not selected by default. |
| Encoding | Select the encoding type from the list or select Custom and define it manually. This field is compulsory for DB<br>data handling. |
| Don't generate empty file | Select the check box to avoid the generation of an<br>empty file. |
| Recalculate formula | Select this check box if you need to recalculate formula(s) in the specified<br>Excel file.<br><br>This check box appears only when you select all<br>these three check boxes: Write excel2007 file<br>format(xlsx), Append existing<br>file, and Append existing<br>sheet. |
| Streaming append | Select this option to write data to an existing excel2007 file in streaming<br>mode. Select this option when you want to write large volumes of data at limited<br>memory.<br><br>This option preserves existing static formatting of data, however<br>more advanced formatting and validation rules might be cleared when using<br>it.<br><br>This option is available when the Write excel2007 file<br>format (xlsx) option and the Append existing<br>file option are selected in the Basic<br>settings view. |
| Use shared strings table | Select this option to use a shared strings table when creating an XLSX<br>file.<br><br>This option provides a tradeoff between performance and file size. It<br>works fine when creating XLSX files that contain many duplicated strings. It is<br>available when Write excel2007 file format (xlsx) is<br>selected and Append existing file is not selected in the<br>Basic settings view.<br><br>Note that 1904 date<br>format will be ignored if the schema contains a dynamic column and the<br>component works in the memory-consuming mode.<br><br>Information noteNote: This option is available<br>only when you have installed the 8.0.1-R2023-03 Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | Use this component to write an MS Excel file with data passed on from other<br>components using a Row link. |
| Dynamic settings | Click the [+] button to add a row in the<br>table and fill the Code field with a context variable<br>to choose your HDFS connection dynamically from multiple connections planned in your<br>Job. This feature is useful when you need to access files in different HDFS systems or<br>different distributions, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be deployed and<br>executed independent of *Talend Studio*.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |

**Related concepts**

* [Extracting data from an Excel file using a dynamic schema](https://help.qlik.com/talend/en-US/components/8.0/extracting-data-from-excel-file-using-dynamic-schema-c "This scenario extracts data from an Excel 2007 file. It demonstrates the use of dynamic schema.")
