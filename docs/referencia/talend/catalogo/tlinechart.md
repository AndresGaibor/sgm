# tlinechart

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tlinechart  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tlinechart -->

# tLineChart

Reads data from an input flow and transforms the data into a line chart in a PNG image file to ease technical analysis.

## tLineChart Standard properties

These properties are used to configure tLineChart running in the Standard Job framework.

The Standard tLineChart component belongs to the Business Intelligence family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <div><span>Information note</span><span>Note:</span> <p>The schema of <span>tLineChart</span>									contains three read-only columns named <span>series</span> (string), <span>x</span> (integer), and <span>y</span> (integer) respectively, in a fixed order. The									data in any extra columns will be only passed to the next									component, if any, without being presented in the generated line									chart.</p> </div> </li> <li> <p> <span>Built-in</span>: The schema is created								and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>. </p> </li> <li> <p> <span>Repository</span>: The schema already								exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>. </p> </li> </ul> |
| Sync columns | Click to synchronize the output file schema with the input file<br>schema. The Sync function only displays once the Row connection is linked with the output<br>component. |
| Generated image path | Name and path of the output image file. |
| Chart title | Enter the title of the line chart to be generated. |
| Domain axis label and Range axis<br>label | Enter the domain axis (X axis) and range axis (Y axis)<br>labels. |
| Plot orientation | Select the plot orientation of the range axis: Vertical or Horizontal. |
| Include legend | Select this check box if you want your line chart to include a<br>legend, indicating the lines of different series in different<br>colors. |
| Image width and Image<br>height | Enter the width and height of the image, in pixels. |
| Moving average | Select this check box to show a moving average for each series on<br>your line chart. With this check box selected, the Period field appears, letting you define<br>a period of which you want to show the moving average. |
| Lower bound and Upper<br>bound | Define the lowest and highest values to be displayed on the range<br>axis. |
| Chart background and Plot<br>background | Select the chart background color and the plot area background<br>color. |

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

* [Creating a line chart to ease trend analysis](https://help.qlik.com/talend/en-US/components/8.0/tlinechart-tmap-tfileinputdelimited-tfiledelete-creating-line-chart-to-ease-trend-analysis-standard-component-this)
