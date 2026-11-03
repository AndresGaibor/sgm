# tfileinputmail

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tfileinputmail  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfileinputmail -->

# tFileInputMail

Reads the standard key data of a given MIME or MSG email file.

## tFileInputMail Standard properties

These properties are used to configure tFileInputMail running in the Standard Job framework.

The Standard tFileInputMail component belongs to the File family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| File Name | Specify the email file to read and extract data from.<br><br>Information noteWarning: Use absolute path (instead of relative path) for<br>this field to avoid possible errors. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description, it defines the number of fields to                                be processed and passed on to the next component. The schema is                                either <span>Built-in</span> or stored remotely                                in the <span>Repository</span>.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-in</span>: The schema will be                                created and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already                                exists and is stored in the Repository, hence can be reused in                                various projects and Job flowcharts. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul> |
| Mail type | Select a type of email from the drop-down list, either MIME or MSG. |
| Attachment export directory | Specify the directory to which you want to export email<br>attachments. |
| Mail parts | Specify the header fields to extract from the MIME<br>email file specified in the File Name field.<br><br><ul> <li> <p> <span>Column</span>: The <span>Column</span> cells are automatically                           filled with the column names defined in the schema.</p> </li> <li> <p> <span>Mail part</span>: Type                           in the names of the header fields or body parts to be extracted from the                           email file in double quotation marks. Refer to <a href="https://tools.ietf.org/html/rfc4021" target="_blank">https://tools.ietf.org/html/rfc4021</a> for a list of MIME mail header fields. </p> </li> <li> <p> <span>Multi value</span>: Select this                           check box to allow multiple field values.</p> </li> <li> <p> <span>Separator</span>: Enter                           a character as the separators for multiple field values.</p> </li> </ul><br><br>This table appears only when MIME<br>is selected from the Mail type<br>drop-down list. |
| MSG Mail parts | Specify what to extract from the defined MSG email file for each<br>schema column.<br><br><ul> <li> <p> <span>Column</span>: The <span>Column</span> cells are automatically                                        filled with the column name defined in the schema.</p> </li> <li> <p> <span>Mail part</span>: Click each                                        cell and then select an email part to be extracted.</p> </li> </ul><br><br>This table appears only when MSG<br>is selected from the Mail type<br>drop-down list. |
| Die on error | Select this check box to stop the execution of the Job when an<br>error occurs. Clear the check box to skip the row on error and<br>complete the process for error-free rows. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at the<br>Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | EXPORTED\_FILE\_PATH: the directory to<br>export mail attachment. This is a Flow variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component handles flow of data therefore it requires output.<br>It is defined as an intermediary step. |

**Related concepts**

* [Extracting key fields from an email](https://help.qlik.com/talend/en-US/components/8.0/tfileinputmail-tlogrow-extracting-key-fields-from-email-standard-component "This Java scenario describes a two-component Job that extracts some key standard fields and displays the values on the Run console.")
* [Retrieving emails and extracting data from email files](https://help.qlik.com/talend/en-US/components/8.0/component-tfileinputmail-retrive-and-extract-email "This article explains how to retrieve emails and extract data from email files using the tPOP and tFileInputMail components.")
