# txslt

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/txslt  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/txslt -->

# tXSLT

Helps to transform data structure to another structure.

This component refers to an XSL stylesheet, to transform an XML source file into a defined output file.

## tXSLT Standard properties

These properties are used to configure tXSLT running in the Standard Job framework.

The Standard tXSLT component belongs to the XML family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| XML file/stream | File path to the XML file or data flow to be validated. Note<br>that in the case of stream, the data must be added to the flow for the<br>component to fetch the data through the corresponding variable.<br><br>The data flow to be processed must be added to the flow in<br>order for this component to fetch these data via the corresponding<br>representative variable.<br><br>This variable can be already pre-defined in Talend Studio or provided by the context or the components you are using along with this<br>component; otherwise, you can define it manually and use it according to the<br>design of your Job, for example, using tJava or tJavaFlex.<br><br>In order to avoid the inconvenience of hand writing, you could<br>select the variable of interest from the auto-completion list (Ctrl+Space) to fill the current field on<br>condition that this variable has been properly defined.<br><br>For further information about how to use a stream, see [Reading data from a remote file in streaming mode](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfilefetch-tsleep-tlogrow-reading-data-from-remote-file-in-streaming-mode-standard-component-this).<br><br>Information noteNote: This field is not available if you select the Use column instead<br>of file/stream for XML option. |
| XSL file/stream | File path to the reference XSL transformation file or<br>transformation data flow. Note that in the case of stream, the data must be<br>added to the flow for the component to fetch the data through the corresponding<br>variable.<br><br>The data flow to be processed must be added to the flow in order for this<br>component to fetch these data via the corresponding representative<br>variable.<br><br>This variable can be already pre-defined in Talend Studio or provided by the context or the components you are using along with this<br>component; otherwise, you can define it manually and use it according to the<br>design of your Job, for example, using tJava or<br>tJavaFlex.<br><br>In order to avoid the inconvenience of hand writing, you could<br>select the variable of interest from the auto-completion list<br>(Ctrl+Space) to fill the<br>current field on condition that this variable has been properly<br>defined.<br><br>For further information about how to use a stream, see [Reading data from a remote file in streaming mode](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfilefetch-tsleep-tlogrow-reading-data-from-remote-file-in-streaming-mode-standard-component-this).<br><br>Information noteNote: This field is not available if you select the Use column instead<br>of file/stream for XSL option. |
| Output file | File path to the output file. If the file does not exist, it will<br>be created. The output file can be any structured or unstructured<br>file such as html, xml, txt or even pdf or edifact depending on your<br>xsl.<br><br>Information noteNote: This field is not available if you select the Use column instead<br>of File for Result option. |
| Parameters | Click the plus button to add new lines in the Parameters list and define the<br>transformation parameters of the XSLT file. Click in each line and<br>enter the key in the *name* list and its<br>associated value in the *value* list. |
| Use column instead of file/stream for XML | Select this option to use the data of a specified column as the input. You need to specify the column to which the input data is passed to in the Input column for XML drop-down list. |
| Use column instead of file/stream for XSL | Select this option to use the data of a specified column as the XSL. You need to specify the column to which the XSL data is passed to in the Input column for XSL drop-down list. |
| Use column instead of File for Result | Select this option to output the transformed data to a specified column. You need to specify the<br>column to which the transformed data is passed to in the Input<br>column for result drop-down list. |
| Schema and Edit<br>Schema | A schema is a row description, it defines the<br>number of fields to be processed and passed on to the next component. The<br>schema is either Built-in or stored remotely in the Repository.<br><br><ul> <li> <span>Built-in</span>: The schema will be created and stored locally for                        this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</li> <li> <span>Repository</span>: The schema already exists and is stored in the                        Repository, hence can be reused in various projects and Job flowcharts. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</li> </ul><br><br>This component offers the advantage of the<br>dynamic schema feature. This allows you to retrieve unknown columns from source<br>files or to copy batches of columns from a source without mapping each column<br>individually. For further information about dynamic schemas, see [Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema).<br><br>This<br>dynamic schema feature is designed for the purpose of retrieving unknown columns of a<br>table and is recommended to be used for this purpose only; it is not recommended for the<br>use of creating tables.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Sync columns | Click to synchronize the output file schema with the input file<br>schema. The Sync function only displays once the Row connection is<br>linked with the Output component. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to gather the processing metadata at the Job<br>level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>OUTPUT\_FILEPATH: the output file path. This is a Flow variable and it<br>returns a string.<br><br><br>OUTPUT\_FILENAME: the output file name. This is a Flow<br>variable and it returns a string.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component can be used as standalone component. |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |

**Related concepts**

* [Transforming stream into HTML using an XSL stylesheet](https://help.qlik.com/talend/en-US/components/8.0/transforming-stream-to-html-using-xsl-stylesheet-standard-component "The tXSLT component provides support for streams. It can receive XML files or XSL files passed to it in the form of stream and, in addition to sending the output to files, it can send the output to the subsequent component through a Row > Main connection. The tXSLT component in this scenario receives the XML file from a tFileInputRaw component in the form of stream and sends its output to a tLogRow component through a predefined column.")
* [Transforming XML into HTML using an XSL stylesheet](https://help.qlik.com/talend/en-US/components/8.0/txslt-tmsgbox-transforming-xml-to-html-using-xsl-stylesheet-standard-component "This scenario describes a two-component Job that converts XML data into an HTML document using an XSL stylesheet. It also defines a transformation parameter of the XSL stylesheet to change the background color of the header of the HTML document created.")
