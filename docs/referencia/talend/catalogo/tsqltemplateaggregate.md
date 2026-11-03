# tsqltemplateaggregate

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsqltemplateaggregate  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsqltemplateaggregate -->

# tSQLTemplateAggregate

Provides a set of matrix based on values or calculations.

tSQLTemplateAggregate collects data values from one or more columns with the intent to manage the collection as a single unit. This component has real-time capabilities since it runs the data transformation on the DBMS itself.

## tSQLTemplateAggregate Standard properties

These properties are used to configure tSQLTemplateAggregate running in the Standard Job framework.

The Standard tSQLTemplateAggregate component belongs to the ELT family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Database Type | Select the database type you want to connect to from the<br>list. |
| Component List | Select the relevant DB connection component in the list if you use<br>more than one connection in the current Job. |
| Database name | Name of the database. |
| Source table name | Name of the table holding the data you want to collect values<br>from. |
| Target table name | Name of the table you want to write the collected and transformed<br>data in. |
| Schema and Edit<br>schema | <ul> <li> <p>A schema is a row description, that is to say, it defines the								number of fields that will be processed and passed on to the next								component. The schema is either built-in or remote in the								Repository. </p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-in</span>: You create and store								the schema locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: You have already								created the schema and stored it in the Repository. You can reuse it								in various projects and Job flowcharts. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul> |
| Operations | <ul> <li> <p>Select the type of operation along with the value to use for the								calculation and the output field.</p> </li> <li> <p> <span>Output Column</span>: Select the								destination field in the list.</p> </li> <li> <p> <span>Function</span>: Select any of the								following operations to perform on data: <span>count</span>, <span>min</span>,									<span>max</span>, <span>avg</span>, <span>sum</span>, and									<span>count</span> <span>									(distinct)</span>.</p> </li> <li> <p> <span>Input column position</span>: Select the								input column from which you want to collect the values to be								aggregated.</p> </li> </ul> |
| Group by | <ul> <li> <p>Define the aggregation sets, the values of which will be used for								calculations.</p> </li> <li> <p> <span>Output Column</span>: Select the column								label in the list offered according to the schema structure you								defined. You can add as many output columns as you wish to make more								precise aggregations.</p> </li> <li> <p> <span>Input Column position</span>: Match the								input column label with your output columns, in case the output								label of the aggregation set needs to be different.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a<br>Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>QUERY: the query statement<br>being processed. This is a Flow variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate component with other<br>relevant DB components, especially the DB connection and commit<br>components. |
| SQL Template | SQL Template List |

**Related concepts**

* [Filtering and aggregating table columns directly on the DBMS](https://help.qlik.com/talend/en-US/components/8.0/tsqltemplatefiltercolumns-tsqltemplatefilterrows-tsqltemplatecommit-tmysqlconnection-filtering-and-aggregating-table-columns-directly-on-dbms-standard-component-the)
