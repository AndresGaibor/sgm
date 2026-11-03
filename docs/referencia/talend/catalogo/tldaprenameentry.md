# tldaprenameentry

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tldaprenameentry  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tldaprenameentry -->

# tLDAPRenameEntry

Renames ones or more entries in a specific LDAP directory.

## tLDAPRenameEntry Standard properties

These properties are used to configure tLDAPRenameEntry running in the Standard Job framework.

The Standard tLDAPRenameEntry component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Use an existing connection | Select this check box and click the relevant tLDAPConnection component on the Component list to reuse the connection<br>details you already defined. |
| Host | LDAP directory server IP address. |
| Port | Number of the listening port of the server. |
| Base DN | Path to user's authorized tree leaf. |
| Protocol | Select the protocol type on the list.<br><br><br>LDAP: no encryption is used,<br><br><br>LDAPS: secured LDAP. When this<br>option is chosen, the Advanced CA<br>check box appears. Once selected, the advanced mode allows you to<br>specify the directory and the keystore password of the certificate<br>file for storing a specific CA. However, you can still deactivate<br>this certificate validation by selecting the Trust all certs check box.<br><br><br>TLS: certificate is used. When this<br>option is chosen, the Advanced CA<br>check box appears and is used the same way as that of the LDAPS type. |
| User and Password | Fill in user authentication information.<br><br>Note that the login must match the LDAP syntax requirement to be<br>valid. e.g.: "cn=Directory Manager".<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Alias dereferencing | Select the option on the list. Never improves search performance if you are sure<br>that no alias is to be dereferenced. By default, Always is to be used:<br><br><br>Always: Always dereference<br>aliases,<br><br><br>Never: Never dereferences<br>aliases,<br><br><br>Searching: Dereferences aliases<br>only after name resolution,<br><br><br>Finding: Dereferences aliases only<br>during name resolution. |
| Referrals handling | Select the option on the list:<br><br><br>Ignore: does not handle request<br>redirections,<br><br><br>Follow: does handle request<br>redirections. |
| Previous DN and New<br>DN | Select from the list the schema column that holds the old DN<br>(Previous DN) and the column<br>that holds the new DN (New DN). |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description, it defines the number of fields to								be processed and passed on to the next component. The schema is								either <span>Built-in</span> or stored remotely								in the <span>Repository</span>. </p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-in</span>: The schema is created								and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already								exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul> |
| Die on error | This check box is selected by default. Clear the check box to skip<br>the row on error and complete the process for error-free rows. If<br>needed, you can retrieve the rows on error via a Row &gt; Reject link. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component covers all possible LDAP queries. It is usually<br>used as a one-component subJob but you can use it with other<br>components as well.<br><br>Note: Press Ctrl + Space bar to<br>access the global variable list, including the GetResultName variable to retrieve automatically the<br>relevant DN Base. |
