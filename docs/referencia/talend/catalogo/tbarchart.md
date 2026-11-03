# tbarchart

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tbarchart  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tbarchart -->

# tBarChart

Generates a bar chart from the input data to ease technical analysis.

tBarChart reads data from an input flow and transforms the data into a bar chart in a PNG image file.

## tBarChart Standard properties

These properties are used to configure tBarChart running in the Standard Job framework.

The Standard tBarChart component belongs to the Business Intelligence family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <div><span>Information note</span><span>Note:</span> <p>The schema of <span>tBarChart</span>									contains three read-only columns named <span>series</span> (string), <span>category</span> (string), and <span>value</span> (integer) respectively, in a fixed order.									The data in any extra columns will be only passed to the next									component, if any, without being presented in the bar									chart.</p> </div> </li> <li> <p> <span>Built-in</span>: The schema is created								and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>. </p> </li> <li> <p> <span>Repository</span>: The schema already								exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>. </p> </li> </ul> |
| Sync columns | Click to synchronize the output file schema with the input file<br>schema. The Sync function only displays once the Row connection is linked with the output<br>component. |
| Generated image path | Name and path of the output image file. |
| Chart title | Enter the title of the bar chart to be generated. |
| Include legend | Select this check box if you want the bar chart to include a<br>legend, indicating all series in different colors. |
| 3Dimensions | Select this check box to create an image with 3D effect. By<br>default, this check box is selected and the bars representing the<br>series of each category will be stacked one over another. If this<br>check box is cleared, a 2D image will be created, with the bars<br>displayed one besides another along the category axis. |
| Image width and Image<br>height | Enter the width and height of the image file, in pixels. |
| Category axis name and Value axis<br>name | Enter the category axis name and value axis name. |
| Foreground alpha | Enter an integer in the range of *0* to<br>*100* to define the transparency of the<br>image. The smaller the number you enter, the more transparent the<br>image will be. |
| Plot orientation | Select the plot orientation of the bar chart: VERTICAL or HORIZONTAL. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStat<br>Catcher Statistics | Select this check box to collect log data at the component<br>level. |
| Enable parallel execution | Select this check box to perform high-speed data processing, by treating<br>multiple data flows simultaneously. Note that this feature depends on the database or<br>the application ability to handle multiple inserts in parallel as well as the number of<br>CPU affected. In the Number of parallel executions<br>field, either:<br><br><ul> <li>Enter the number of parallel executions desired.</li> <li>Press <span>Ctrl+Space</span> and select               the appropriate context variable from the list. For further information about context               variables, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables" target="_blank">Using contexts and variables</a>. </li> </ul><br><br><ul><li>						            The <span>Action on							table</span> field is not available with the							parallelization function. Therefore, you must use a <span>tCreateTable</span> component if you							want to create a table. 					          </li><li>						            When parallel execution is enabled, it is not							possible to use global variables to retrieve return values in a							subJob.					          </li> </ul> |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is mainly used as Output component. It requires an<br>Input component and Row main link<br>as input. |

**Related concepts**

* [Creating a bar chart from the input data](https://help.qlik.com/talend/en-US/components/8.0/tbarchart-tmap-tfileoutputdelimited-tpostjob-creating-bar-chart-from-input-data-standard-component-this)
