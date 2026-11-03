# tldapattributesinput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tldapattributesinput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tldapattributesinput -->

# tLDAPAttributesInput

Analyses each object found via the LDAP query and lists a collection of attributes associated with the object.

tLDAPAttributesInput executes an LDAP query based on the given filter and corresponding to the schema definition. Then it passes on the field list to the next component via a Main row link.

## tLDAPAttributesInput Standard properties

These properties are used to configure tLDAPAttributesInput running in the Standard Job framework.

The Standard tLDAPAttributesInput component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Use an existing connection | Select this check box and click the relevant tLDAPConnection component on the Component list to reuse the connection<br>details you already defined. |
| Host | LDAP Directory server IP address. |
| Port | Listening port number of server. |
| Base DN | Path to user's authorised tree leaf. |
| Protocol | Select the protocol type on the list.<br><br><br>LDAP : no encryption is used<br><br><br>LDAPS: secured LDAP. When this<br>option is chosen, the Advanced CA<br>check box appears. Once selected, the advanced mode allows you to<br>specify the directory and the keystore password of the certificate<br>file for storing a specific CA. However, you can still deactivate<br>this certificate validation by selecting the Trust all certs check box.<br><br><br>TLS: certificate is used. When this<br>option is chosen, the Advanced CA<br>check box appears and is used the same way as that of the LDAPS type. |
| Authentication User and<br>Password | Select the Authentication check<br>box if LDAP login is required. Note that the login must match the<br>LDAP syntax requirement to be valid. e.g.: "cn=Directory<br>Manager".<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Filter | Type in the filter as expected by the LDAP directory db. |
| Multi valued field separator | Type in the value separator in multi-value fields. |
| Alias dereferencing | Select the option on the list. Never<br>improves search performance if you are sure that no alias<br>is to be dereferenced. By default, Always is to be used:<br><br><br>Always: Always dereference<br>aliases<br><br><br>Never: Never dereferences<br>aliases.<br><br><br>Searching:Dereferences aliases only<br>after name resolution.<br><br><br>Finding: Dereferences aliases only<br>during name resolution |
| Referral handling | Select the option on the list:<br><br><br>Ignore: does not handle request<br>redirections<br><br><br>Follow:does handle request<br>redirections |
| Limit | Fill in a limit number of records to be read If needed. |
| Time Limit | Fill in a timeout period for the directory. access |
| Paging | Specify the number of entries returned at a time by the LDAP<br>server. |
| Die on error | This check box is selected by default. Clear the check box to skip<br>the row on error and complete the process for error-free rows. If<br>needed, you can retrieve the rows on error via a Row &gt; Rejects link. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-in</span>: The schema is created								and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already								exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> <div><span>Information note</span><span>Warning:</span> <p> <em> As this component is intended to list the attributes										associated with a LDAP object, its schema is then										pre-defined. You should retain these established columns,										even though you may need to add some new columns. Hence you										should use the Built-in mode.</em> </p> </div> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p>The pre-defined schema lists:</p> <p> - <em>objectclass</em>: list of object classes</p> <p> - <em>mandatoryattributes</em>: list of mandatory								attributes to these classes</p> <p> - <em>optionalattributes</em>: list of optional								attributes to these classes</p> <p> - <em>objectattribute</em>s: list of attributes that								are essential for the analysed object.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Class Definition Root | Specify the root of the object class definition namespace. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a<br>job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>RESULT\_NAME: the<br>name of the current LDAP entry satisfying the search filter. This is a flow variable,<br>and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component covers all possible LDAP queries.<br><br>Note: Press Ctrl + Space bar to<br>access the global variable list, including the GetResultName variable to retrieve automatically the<br>relevant Base |
