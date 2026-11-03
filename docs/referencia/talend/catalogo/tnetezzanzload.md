# tnetezzanzload

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tnetezzanzload  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tnetezzanzload -->

# tNetezzaNzLoad

Inserts data into a Netezza database table using Netezza's nzload utility.

tNetezzaNzLoad bulk loads data into a Netezza table either from an existing data file, an input flow, or directly from a data flow in streaming mode through a named-pipe.

## tNetezzaNzLoad Standard properties

These properties are used to configure tNetezzaNzLoad running in the Standard Job framework.

The Standard tNetezzaNzLoad component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Host | Database server IP address. |
| Port | Listening port number of the DB server. |
| Database | Name of the Netezza database. |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | Name of the table into which the data is to be inserted. |
| Action on table | On the table defined, you can perform one of the following<br>operations before loading the data:<br><br><br>None: No operation is carried<br>out.<br><br><br>Drop and create a table: The table<br>is removed and created again.<br><br><br>Create a table: The table does not<br>exist and gets created.<br><br><br>Create table if not exists: The<br>table is created if it does not exist.<br><br><br>Drop table if exists and create:<br>The table is removed if it already exists and created again.<br><br><br>Clear table: The table content is<br>deleted before the data is loaded.<br><br><br>Truncate table: executes a truncate<br>statement prior to loading the data to clear the entire content of<br>the table. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Data file | Full path to the data file to be used. If this component is used<br>on its own (not connected to another component with input flow) then<br>this is the name of an existing data file to be loaded into the<br>database. If it is connected, with an input flow to another<br>component; this is the name of the file to be generated and written<br>with the incoming data to later be used with nzload to load into the<br>database. |
| Use named-pipe | Select this check box to use a named-pipe instead of a data file.<br>This option can only be used when the component is connected with an<br>input flow to another component. When the check box is selected, no<br>data file is generated and the data is transferred to nzload through<br>a named-pipe. This option greatly improves performance in both Linux<br>and Windows.<br><br>Information noteNote:<br><br>This component on named-pipe mode uses a JNI interface to<br>create and write to a named-pipe on any Windows platform. Therefore the path<br>to the associated JNI DLL must be configured inside the java library path.<br>The component comes with two DLLs for both 32 and 64 bit operating systems<br>that are automatically provided in Talend Studio with the component. |
| Named-pipe name | Specify a name for the named-pipe to be used. Ensure that the name<br>entered is valid. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional JDBC parameters for the<br>database connection created. |
| Use existing control file | Select this check box to provide a control file to be<br>used with the nzload utility instead of specifying all the options<br>explicitly in the component. When this check box is selected, Data file and the other nzload related<br>options no longer apply. Please refer to Netezza's nzload manual for<br>details on creating a control file.<br><br>Information noteNote:<br><br>The global variable NB\_LINE is not supported<br>when any control file is being used. |
| Control file | Enter the path to the control file to be used, between double<br>quotation marks, or click [...] and<br>browse to the control file. This option is passed on to the nzload<br>utility via the *-cf* argument. |
| Field separator | Character, string or regular expression used to separate<br>fields.<br><br>Information noteWarning:<br><br><br>*This is nzload's delim argument. If you<br>do not use the Wrap quotes around<br>fields option, you must make sure that the<br>delimiter is not included in the data that's inserted to the<br>database. The default value is \t or TAB. To improve<br>performance, use the default value.* |
| Wrap quotes around fields | This option is only applied to columns of<br>*String*, *Byte*,<br>*Byte[]*, *Char*, and<br>*Object* types. Select either:<br><br><br>None: do not wrap column values in<br>quotation marks.<br><br><br>Single quote: wrap column values in<br>single quotation marks.<br><br><br>Double quote: wrap column values in<br>double quotation marks.<br><br>Information noteWarning:<br><br><br>*If using the Single quote or Double<br>quoteoption, it is necessary to use \ as the<br>Escape char.* |
| Advanced options | Set the nzload arguments in the corresponding table. Click<br>[+] as many times as required<br>to add arguments to the table. Click the Parameter field and choose among the arguments from<br>the list. Then click the corresponding Value field and enter a value between quotation<br>marks.<br><br>For details about the available parameters, see [Parameters](https://help.qlik.com/talend/en-US/components/8.0/tnetezzanzload). |
| Encoding | Select the encoding type from the list. |
| Specify nzload path | Select this check box to specify the full path to the nzload<br>executable. You must check this option if the nzload path is not<br>specified in the PATH environment variable. |
| Full path to nzload executable | Full path to the nzload executable on the machine in use. It is<br>advisable to specify the nzload path in the PATH environment<br>variable instead of selecting this option. |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level. |
| Enable parallel execution | Select this check box to perform high-speed data processing, by treating<br>multiple data flows simultaneously. Note that this feature depends on the database or<br>the application ability to handle multiple inserts in parallel as well as the number of<br>CPU affected. In the Number of parallel executions<br>field, either:<br><br><ul> <li>Enter the number of parallel executions desired.</li> <li>Press <span>Ctrl+Space</span> and select               the appropriate context variable from the list. For further information about context               variables, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables" target="_blank">Using contexts and variables</a>. </li> </ul><br><br>Note that when parallel execution is enabled, it is not possible to use global<br>variables to retrieve return values in a subJob.<br><br>Information noteWarning:<br><br><ul><li>						            The <span>Action on							table</span> field is not available with the							parallelization function. Therefore, you must use a <span>tCreateTable</span> component if you							want to create a table. 					          </li><li>						            When parallel execution is enabled, it is not							possible to use global variables to retrieve return values in a							subJob.					          </li> </ul> |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is mainly used when non particular transformation<br>is required on the data to be loaded ont to the database.<br><br>This component can be used as a standalone or an output<br>component. |

## Parameters

The following table lists the parameters you can use in the Advanced options table in the Advanced settings tab.

| -If | Name of the log file to generate. The logs will be appended if the<br>log file already exists. If the parameter is not specified, the<br>default name for the log file is<br>'*&lt;table\_name&gt;.&lt;db\_name&gt;.nzlog*'.<br>And it's generated under the current working directory where the job<br>is running. |
| --- | --- |
| -bf | Name of the bad file to generate. The bad file contains all the<br>records that could not be loaded due to an internal Netezza error.<br>The records will be appended if the bad file already exists. If the<br>parameter is not specified, the default name for the bad file is<br>'*&lt;table\_name&gt;.&lt;db\_name&gt;.nzbad*'.<br>And it's generated under the current working directory where the job<br>is running. |
| -ouputDir | Directory path to where the log and the bad file are generated. If<br>the parameter is not specified the files are generated under the<br>current directory where the Job is currently running. |
| -logFileSize | Maximum size for the log file. The value is in MB. The default<br>value is 2000 or 2GB. To save hard disk space, specify a smaller<br>amount if your Job runs often. |
| -compress | Specify this option if the data file is compressed. Valid values<br>are "TRUE" or "FALSE". Default value if "FALSE".<br><br>This option is only valid if this component is used by itself<br>and not connected to another component via an input flow. |
| -skipRows &lt;n&gt; | Number of rows to skip from the beginning of the data file. Set<br>the value to "1" if you like to skip the header row from the data<br>file. The default value is "0".<br><br>This option should only be used if this component is used by<br>itself and not connected to another component via an input<br>flow. |
| -maxRows &lt;n&gt; | Maximum number of rows to load from the data file.<br><br>This option should only be used if this component is used by<br>itself and not connected to another component via an input<br>flow. |
| -maxErrors | Maximum number of error records to allow before terminating the<br>load process. The default value is "1". |
| -ignoreZero | Binary zero bytes in the input data will generate errors. Set this<br>option to "NO" to generate error or to "YES" to ignore zero bytes.<br>The default value is "NO". |
| -requireQuotes | This option requires all the values to be wrapped in quotes. The<br>default value is "FALSE".<br><br>This option currently does not work with input flow. Use this<br>option only in standalone mode with an existing file. |
| -nullValue &lt;token&gt; | Specify the token to indicate a null value in the data file. The<br>default value is "NULL". To improve slightly performance you can set<br>this value to an empty field by specifying the value as single<br>quotes: "\'\'". |
| -fillRecord | Treat missing trailing input fields as null. You do not need to<br>specify a value for this option in the value field of the table.<br>This option is not turned on by default, therefore input fields must<br>match exactly all the columns of the table by default.<br><br>Trailing input fields must be nullable in the database. |
| -ctrlChar | Accept control chars in char/varchar fields (must escape NUL, CR<br>and LF). You do not need to specify a value for this option in the<br>value field of the table. This option is turned off by<br>default. |
| -ctInString | Accept un-escaped CR in char/varchar fields (LF becomes only end<br>of row). You do not need to specify a value for this option in the<br>value field of the table. This option is turned off by<br>default. |
| -truncString | Truncate any string value that exceeds its declared char/varchar<br>storage. You do not need to specify a value for this option in the<br>value field of the table. This option is turned off by<br>default. |
| -dateStyle | Specify the date format in which the input data is written in.<br>Valid values are: "YMD", "Y2MD", "DMY", "DMY2", "MDY", "MDY2",<br>"MONDY", "MONDY2". The default value is "YMD".<br><br>The date format of the column in the component's schema must<br>match the value specified here. For example if you want to load<br>a DATE column, specify the date format in the component schema<br>as "yyyy-MM-dd" and the -dateStyle option as "YMD".<br><br>For more description on loading date and time fields, see [Loading DATE, TIME and TIMESTAMP columns](https://help.qlik.com/talend/en-US/components/8.0/tnetezzanzload). |
| -dateDelim | Delimiter character between date parts. The default value is "-"<br>for all date styles except for "MONDY[2]" which is " " (empty<br>space).<br><br>The date format of the column in the component's schema must<br>match the value specified here. |
| -y2Base | First year expressible using two digit year (Y2) dateStyle. |
| -timeStyle | Specify the time format in which the input data is written in.<br>Valid values are: "24HOUR" and "12HOUR". The default value is<br>"24HOUR". For slightly better performance you should keep the<br>default value.<br><br>The time format of the column in the component's schema must<br>match the value specified here. For example if you want to load<br>a TIME column, specify the date format in the component schema<br>as "HH:mm:ss" and the -timeStyle option as "24HOUR".<br><br>For more description on loading date and time fields, see [Loading DATE, TIME and TIMESTAMP columns](https://help.qlik.com/talend/en-US/components/8.0/tnetezzanzload). |
| -timeDelim | Delimiter character between time parts. The default value is ":".<br><br>Information noteNote:<br><br>The time format of the column in the component's schema must<br>match the value specified here. |
| -timeRoundNanos | Allow but round non-zero digits with smaller than microsecond<br>resolution. |
| -boolStyle | Specify the format in which Boolean data is written in the data.<br>The valid values are: "1\_0", "T\_F", "Y\_N", "TRUE\_FALSE", "YES". The<br>default value is "1\_0". For slightly better performance keep the<br>default value. |
| -allowRelay | Allow load to continue after one or more SPU reset or failed over.<br>The default behaviour is not allowed. |
| -allowRelay &lt;n&gt; | Specify number of allowable continuation of a load. Default value<br>is "1". |

## Loading DATE, TIME and TIMESTAMP columns

When this component is used with an input flow, the date format specified inside the component's schema must match the value specified for -dateStyle, -dateDelim, -timeStyle, and -timeDelim options.

| DB Type | Schema date format | -dateStyle | -dateDelim | -timeStyle | -timeDelim |
| --- | --- | --- | --- | --- | --- |
| DATE | "yyyy-MM-dd" | "YMD" | "-" | n/a | n/a |
| TIME | "HH:mm:ss" | n/a | n/a | "24HOUR" | ":" |
| TIMESTAMP | "yyyy-MM-dd HH:mm:ss" | "YMD" | "-" | "24HOUR" | ":" |
