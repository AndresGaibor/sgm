# tsendmail

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsendmail  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsendmail -->

# tSendMail

Notifies recipients about a particular state of a Job or possible errors.

tSendMail sends emails and attachments to defined recipients.

## tSendMail Standard properties

These properties are used to configure tSendMail running in the Standard Job framework.

The Standard tSendMail component belongs to the Internet family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| To | Main recipient email address. |
| From | Sending server email address. |
| Show sender's name | Select this check box if you want the<br>sender name to show in the messages. |
| Cc | Email addresses of secondary recipients<br>of the email message directed to another. |
| Bcc | Email addresses of secondary recipients<br>of the email message. Recipients listed in the Bcc field receive a copy<br>of the message but are not shown on any other recipient's copy. |
| Subject | Heading of the mail. |
| Message | Body message of the email. Press<br>Ctrl+Space to<br>display the list of available variables. |
| Die if the attachment file doesn't<br>exist | This check box is selected by default.<br>Clear this check box if you want the message to be sent even if there<br>are no attachments. |
| Attachments | Specify the file(s) attached and sent<br>along with the email message. Click the [+] button to add as many rows as needed<br>and set the value of the following columns for each row:<br><br><ul> <li> <p> <span>File</span>: Enter the path to the                                        attached file or the path to the folder if all files                                        directly under it will be attached.</p> </li> <li> <p> <span>Content Transfer Encoding</span>:                                        Click the cell and select a content transfer encoding value                                        from the list.</p> </li> </ul> |
| Other Headers | Click the plus button to add as many<br>lines as needed where you can type the Key and the corresponding Value of any header<br>information that does not belong to the standard header. |
| SMTP Host and Port | IP address of SMTP server used to send<br>emails. |
| SSL Support | Select this check box to authenticate the<br>server at the client side via an SSL protocol. |
| STARTTLS Support | Select this check box to authenticate the<br>server at the client side via a STARTTLS protocol. |
| Importance | Select in the list the priority level of<br>your messages. |
| Authentication mode | Select one of the three authentication modes from the drop-down list.<br><br><ul> <li> <span>No Auth</span>, which requires no authentication.</li> <li> <span>Basic</span>, which authenticates accesses using username                        and password. You need to provide the username and password to send the                        mail. To enter the password, click the <span>[...]</span> button                        next to the <span>Password</span> field, enter the password in                        double quotes in the pop-up dialog box, and click <span>OK</span>                        to save the settings.</li> <li> <span>OAuth2</span>, which authenticates accesses using OAuth                        2.0. You need to provide the username and OAuth access token to send the                        mail. To enter the OAuth access token, click the                           <span>[...]</span> button next to the <span>OAuth Access                           Token</span> field, enter the OAuth access token in double quotes in                        the pop-up dialog box, and click <span>OK</span> to save the                        settings.</li> </ul><br><br>Information noteNote: The Authentication mode drop-down list and the<br>Oauth2 item are available only when you have<br>installed the 8.0.1-R2022-08 Talend Studio Monthly update or a later one delivered by<br>Talend. For more information, check with your administrator. |
| Die on error | This check box is selected by default.<br>Clear the check box to skip the row on error and complete the process<br>for error-free rows. |

## Advanced settings

| Properties | Description |
| --- | --- |
| MIME subtype from the 'text' MIME<br>type | Select in the list the structural form<br>for the text of the message. |
| Encoding type | Select the encoding from the list or<br>select Custom<br>and define it manually. |
| Set localhost | Select this option to specify a name for the local host. You can fill a string in the double<br>quotes in the Localhost field as the host name.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-08<br>Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Use two line authentication for OAuth2 | Select this option to use two-line authentication for OAuth2.<br><br>This option is available when you select OAuth2 from the Authentication mode drop-down list in the Basic settings view.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-08<br>Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Custom properties | Add custom properties and set property values.<br><br>To add a custom property key-value pair, add a row in the table by clicking the<br>plus button on the bottom of the table, fill the property name in double<br>quotation marks in the Key column, and fill the property<br>value in the Value column.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-08<br>Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| tStatCatcher Statistics | Select this check box to gather the Job<br>processing metadata at a Job level as well as at each component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the component when an<br>error occurs. This is an After variable and it returns a string.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is typically used as one<br>subJob but can also be used as output or end object. It can be connected<br>to other components with either Row or Iterate links. |

**Related concepts**

* [Sending an email on error](https://help.qlik.com/talend/en-US/components/8.0/tsendmail-tfileinputdelimited-tfileoutputxml-tfileoutputxml-sending-email-on-error-standard-component-this)
* [Sending an email with attachment in HTML format](https://help.qlik.com/talend/en-US/components/8.0/component-tsendmail-send-email "Through the configuration and properties of the tSendMail component, it is possible to send emails as plain text, HTML, and include attachments as required. Here is an example of using the tSendMail component to send an email with attachment in HTML format.")
