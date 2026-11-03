# tldapoutput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tldapoutput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tldapoutput -->

# tLDAPOutput

Executes an LDAP query based on the given filter and corresponding to the schema definition. Then it passes on the field list to the next component via a Row &gt; Main link.

## tLDAPOutput Standard properties

These properties are used to configure tLDAPOutput running in the Standard Job framework.

The Standard tLDAPOutput component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| ![](https://help.qlik.com/talend/en-US/components/Resources/images/Save_Icon.png) | Click this icon to open a database connection wizard and store the<br>database connection parameters you set in the component Basic settings view.<br><br>For more information about setting up and storing database<br>connection parameters, see [Centralizing database metadata](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/centralizing-database-metadata). |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Note that when a Job contains the parent Job and the child Job,<br>Component List presents only the<br>connection components in the same Job level. |
| Host | LDAP Directory server IP address. |
| Port | Listening port number of server. |
| Base DN | Path to user's authorized tree leaf. |
| Protocol | Select the protocol type on the list.<br><br><br>LDAP : no encryption is used<br><br><br>LDAPS: secured LDAP. When this<br>option is chosen, the Advanced CA<br>check box appears. Once selected, the advanced mode allows you to<br>specify the directory and the keystore password of the certificate<br>file for storing a specific CA. However, you can still deactivate<br>this certificate validation by selecting the Trust all certs check box.<br><br><br>TLS: certificate is used When this<br>option is chosen, the Advanced CA<br>check box appears and is used the same way as that of the LDAPS type. |
| User and Password | Fill in the User and Password as required by the<br>directory<br><br>Note that the login must match the LDAP syntax requirement to be<br>valid. e.g.: "cn=Directory Manager".<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Multi valued field separator | Type in the value separator in multi-value fields. |
| Alias dereferencing | Select the option on the list. Never improves search performance if you are sure<br>that no aliases is to be dereferenced. By default, Always is to be used:<br><br><br>Always: Always dereference<br>aliases<br><br><br>Never: Never dereferences<br>aliases.<br><br><br>Searching:Dereferences aliases only<br>after name resolution.<br><br><br>Finding: Dereferences aliases only<br>during name resolution |
| Referral handling | Select the option on the list:<br><br><br>Ignore: does not handle request<br>redirections<br><br><br>Follow:does handle request<br>redirections |
| Insert mode | Select the editing mode on the list:<br><br><br>Add: add a value in a multi-value<br>attribute,<br><br><br>Insert: insert new data,<br><br><br>Update: updates the existing<br>data,<br><br><br>Delete: remove the selected data<br>from the directory,<br><br><br>Insert or<br>update: Insert a new record. If the record with the given reference<br>already exists, an update would be made.<br><br>Information noteWarning:<br><br>When Update is selected, you<br>must go to the Advanced<br>settings view, and select the Use Attribute Options (for update<br>mode) check box to show the Attribute Options table. Then, select the<br>attribute to update under the Attribute<br>name part and the choose Replace under the Option part. |
| DN Column Name | Select in the list the type of the LDAP input entity used. |
| Schema and Edit<br>schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Die on error | This check box is selected by default. Clear the check box to skip<br>the row on error and complete the process for error-free rows. If<br>needed, you can retrieve the rows on error via a Row &gt; Reject link. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use Attribute Options (for update mode) | Select this check box to choose the desired attribute (including<br>dn, dc, ou, objectClass, mail and uid) and the corresponding<br>operation (including Add, Replace, Remove Attribute and Remove<br>Value). |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a<br>job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>NB\_LINE\_REJECTED: the number of rows rejected. This is an After<br>variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component covers all possible LDAP queries.<br><br>Note: Press Ctrl + Space bar to<br>access the global variable list, including the GetResultName variable to retrieve the relevant DN<br>Base automatically. This component allows you to carry out actions<br>on a table or on the data of a table in an database. It also allows<br>you to create a reject flow using a Row &gt;<br>Rejects link to filter data in error. For an example<br>of tMysqlOutput in use, see [Retrieving data in error with a Reject link](https://help.qlik.com/talend/en-US/components/8.0/mysql/tmysqloutput-tmap-tfileoutputdelimited-tfileinputdelimited-retrieving-data-in-error-with-reject-link-standard-component-this). |

**Related concepts**

* [Editing data in a LDAP directory](https://help.qlik.com/talend/en-US/components/8.0/tldapinput-tldapoutput-tmap-tlogrow-editing-data-in-ldap-directory-standard-component-all-of)
