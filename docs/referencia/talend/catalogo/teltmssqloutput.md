# teltmssqloutput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/teltmssqloutput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/teltmssqloutput -->

# tELTMSSqlOutput

Executes the SQL Insert, Update and Delete statement to the MSSql database

The three ELT MSSql components are closely related, in terms of their operating conditions. These components should be used to handle MSSql DB schemas to generate Insert statements, including clauses, which are to be executed in the DB output table defined.

Carries out the action on the table specified and inserts the data according to the output schema defined the ELT Mapper.

## tELTMSSqlOutput Standard properties

These properties are used to configure tELTMSSqlOutput running in the Standard Job framework.

The Standard tELTMSSqlOutput component belongs to the ELT family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Action on data | On the data of the table defined, you can<br>perform the following operation:<br><br><br>Insert: Adds new entries to the table. If duplicates<br>are found, Job stops.<br><br><br>Update: Updates entries in the table.<br><br><br>Delete: Deletes the entries which correspond to the<br>entry flow. |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-in</span>: The schema is created and                            stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already exists                            and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul> |
| Where clauses (for UPDATE and<br>DELETE only) | Enter a clause to filter the data to be updated or deleted<br>during the update or delete operations.<br><br>This field is available when Update or Delete is<br>selected from the Action on data<br>drop-down list and Use WHERE conditions<br>table is not selected. |
| Use WHERE conditions table | Select this option to invoke the Where conditions table table, where you can set filter<br>conditions by providing values in the Column, Function,<br>and Value fields of the Where conditions table.<br><br>This option is available when Update or Delete is<br>selected from the Action on data<br>drop-down list. |
| Where conditions<br>table | Add rows and enter conditions as prompted to filter the data<br>to be updated or deleted during the update or delete operation. A data<br>record is selected for the update or delete operation only when it matches<br>all the conditions set in this table.<br><br>In addition to the commonly used operators (such as =, &gt;=,<br>&lt;&gt;, and so on), the Function column of this table also provides<br>the following operators:<br><br><ul> <li> <span>BETWEEN</span>,                              which filters the data using an interval given in the <span>Value</span> field. The interval needs to                              be in the format of <span>&lt;start&gt; and                                  &lt;end&gt;</span>, for example: <span>10                                      and 20</span>. </li> <li> <span>LIKE</span>, which                              filters the data using a string given in the <span>Value</span> field. The string needs to be                              in the format of <span>sample_string%</span>.</li> <li> <span>IN</span>, which                              filters the data using the elements in a set given in the <span>Value</span> field. The set needs to be in                              the format of <span>(element1, element2, element3,                                  ...)</span>, for example: <span>(1,2,5)</span>.</li> </ul><br><br>This option is available when the Use WHERE conditions table option is selected. |
| Default Table Name | Enter the default table name, between<br>double quotation marks. |
| Default Schema Name | Enter the default schema name,between<br>double quotation marks. |
| Table name from connection name is<br>variable | Select this check box when the name of the connection to this<br>component is set to a variable, such as a context variable. |
| Use different table name | Select this checkbox to define a different output table name,<br>between double quotation marks, in the Table<br>name field which appears. |
| Mapping | Specify the metadata mapping file<br>for the database to be used. The metadata mapping file is used for the data<br>type conversion between database and Java. For more information about the<br>metadata mapping, see the related documentation for Type mapping.<br><br>Information noteNote: You can use Hive mapping to support Databricks Delta<br>Lake. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Authenticate using Azure Active<br>Directory | When selected, this option allows you pick<br>the authentication mode to use from the Azure Active Directory<br>authentication mode dropdown list:<br><br><ul> <li> <span>Service principal (client secret)</span>: use the service                           principal credentials (client ID and client secret) to authenticate.</li> <li> <span>User password</span>: use the Azure Active Directory user                           credentials (username and password) to authenticate.</li> </ul> |
| Use update statement without subqueries | Select this option to generate an UPDATE statement for the MSSql database.<br><br>This option is available when Update is selected from the<br>Action on data dropdown list in the Basic<br>settings view. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at a<br>Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>NB\_LINE\_INSERTED: the number of<br>rows inserted. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>QUERY: the query statement populated by the ELT Map component the<br>component connects to. This is an After variable and it returns a string.<br><br>Information noteNote: This<br>variable is available only when you have installed the R2022-01 Talend Studio<br>Monthly update or a later one delivered by Talend. For<br>more information, check with your administrator.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | tELTMSSqlOutput is to be used along with the tELTMSSqlMap. Note that the Output link to be used with these components must correspond strictly to the syntax of the table name.<br><br>Information noteNote: Note that the ELT components do not handle actual data flow<br>but only schema information. |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |
