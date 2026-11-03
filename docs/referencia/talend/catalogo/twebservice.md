# twebservice

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/twebservice  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/twebservice -->

# tWebService

Calls a method via a Web service in order to retrieve the values of the parameters defined in the component editor.

Information noteWarning: This component requires a JDK to be functional. It should be noted that tWebservice will not run in Talend Cloud.

tWebservice calls the defined method from the invoked Web service and returns the class as defined, based on the given parameters.

## tWebService Standard properties

These properties are used to configure tWebService running in the Standard Job framework.

The Standard tWebService component belongs to the Internet family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p>Either<span> Built-in</span> or <span>Repository</span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally. Enter properties manually</p> </li> <li> <p> <span>Repository</span>: Select the repository								file where properties are stored. The fields that come after are								pre-filled in using the fetched data.</p> </li> </ul> |
| Service configuration | Click the [...] button next to the field to open the component<br>editor.<br><br>In this editor, you can:<br><br>-select the Web service you want to use,<br><br>-configure the input parameters of the Web service,<br><br>-configure the output parameters of the Web service. These<br>parameters will be used to retrieve and output specific data. |
| Mapping links display as | Auto: By default, the links<br>between the input and output schemas and the Web service parameters<br>are in the form of curves.<br><br><br>Curves: Links between the schema<br>and the Web service parameters are in the form of curve.<br><br><br>Lines: Links between the schema and<br>the Web service parameters are in the form of straight lines. This<br>option slightly optimizes performance. |
| Connection Time out | Set a value in seconds for Web service connection time out. |
| Receive Time out | Set a value in seconds for server answer. |
| Input schema | A schema is a row description. It defines the number of fields<br>that will be processed and passed on to the next component. The<br>schema is either built-in or remote in the Repository. This field is<br>used to process the input schema. The option for this schema may<br>be:<br><br>- Built-in: No property data<br>stored centrally.<br><br>- Repository: Select the<br>Repository file where properties are stored. The following fields<br>are pre-filled in using fetched data. |
| Edit Schema | Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Sync columns | This button is available when an input link has been created.<br>Click this button to retrieve the schema from the previous component<br>connected in the Job. |
| Output schema | This field is used to process the output schema. The schema is<br>either built-in or remote in the Repository and is configured the<br>same way as the input schema is.<br><br>Information noteWarning:<br><br><br>*The input schema is not necessarily identical with the<br>output schema.* |
| Use NTLM | Select this check box if you want to use the NTLM authentication<br>protocol.<br><br><br>Domain: Name of the client<br>domain,<br><br><br>Host: Client IP address. |
| Need authentication | Select this check box and enter a username and a password in the<br>corresponding fields if this is necessary to access the<br>service.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Use http proxy | Select this check box if you are using a proxy server and fill in<br>the necessary information. |
| Trust server with SSL | Select this check box to validate the server certificate to the<br>client via an SSL protocol and fill in the corresponding<br>fields:<br><br><br>TrustStore file: enter the path<br>(including filename) to the certificate TrustStore file that<br>contains the list of certificates that the client trusts.<br><br><br>TrustStore password: enter the<br>password used to check the integrity of the TrustStore data. |
| Die on error | Clear this check box to skip the rows in error and to complete the<br>process for the error free rows. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Temporary folder (for wsdl2java) | Set or browse to a temporary folder that you configured in order<br>to store the wsdl files. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a<br>Job level as well as at each component level. |
| Enable parallel execution | Select this check box to perform high-speed data processing, by treating<br>multiple data flows simultaneously. Note that this feature depends on the database or<br>the application ability to handle multiple inserts in parallel as well as the number of<br>CPU affected. In the Number of parallel executions<br>field, either:<br><br><ul> <li>Enter the number of parallel executions desired.</li> <li>Press <span>Ctrl+Space</span> and select               the appropriate context variable from the list. For further information about context               variables, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables" target="_blank">Using contexts and variables</a>. </li> </ul><br><br>Note that when parallel execution is enabled, it is not possible to use global<br>variables to retrieve return values in a subJob. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component can be used as an input or as an intermediate<br>component. It must be linked to an output component. |
| Limitation | A JDK is required for this component to operate. |

**Related concepts**

* [Getting country names using tWebService](https://help.qlik.com/talend/en-US/components/8.0/twebservice-tfixedflowinput-tlogrow-tlogrow-getting-country-names-using-twebservice-standard-component-this)
