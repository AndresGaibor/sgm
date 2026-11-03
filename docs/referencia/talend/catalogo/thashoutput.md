# thashoutput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/thashoutput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/thashoutput -->

# tHashOutput

Loads data to the cache memory to offer high-speed access, facilitating transactions involving a large amount of data.

It should be noted that loading data will consume a lot of memory to store records for each record has an overhead. The number of inputted entries also impacts the usage of memory.

The components of the Technical family are normally hidden from the Palette by default. For more information about how to show them on the Palette, see [Palette settings](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/palette-settings).

Information noteNote: This component cannot be used in ESB use cases.

## tHashOutput Standard properties

These properties are used to configure tHashOutput running in the Standard Job framework.

The Standard tHashOutput component belongs to the Technical family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>schema | <ul> <li> <p>A schema is a row description, it defines the number of fields to                                be processed and passed on to the next component. The schema is                                either built-in or remotely stored in the Repository.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <p>Click <span>Sync columns</span> to retrieve                                the schema from the previous component connected in the Job. </p> <p>This component offers the advantage of the                  dynamic schema feature. This allows you to retrieve unknown columns from source                  files or to copy batches of columns from a source without mapping each column                  individually. For further information about dynamic schemas, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema" target="_blank">Dynamic schema</a>.</p> <p>This            dynamic schema feature is designed for the purpose of retrieving unknown columns of a            table and is recommended to be used for this purpose only; it is not recommended for the            use of creating tables.</p> </li> <li> <p> <span>Built-in</span>: The schema is created                                and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>. </p> </li> <li> <p> <span>Repository</span>: The schema already                                exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>. </p> </li> </ul> |
| Link with a tHashOutput | Select this check box to connect to a tHashOutput component.<br><br>Information noteNote:<br><br>If multiple tHashOutput<br>components are linked in this way, the data loaded to the cache<br>by all of them can be read by a tHashInput component that is linked with any of<br>them. |
| Component list | Drop-down list of available tHashOutput components. |
| Data write model | Drop-down list of available data write modes. |
| Keys management | Drop-down list of available keys management modes.<br><br><ul> <li> <p> <span>Keep all</span>: writes all the                                        data received to the cache memory.</p> </li> <li> <p> <span>Keep first</span>: writes only                                        the first record to the cache memory if multiple records                                        received have the same key value.</p> </li> </ul> |
| Append | Selected by default, this option is designed to append data to the<br>memory in case an iterator exists in the same subJob. If it is<br>unchecked, tHashOutput will clear<br>the memory before loading data to it.<br><br>Information noteNote:<br><br>If Link with a tHashOutput is<br>selected, this check box will be hidden but is always<br>enabled. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component writes data to the cache memory and is closely<br>related to tHashInput. Together,<br>these twin components offer high-speed data access to facilitate<br>transactions involving a massive amount of data. |

**Related concepts**

* [Clearing the memory before loading data to it in case an iterator exists in the same subJob](https://help.qlik.com/talend/en-US/components/8.0/thashoutput-thashinput-tfixedflowinput-tlogrow-clearing-memory-before-loading-data-to-it-in-case-iterator-exists-in-same-subjob-standard-component-in-this)
* [Reading data from the cache memory for high-speed data access](https://help.qlik.com/talend/en-US/components/8.0/thashoutput-thashinput-tfixedflowinput-tfileoutputdelimited-reading-data-from-cache-memory-for-high-speed-data-access-standard-component-the)
