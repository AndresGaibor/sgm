# taggregatesortedrow

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/taggregatesortedrow  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/taggregatesortedrow -->

# tAggregateSortedRow

Aggregates the sorted input data for output column based on a set of operations. Each output column is configured with many rows as required, the operations to be carried out and the input column from which the data will be taken for better data aggregation.

## tAggregateSortedRow Standard properties

These properties are used to configure tAggregateSortedRow running in the Standard Job framework.

The Standard tAggregateSortedRow component belongs to the Processing family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description, it defines the number of fields to                                be processed and passed on to the next component. The schema is                                either <span>Built-in</span> or stored remotely                                in the <span>Repository</span>.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <p>Click <span>Sync columns</span> to retrieve                                the schema from the previous component connected in the Job.</p> <p>This component offers the advantage of the                  dynamic schema feature. This allows you to retrieve unknown columns from source                  files or to copy batches of columns from a source without mapping each column                  individually. For further information about dynamic schemas, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema" target="_blank">Dynamic schema</a>.</p> <p>This            dynamic schema feature is designed for the purpose of retrieving unknown columns of a            table and is recommended to be used for this purpose only; it is not recommended for the            use of creating tables.</p> </li> <li> <p> <span>Built-in</span>: The schema will be                                created and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already                                exists and is stored in the Repository, hence can be reused in                                various projects and Job flowcharts. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul> |
| Input rows count | Specify the number of rows that are sent to the tAggregateSortedRow component.<br><br>Information noteNote:<br><br>If you specified a Limit for<br>the number of rows to be processed in the input component, you<br>will have to use that same limit in the Input rows count field. |
| Group by | <ul> <li> <p>Define the aggregation sets, the values of which will be used for                                calculations.</p> </li> <li> <p> <span>Output Column</span>: Select the column                                label in the list offered based on the schema structure you defined.                                You can add as many output columns as you wish to make more precise                                aggregations. </p> <p>Ex: Select Country to calculate an average of values for each                                country of a list or select Country and Region if you want to                                compare one country's regions with another country' regions.</p> </li> <li> <p> <span>Input Column</span>: Match the input                                column label with your output columns, in case the output label of                                the aggregation set needs to be different.</p> </li> </ul> |
| Operations | <ul> <li> <p>Select the type of operation along with the value to use for the                                calculation and the output field.</p> </li> <li> <p> <span>Output Column</span>: Select the                                destination field in the list.</p> <div> <span>Function</span>: Select the operator among:                        <ul> <li> <p> <span>count</span>: calculates the number of rows</p> </li> <li> <p> <span>min</span>: selects the minimum value</p> </li> <li> <p> <span>max</span>: selects the maximum value</p> </li> <li> <p> <span>avg</span>: calculates the average</p> </li> <li> <p> <span>sum</span>: calculates the sum</p> </li> <li> <p> <span>first</span>: returns the first value</p> </li> <li> <p> <span>last</span>: returns the last value</p> </li> <li> <p> <span>list</span>: lists values of an aggregation by multiple keys.</p> </li> <li> <p> <span>list (object)</span>: lists Java values of an aggregation by multiple keys</p> </li> <li> <p> <span>count (distinct)</span>: counts the number of the distinct rows</p> </li> <li> <p> <span>standard deviation</span>: calculates the                                    variability of a set of value.</p> </li> <li> <p> <span>union (geometry)</span>: makes the union of a set of Geometry objects</p> </li> <li> <span>population standard deviation</span>: calculates the                                spread of a data distribution. Use this function if the data to be                                calculated is considered a population on its own. This calculation                                supports 39 decimal places.</li> <li> <span>sample                                    standard deviation</span>: calculates the spread of a data                                distribution. Use this function if the data to be calculated is                                considered a sample from a larger population. This calculation                                supports 39 decimal places.</li> </ul></div> </li> <li> <p> <span>Input column</span>: Select the input                                column from which the values are taken to be aggregated.</p> </li> <li> <p> <span>Ignore null values</span>: Select the                                check boxes corresponding to the names of the columns for which you                                want the NULL value to be ignored.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Check this box to collect the log data at component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component handles flow of data therefore it requires input<br>and output, hence is defined as an intermediary step. |

**Related concepts**

* [Sorting and aggregating the input data](https://help.qlik.com/talend/en-US/components/8.0/tsortrow-taggregatesortedrow-tlogrow-tfixedflowinput-sorting-and-aggregating-input-data-standard-component-this)
