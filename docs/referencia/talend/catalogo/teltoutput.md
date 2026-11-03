# teltoutput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/teltoutput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/teltoutput -->

# tELTOutput

Carries out the action on the table specified and inserts the data according to the output schema defined in the ELT Mapper.

The three ELT components are closely related, in terms of their operating conditions. These components should be used to handle DB schemas to generate Insert statements, including clauses, which are to be executed in the DB output table defined.

## tELTOutput Standard properties

These properties are used to configure tELTOutput running in the Standard Job framework.

The Standard tELTOutput component belongs to the ELT family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Action on table | Select an operation to be performed on the table defined.<br><br><ul> <li> <p> <span>None</span>: No operation is carried out.</p> </li> <li> <p> <span>Drop and create table</span>: The table is removed            and created again.</p> </li> <li> <p> <span>Create table</span>: The table does not exist and            gets created.</p> </li> <li> <p> <span>Create table if does not exist</span>: The table is            created if it does not exist.</p> </li> <li> <p> <span>Drop table if exist and create</span>: The table is            removed if it already exists and created again.</p> </li> <li> <p> <span>Clear table</span>: The table content is            deleted. You have the possibility to rollback the operation.</p> </li> <li> <p> <span>Truncate table</span>: The table content is            deleted. You do not have the possibility to rollback the operation.</p> </li> </ul> |
| Action on data | On the data of the table defined, you can perform the following operation:<br><br><ul> <li> <p> <span>Insert</span>: Adds new entries to the table. If duplicates are found, Job stops.</p> </li> <li> <p> <span>Update</span>: Updates entries in the table.</p> </li> <li> <p> <span>Delete</span>: Deletes the entries which correspond to the entry flow.</p> </li> </ul> |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description, it defines the number of fields to be processed and passed on to the next component. The schema is either built-in or remotely stored in the Repository.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-in</span>: The schema is created and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul> |
| Where clauses (for UPDATE and<br>DELETE only) | Enter a clause to filter the data to be updated or deleted<br>during the update or delete operations.<br><br>This field is available when Update or Delete is<br>selected from the Action on data<br>drop-down list and Use WHERE conditions<br>table is not selected. |
| Use WHERE conditions table | Select this option to invoke the Where conditions table table, where you can set filter<br>conditions by providing values in the Column, Function,<br>and Value fields of the Where conditions table.<br><br>This option is available when Update or Delete is<br>selected from the Action on data<br>drop-down list. |
| Where conditions<br>table | Add rows and enter conditions as prompted to filter the data<br>to be updated or deleted during the update or delete operation. A data<br>record is selected for the update or delete operation only when it matches<br>all the conditions set in this table.<br><br>In addition to the commonly used operators (such as =, &gt;=,<br>&lt;&gt;, and so on), the Function column of this table also provides<br>the following operators:<br><br><ul> <li> <span>BETWEEN</span>,                              which filters the data using an interval given in the <span>Value</span> field. The interval needs to                              be in the format of <span>&lt;start&gt; and                                  &lt;end&gt;</span>, for example: <span>10                                      and 20</span>. </li> <li> <span>LIKE</span>, which                              filters the data using a string given in the <span>Value</span> field. The string needs to be                              in the format of <span>sample_string%</span>.</li> <li> <span>IN</span>, which                              filters the data using the elements in a set given in the <span>Value</span> field. The set needs to be in                              the format of <span>(element1, element2, element3,                                  ...)</span>, for example: <span>(1,2,5)</span>.</li> </ul><br><br>This option is available when the Use WHERE conditions table option is selected. |
| Default Table Name | Enter the default table name, between double quotation marks. |
| Default Schema Name | Enter the default schema name, between double quotation marks. |
| Table name from connection name is<br>variable | Select this check box when the name of the connection to this<br>component is set to a variable, such as a context variable. |
| Use different table name | Select this check box to define a different output table name, between double quotation marks, in the Table name field which appears. |
| Mapping | Specify the metadata mapping file<br>for the database to be used. The metadata mapping file is used for the data<br>type conversion between database and Java. For more information about the<br>metadata mapping, see the related documentation for Type mapping.<br><br>Information noteNote: You can use Hive mapping to support Databricks Delta<br>Lake. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use update statement without subqueries | Select this option to generate an UPDATE statement for the database.<br><br>This option is available when Update is selected from the Action on data drop-down list in the Basic settings view. |
| Clause SET | Select the column names that will be used to generate the SET<br>clauses.<br><br>SET clauses will not be generated for the columns that are<br>not selected.<br><br>This field appears when Update is selected from the Action on data drop-down list in the Basic settings view. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>NB\_LINE\_INSERTED: the number of<br>rows inserted. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>QUERY: the query statement populated by the ELT Map component the<br>component connects to. This is an After variable and it returns a string.<br><br>Information noteNote: This<br>variable is available only when you have installed the R2022-01 Talend Studio<br>Monthly update or a later one delivered by Talend. For<br>more information, check with your administrator.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | tELTOutput is to be used along with the tELTMap. Note that the Output link to be used with these components must correspond strictly to the syntax of the table name.<br><br>Note that the ELT components do not handle actual data flow but only schema information. |
| Limitation | Avoid using any keyword for the database as the table/column name or using any special character in the table/column name. If you want to, you can enclose the table/column name in a pair of \" to see whether it works. For example, when you want to use the keyword number as an Oracle database column name, you can have the Db Column value in the schema editor set to \"number\". But note that this solution does not always work. |

**Related concepts**

* [Aggregating Snowflake data using ELT components](https://help.qlik.com/talend/en-US/components/8.0/teltinput-teltmap-tsnowflakeinput-tlogrow-aggregating-snowflake-data-using-context-variables-as-table-and-connection-names "This scenario shows you an example of aggregating Snowflake data from two source tables STUDENT and TEACHER to one target table FULLINFO using the ELT components.")
