# tsystem

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsystem  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsystem -->

# tSystem

Calls other system processing commands, already up and running in a larger Job.

## tSystem Standard properties

These properties are used to configure tSystem running in the Standard Job framework.

The Standard tSystem component belongs to the System family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Use home directory | Select this check box to change the name and path of a dedicated<br>directory. |
| Use Single Command | When the required command is very simple, to the degree that, for<br>example, only one parameter is used and without space, select this<br>option to activate its Command<br>field. In this field, enter the simple system command. Note that the<br>syntax is not checked.<br><br>Information noteWarning:<br><br><br>*In Windows, the MS-DOS commands do not allow you to<br>pass directly from the current folder to the folder<br>containing the file to be launched. To launch a file, you<br>must therefore use an initial command to change the current<br>folder, then a second one to launch the file* |
| Use Array Command | Select this option to activate its Command field. In this field, enter the system<br>command in array, one parameter per line.<br><br>For example, enter the following command with consecutive spaces<br>in array for<br>Linux:<br><br>```<br><br>"cp"<br>"/temp/source.txt"<br>"/temp/copy  to/"<br><br>``` |
| Standard<br>Output and Error<br>Output | <ul> <li> <p>Select the type of output for the processed data to be transferred								to.</p> </li> <li> <p> <span>to console</span>: data is passed on to								be viewed in the <span>Run</span> view.</p> </li> <li> <p> <span>to global variable</span>: data is								passed on to an output variable linked to the <span>tSystem</span> component.</p> </li> <li> <p> <span>to console and </span> <span>to global variable</span>: data is passed on to								the <span>Run</span> view and to an output								variable linked to the <span>tSystem</span>								component.</p> </li> <li> <p> <span>normal</span>: data is passed on to the								component that comes next. </p> </li> </ul> |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description, it defines the number of fields to be processed and								passed on to the next component. The schema is either <span>Built-in</span> or stored remotely in the									<span>Repository</span>.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <p> Click <span>Sync columns</span> to retrieve								the schema from the preceding component in the Job.</p> </li> <li> <p> <span>Built-in</span>: You create and store the schema locally for								this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and								stored it in the Repository. You can reuse it in various projects								and Job flowcharts. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul> |
| Environment variables | Click the [+] button to add as<br>many global variables as needed.<br><br><br>name: Enter the syntax of the new<br>variable.<br><br><br>value: Enter a value for this<br>variable according to the context. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to collect log data at the component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>OUTPUT: the standard output<br>from a process. This is an After variable and it returns a string.<br><br><br>ERROROUTPUT: the<br>erroneous output from a process. This is an After variable and it returns a<br>string.<br><br><br>EXIT\_VALUE: the exit code from a process. This is an After variable and<br>it returns an integer.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component can typically used for companies which already<br>implemented other applications that they want to integrate into<br>their processing flow through Talend. |
| Connections | Outgoing links (from this component to another):<br><br><br>Row: Main.<br><br><br>Trigger: On Subjob Ok; On Subjob<br>Error; Run if.<br><br>Incoming links (from one component to this one):<br><br><br>Row: Main; Reject; Iterate.<br><br><br>Trigger: On Subjob Ok; On Subjob<br>Error; Run if; On Component Ok; On Component Error; Synchronize;<br>Parallelize.<br><br>For further information regarding connections, see [Using connections in a Job](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/using-connections-in-job). |

**Related concepts**

* [Echoing 'Hello World!'](https://help.qlik.com/talend/en-US/components/8.0/tsystem-echoing-hello-world-standard-component "This scenario is one single component tSystem to execute a system command and shows the results in the Run view \"console\".")
* [Executing an external command with multiple parameters using tSystem](https://help.qlik.com/talend/en-US/components/8.0/executing-cmd-with-multiple-para-using-tsystem-overview "This scenario executes an external command with multiple parameters using the tSystem component. It demonstrates the use of the Use Array Command option of the component. The system command copy {source} {destination} is used for this purpose. The command has two parameters: {source} and {destination}.")
