# tpop

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tpop  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tpop -->

# tPOP

Fetches one or more email messages from a server using the POP3 or IMAP protocol.

tPOP uses the POP or IMAP protocol to connect to a specific email server. Then it fetches one or more email messages and writes the recovered information in specified files. Parameters in the Advanced settings view allows you to use filters on your selection.

## tPOP Standard properties

These properties are used to configure tPOP running in the Standard Job framework.

The Standard tPOP component belongs to the Internet family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Host | IP address of the email server you want to connect to. |
| Port | Port number of the email server. |
| Authentication mode | Select one of the two authentication modes from the drop-down list.<br><br><ul> <li> <span>Basic</span>, which authenticates accesses using                                username and password. You need to provide the username and password                                to retrieve the mail messages. To enter the password, click the                                    <span>[...]</span> button next to the                                    <span>Password</span> field, enter the password in                                double quotes in the pop-up dialog box, and click                                    <span>OK</span> to save the settings.</li> <li> <span>OAuth2</span>, which authenticates accesses using OAuth                                2.0. You need to provide the username and OAuth access token to                                retrieve the mail messages. To enter the OAuth access token, click                                the <span>[...]</span> button next to the <span>OAuth                                    Access Token</span> field, enter the OAuth access token in                                double quotes in the pop-up dialog box, and click                                    <span>OK</span> to save the settings.</li> </ul><br><br><ul> <li> <span>Microsoft Exchange</span>, which authenticates                                accesses using Microsoft Exchange. You need to provide the username,                                tenant ID, application (client) ID, and secret value of a Microsoft                                Azure application in the <span>Username</span>,                                    <span>Directory (tenant) ID</span>,                                    <span>Application (client) ID</span>, and                                    <span>Secret Value</span> fields. Note that the                                Microsoft Azure application needs to have the POP or IMAP API                                permission and the service principal of the application needs to be                                registered in Microsoft Exchange. See <a href="https://help.qlik.com/talend/en-US/components/8.0/pop/configuring-an-oauth2-application-for-pop-and-imap" target="_blank">Configuring a Microsoft Azure application for POP and IMAP</a> and <a href="https://help.qlik.com/talend/en-US/components/8.0/pop/registering-service-principal-in-exchange" target="_blank">Registering the service principal of an application in Microsoft Exchange</a> for                                related information.</li> </ul><br><br>Information noteNote:<br><br><ul> <li>The <span>Authentication mode</span> drop-down list and the                             <span>Oauth2</span> item are available only when you have                           installed the 8.0.1-R2022-08 <span>Talend Studio</span> Monthly update or a later one delivered by                             <span>Talend</span>. For more information, check with your administrator.</li> <li>The <span>Microsoft Exchange</span> item is available only                           when you have installed the 8.0.1-R2022-09 <span>Talend Studio</span> Monthly update                                    or a later one delivered by <span>Talend</span>. For more information, check with your administrator.</li> </ul> |
| Username and Password | User authentication data for the email server.<br><br><ul> <li> <span>Username</span>: enter the username you use to                                access your email box.</li> <li> <span>Password</span>: enter the password you use to                                access your email box. </li> </ul><br><br>These two fields are available when you select Basic<br>from the Authentication mode drop-down list. |
| Output directory | Enter the path to the file in which you want to store the email<br>messages you retrieve from the email server, or click the [...]<br>button next to the field to browse to the file. |
| Filename pattern | Define the syntax of the names of the files that will hold each of the<br>email messages retrieved from the email server, or press Ctrl+Space to display the list of predefined<br>patterns. |
| Retrieve all emails? | Select this check box to retrieve all email messages present on the<br>specified server. |
| Number of emails to retrieve | Enter the number of email messages you want to retrieve.<br><br>This field is available only when the Retrieve<br>all emails? check box is cleared. |
| Newer email first | Select this check box to retrieve the most recent email messages<br>according to the number specified in the Number of<br>emails to retrieve field, and the email messages will be<br>returned in chronological order.<br><br>This check box is available only when the Retrieve all emails? check box, which is selected by<br>default, is cleared. |
| Delete emails from server | Select this check box if you do not want to keep the retrieved email<br>messages on the server.<br><br>Information noteNote: For Gmail servers, this option does not work for the pop3<br>protocol. Select the imap protocol and ensure that the Gmail account<br>is configured to use imap. |
| Choose the protocol | From the list, select the protocol to be used to retrieve the email<br>messages from the server. This protocol is the one used by the email<br>server. If you choose the imap protocol, you will be able to select the<br>folder from which you want to retrieve your emails. |
| Use SSL | Select this check box if your email server uses this protocol for<br>authentication and communication confidentiality.<br><br>Information noteNote: This option is obligatory for users of Gmail. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a job<br>level as well as at each component level. |
| Filter | Click the plus button to add as many lines as needed to<br>filter email messages, select one or multiple of the following filter<br>items in the Filter item columns of the lines,<br>and set values for the filter items in the<br>Pattern columns.<br><br><ul> <li> <span>From</span>: email messages are filtered                           according to the sender email address.</li> <li> <span>To</span>: email messages are filtered                           according to the recipient email address.</li> <li> <span>Subject</span>: email messages are filtered                           according to the message subject matter.</li> <li> <span>Before date</span>: email messages are                           filtered by the sending or receiving date. All messages before the set                           date are retrieved.</li> <li> <span>After date</span>: email messages are filtered                           by the sending or receiving date. All messages after the set date are                           retrieved.</li> </ul><br><br>To set a value for the filter item, you can enter the value in the<br>Pattern column directly or press Ctrl + Space and select the expression<br>from the list. |
| Use two line authentication for OAuth2 | Select this option to use two-line authentication for OAuth2.<br><br>This option is available when you select OAuth2 from the Authentication mode drop-down list in the Basic settings view.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-08<br>Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Custom properties | Add custom properties and set property values.<br><br>To add a custom property key-value pair, add a row in the table by clicking the<br>plus button on the bottom of the table, fill the property name in double<br>quotation marks in the Key column, and fill the property<br>value in the Value column.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-08<br>Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Filter condition relation | Select the type of logical relation you want to use to combine the<br>specified filters:<br><br><br>and: the conditions set by the filters<br>are combined together, the research is more restrictive.<br><br><br>or: the conditions set by the filters<br>are independent, the research is large. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>NB\_EMAIL: the number of emails received.<br>This is an After variable and it returns an integer.<br><br><br>CURRENT\_FILE: the<br>current file name. This is a Flow variable and it returns a string.<br><br><br>CURRENT\_FILEPATH:<br>the current file path. This is a Flow variable and it returns a string.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component does not handle data flow, it can be used alone. |
| Limitation | When the Use SSL check box or the<br>imap protocol is selected,<br>tPOP cannot work with IBM Java<br>6. |

**Related concepts**

* [Retrieving a selection of email messages from an email server](https://help.qlik.com/talend/en-US/components/8.0/tpop-retrieving-selection-of-email-messages-from-email-server-standard-component-this)
