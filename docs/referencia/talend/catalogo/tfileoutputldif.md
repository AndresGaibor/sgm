# tfileoutputldif

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tfileoutputldif  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfileoutputldif -->

# tFileOutputLDIF

Writes or modifies an LDIF file with data separated in respective entries based on the schema defined, or else deletes content from an LDIF file.

tFileOutputLDIF outputs data to an LDIF type of file which can then be loaded into an LDAP directory.

## tFileOutputLDIF Standard properties

These properties are used to configure tFileOutputLDIF running in the Standard Job framework.

The Standard tFileOutputLDIF component belongs to the File family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| File Name | Specify the path to the LDIF output file.<br><br>Information noteWarning: Use absolute path (instead of relative path) for<br>this field to avoid possible errors. |
| Wrap | Specify the number of characters at which the line will be<br>wrapped. |
| Change type | Select a changetype that defines the operation you want to perform<br>on the entries in the output LDIF file.<br><br><ul> <li> <p> <span>Add</span>: the LDAP											operation for adding the entry.</p> </li> <li> <p> <span>Modify</span>: the LDAP											operation for modifying the entry.</p> </li> <li> <p> <span>Delete</span>: the LDAP											operation for deleting the entry.</p> </li> <li> <p> <span>Modrdn</span>: the LDAP											operation for modifying an entry's RDN (Relative											Distinguished Name).</p> </li> <li> <p> <span>Default</span>: the default											LDAP operation.</p> </li> </ul> |
| Multi-Values / Modify Detail | Specify the attributes for multi-value fields when Add or Default is selected from the Change type list or provide the detailed<br>modification information when Modify is selected from the Change type list.<br><br><ul> <li> <p> <span>Column</span>: The <span>Column</span> cells are automatically filled with										the defined schema column names.</p> </li> <li> <p> <span>Operation</span>: Select an										operation to be performed on the corresponding field. This										column is available only when <span>Modify</span> is selected from the <span>Change type</span> list.</p> </li> <li> <p> <span>MultiValue</span>: Select the										check box if the corresponding field is a multi-value										field.</p> </li> <li> <p> <span>Separator</span>: Specify the										value separator in the corresponding multi-value										field.</p> </li> <li> <p> <span>Binary</span>: Select the check										box if the corresponding field represents binary										data.</p> </li> <li> <p> <span>Base64</span>: Select the check										box if the corresponding field should be base-64 encoded.										The base-64 encoded data in the LDIF file is represented by										the <span>::</span> symbol.</p> </li> </ul><br><br>This table is available only when Add, Modify, or<br>Default is selected from the<br>Change type list. |
| Schema and Edit<br>schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Sync columns | Click to synchronize the output file schema with the input file<br>schema. The Sync function only displays once the Row connection is<br>linked with the Output component. |
| Append | Select this check box to add the new rows at the end of the<br>file. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Enforce safe base 64 conversion | Select this check box to enable the safe base-64 encoding. For<br>more detailed information about the safe base-64 encoding, see https://www.ietf.org/rfc/rfc2849.txt. |
| Create directory if not exists | This check box is selected by default. It creates the directory<br>that holds the output delimited file, if it does not already<br>exist. |
| Custom the flush buffer size | Select this check box to specify the number of lines to write<br>before emptying the buffer. |
| Row number | Type in the number of lines to write before emptying the<br>buffer.<br><br>This field is available only when the Custom<br>the flush buffer size check box is selected. |
| Encoding | Select the encoding from the list or select Custom and define it manually. This field is<br>compulsory for DB data handling. |
| Don't generate empty file | Select this check box if you do not want to generate empty<br>files. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a<br>Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used to write an LDIF file with data passed on<br>from an input component using a Row<br>&gt; Main connection. |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |

**Related concepts**

* [Writing data from a database table into an LDIF file](https://help.qlik.com/talend/en-US/components/8.0/tfileoutputldif-tfixedflowinput-tmysqlinput-tmysqloutput-writing-data-from-database-table-into-ldif-file-standard-component-this)
