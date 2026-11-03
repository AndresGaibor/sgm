# tldapconnection

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tldapconnection  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tldapconnection -->

# tLDAPConnection

Creates a connection to an LDAP Directory server.

tLDAPConnection can be invoked by other components that need to access the LDAP Directory server, e.g., tLDAPInput, tLDAPOutput, etc.

## tLDAPConnection Standard properties

These properties are used to configure tLDAPConnection running in the Standard Job framework.

The Standard tLDAPConnection component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Host | LDAP Directory server IP address. |
| Port | Listening port number of server. |
| Protocol | Select the protocol type on the list.<br><br><br>LDAP: no encryption is used<br><br><br>LDAPS: secured LDAP. When this<br>option is chosen, the Advanced CA<br>check box appears. Once selected, the advanced mode allows you to<br>specify the directory and the keystore password of the certificate<br>file for storing a specific CA. However, you can still deactivate<br>this certificate validation by selecting the Trust all certs check box.<br><br><br>TLS: certificate is used. When this<br>option is chosen, the Advanced CA<br>check box appears and is used the same way as that of the LDAPS type. |
| Base DN | Path to user's authorized tree leaf. |
| User and Password | Fill in the User and Password as required by the<br>directory<br><br>Note that the login must match the LDAP syntax requirement to be<br>valid. e.g.: "cn=Directory Manager".<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Alias dereferencing | Select the option on the list. Never improves search performance if you are sure<br>that no aliases is to be dereferenced. By default, Always is to be used:<br><br><br>Always: Always dereference<br>aliases<br><br><br>Never: Never dereferences<br>aliases.<br><br><br>Searching:Dereferences aliases only<br>after name resolution.<br><br><br>Finding: Dereferences aliases only<br>during name resolution |
| Referral handling | Select the option on the list:<br><br><br>Ignore: does not handle request<br>redirections<br><br><br>Follow:does handle request<br>redirections |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a<br>job level as well as at each component level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is to be used with other LDAP components,<br>especially with tLDAPInput and<br>tLDAPOutput. |
