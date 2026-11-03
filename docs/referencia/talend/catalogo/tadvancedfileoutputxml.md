# tadvancedfileoutputxml

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tadvancedfileoutputxml  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tadvancedfileoutputxml -->

# tAdvancedFileOutputXML

Writes an XML file with separated data values according to an XML tree structure.

tAdvancedFileOutputXML outputs data to an XML type of file and offers an interface to deal with loop and group by elements if needed.

## tAdvancedFileOutputXML Standard properties

These properties are used to configure tAdvancedFileOutputXML running in the Standard Job framework.

The Standard tAdvancedFileOutputXML component belongs to the File and the XML families.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li>Either Built-in or Repository. </li> <li> <span>Built-in</span>: No property data stored                  centrally.</li> <li> <span>Repository</span>: Select the Repository file                  where Properties are stored. The following fields are pre-filled in using fetched                  data.</li> </ul> |
| Use Output Stream | Select this check box process the data flow of interest. Once you have<br>selected it, the Output Stream field<br>displays and you can type in the data flow of interest.<br><br>The<br>data flow to be processed must be added to the flow in order for this component<br>to fetch these data via the corresponding representative variable.<br><br>This variable can be already pre-defined in Talend Studio or provided by the context or the components you are using along with this<br>component; otherwise, you can define it manually and use it according to the<br>design of your Job, for example, using tJava or tJavaFlex.<br><br>In order to avoid the<br>inconvenience of hand writing, you could select the variable of interest from<br>the auto-completion list (Ctrl+Space) to<br>fill the current field on condition that this variable has been properly<br>defined.<br><br>For further information about how to use a<br>stream, see [Reading data from a remote file in streaming mode](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfilefetch-tsleep-tlogrow-reading-data-from-remote-file-in-streaming-mode-standard-component-this). |
| File name | Name or path to the output file and/or the variable to be used.<br><br>This field becomes unavailable once you have selected the<br>Use Output Stream check box.<br><br>For further information about how to define and use a variable<br>in a Job, see [Using contexts and<br>variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |
| Configure XML tree | Opens the dedicated interface to help you set the XML mapping. For details<br>about the interface, see [Defining the XML tree](https://help.qlik.com/talend/en-US/components/8.0/xml-connectors/defining-xml-tree). |
| Schema and Edit Schema | <ul> <li>A schema is a row description, it defines the number of fields that will be                  processed and passed on to the next component. The schema is either built-in or                  remote in the Repository. <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <span>Built-in</span>: The schema will be created                  and stored locally for this component only. For more information about a component                  schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</li> <li> <span>Repository</span>: The schema already exists                  and is stored in the Repository, hence can be reused in various projects and Job                  designs. For more information about a component schema in its <span>Basic                     settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</li> </ul> |
| Sync columns | Click to synchronize the output file schema with the input file schema. The<br>Sync function only displays once the Row connection is linked with the Output<br>component. |
| Append the source xml file | Select this check box to add the new lines at the end of your source XML<br>file. |
| Generate compact file | Select this check box to generate a file that does not have any empty space<br>or line separators. All elements then are presented in a unique line and this will<br>reduce considerably file size. |
| Include DTD or XSL | Select this check box to to add the DOCTYPE declaration, indicating the root<br>element, the access path and the DTD file, or to add the processing instruction,<br>indicating the type of stylesheet used (such as XSL types), along with the access<br>path and file name. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Split output in several files | If the XML file output is big, you can split the file every certain number<br>of rows. |
| Trim data | This check box is activated when you are using the dom4j generation mode.<br>Select this check box to trim the leading or trailing whitespace from the value of<br>a XML element. |
| Create directory only if not exists | This check box is selected by default. It creates a directory to hold the<br>output XML files if required. |
| Create empty element if needed | This box is selected by default. If no column is associated to an XML node,<br>this option will create an open/close tag in place of the expected tag. |
| Create attribute even if its value is<br>NULL | Select this check box to generate XML tag attribute for the associated input<br>column whose value is null. |
| Create attribute even if it is<br>unmapped | Select this check box to generate XML tag attribute for the associated input<br>column that is unmapped. |
| Create associated XSD file | If one of the XML elements is defined as a Namespace element, this option<br>will create the corresponding XSD file.<br><br>This option is available only when the<br>generation mode is set to Slow and memory-consuming<br>(Dom4j) in the Advanced settings<br>tab. |
| Add Document type as node | Select this check box to add column(s) of the Document type as node(s) instead of escaped string(s) in the<br>output XML file.<br><br>This option is available only when the<br>generation mode is set to Slow and memory-consuming<br>(Dom4j) in the Advanced<br>settings tab. |
| Advanced separator (for number) | Select this check box to change the expected data separator.<br><br><br>Thousands separator: define the<br>thousands separator, between inverted commas<br><br><br>Decimal separator: define the decimals<br>separator between inverted commas |
| Generation mode | Select the appropriate generation mode according to your memory<br>availability. The available modes are:<br><br><ul> <li> <span>Slow and memory-consuming                           (Dom4j)</span> <div><span>Information note</span><span>Note:</span> This option allows you to use dom4j to process the XML                           files of high complexity.</div> </li> <li> <span>Fast with low memory                           consumption</span> </li> </ul><br><br>This option is not available if Append the source xml file is selected in the Basic settings view, because in this situation,<br>the generation mode is set automatically as dom4j. |
| Encoding | Select the encoding from the list or select Custom and define it manually.<br>This field is compulsory for DB data handling. |
| Don't generate empty file | Select the check box to avoid the generation of an empty file. |
| Add blank line after XML declaration | This option is selected by default to add a blank line right after the XML<br>declaration in the generated XML file. If not selected, no line is added to the<br>file.<br><br>This option is not available if Generate compact<br>file is selected in the Basic settings<br>view. |
| tStatCatcher Statistics | Select the check box to collect the log data at a Job level as well as at<br>each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | Use this component to write an XML file with data passed on from other<br>components using a Row link. |

**Related concepts**

* [The Append the source XML file feature](https://help.qlik.com/talend/en-US/components/8.0/appending-records-to-xml-file)
* [Creating an XML file using a loop](https://help.qlik.com/talend/en-US/components/8.0/tadvancedfileoutputxml-tfileinputdelimited-creating-xml-file-using-loop-standard-component-the)
