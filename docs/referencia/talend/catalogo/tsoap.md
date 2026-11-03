# tsoap

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsoap  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsoap -->

# tSOAP

Calls a method via a Web service in order to retrieve the values of the parameters defined in the component editor.

tSOAP sends the defined SOAP message with the given parameters to the invoked Web service and returns the value as defined, based on the given parameters.

## tSOAP Standard properties

These properties are used to configure tSOAP running in the Standard Job framework.

The Standard tSOAP component belongs to the Internet family.

Information noteNote: This component is designed for Data Integration Jobs. It is not supported in ESB use cases. To build Jobs that need to be deployed into the Talend Runtime, use the tESBConsumer component which is best suited for the Talend Runtime.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit schema | A schema is a row description, it defines the number of fields that will<br>be processed and passed on to the next component.<br><br>This component always uses a built-in, read-only schema.<br><br>By default, the schema contains three String type columns:<br><br>- Header: stores the SOAP message<br>header of the response from the server end.<br><br>- Body: stores the SOAP message body of<br>the response from the server end.<br><br>- Fault: stores the error information<br>when an error occurs during the SOAP message processing.<br><br>If the Output in Document check box is<br>selected, the schema then contains only one Document type column named Soap, which stores the whole response SOAP message in the XML<br>format.<br><br>Click Edit schema to view the schema<br>structure.<br><br>Information noteWarning:<br><br><br>*Changing the schema type may result in loss of the schema<br>structure and therefore failure of the component.* |
| Use NTLM | Select this check box if you want to use the NTLM authentication<br>protocol.<br><br><br>Domain: Name of the client domain. |
| Need authentication | Select this check box and enter a user name and a password in the<br>corresponding fields if this is necessary to access the service.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Use http proxy | Select this check box if you are using a proxy server and fill in the<br>necessary information. |
| Trust server with SSL | Select this check box to validate the server certificate to the client<br>via an SSL protocol and fill in the corresponding fields:<br><br><br>TrustStore file: enter the path (including<br>filename) to the certificate TrustStore file that contains the list of<br>certificates that the client trusts.<br><br><br>TrustStore password: enter the password<br>used to check the integrity of the TrustStore data. |
| ENDPOINT | Type in the URL address of the invoked Web server. |
| SOAP Action | Type in the URL address of the SOAPAction HTTP header field to be used to<br>identify the intent of the SOAP HTTP request. |
| SOAP version | Select the version of the SOAP system you are using.<br><br>Information noteWarning:<br><br><br>*The required SOAP Envelope varies among<br>versions.* |
| Use a message from the input<br>schema | Select this check box to read a SOAP message from the preceding component<br>to send to the invoked Web service.<br><br>When this check box is selected, the SOAP<br>message field becomes a drop-down list allowing you to select<br>a Document type column to read an input XML<br>file.<br><br>Information noteWarning:<br><br><br>*This option makes sense only when the<br>tSOAP component is connected with<br>an input component the schema of which contains a Document type column to read a valid SOAP<br>message.* |
| Output in Document | Select this check box to output the response message in XML<br>format. |
| SOAP message | Type in the SOAP message to be sent to the invoked Web service.<br>The global and context variables can be used when you write a SOAP message.<br><br>Information noteNote:<br><br>To use special Latin characters, use encoding CP1252 in the SOAP message<br>instead.<br><br>For further information about the context variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use Kerberos | Select this check box to choose a tSetKerberosConfiguration component from the Kerberos configuration list.<br><br>Information noteNote:<br><br>The OnSubjobOk trigger of tSetKerberosConfiguration should be used for<br>connection with tSoap. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a Job<br>level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component can be used as an input or as an intermediate<br>component. |
| Connections | Outgoing links (from this component to another):<br><br><br>Row: Main; Iterate<br><br><br>Trigger: Run if; On Component Ok; On<br>Component Error.<br><br>Incoming links (from one component to this one):<br><br><br>Row: Main; Iterate<br><br><br>Trigger: Run if; On Component Ok; On<br>Component Error.<br><br>For further information regarding connections, see [Using connections in a Job](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/using-connections-in-job). |

**Related concepts**

* [Fetching the country name information using a Web service](https://help.qlik.com/talend/en-US/components/8.0/tsoap-tlogrow-fetching-country-name-information-using-web-service-standard-component "This scenario describes a two-component Job that uses a Web service to retrieve the country name information of a given country code.")
* [Using a SOAP message from an XML file to get country name information and saving the information to an XML file](https://help.qlik.com/talend/en-US/components/8.0/tsoap-tfileinputxml-tfileoutputxml-tfileoutputxml-using-soap-message-from-xml-file-to-get-country-name-information-and-saving-information-to-xml-file-standard-component-this)
