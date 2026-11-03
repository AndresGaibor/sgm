# twebserviceinput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/twebserviceinput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/twebserviceinput -->

# tWebServiceInput

Invokes a Method through a Web service.

This component calls the defined method from the invoked Web service, and returns the class as defined, based on the given parameters.

## tWebServiceInput Standard properties

These properties are used to configure tWebServiceInput running in the Standard Job framework.

The Standard tWebServiceInput component belongs to the Internet family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p>Either <span>Built-in</span> or <span>Repository</span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored                                centrally.</p> </li> <li> <p> <span>Repository</span>: Select the Repository                                file where the properties are stored. The fields that follow are                                completed automatically using the data retrieved.</p> </li> </ul> |
| ![](https://help.qlik.com/talend/en-US/components/Resources/images/Save_Icon.png) | Click this icon to open a WSDL schema wizard and store your WSDL<br>connection in the Repository tree<br>view.<br><br>For more information about setting up and storing database<br>connection parameters, see [Centralizing database metadata](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/centralizing-database-metadata). |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description, it defines the number of fields to                                be processed and passed on to the next component. The schema is                                either <span>Built-in</span> or stored remotely                                in the <span>Repository</span>.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-in</span>: You create the schema                                and store it locally for the relevant component. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: You have already                                created the schema and stored it in the Repository. You can reuse it                                in various projects and Job flowcharts. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul> |
| WSDL | Description of Web service bindings and configuration. |
| Need authentication / Username and<br>Password | Select this check box and:<br><br>-enter a username and a password in the corresponding fields if<br>this is necessary to access the service. Or,<br><br>-select the Windows<br>authentication check box and enter the windows domain<br>in the corresponding field if this is necessary to access the<br>service.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Use http proxy | Select this check box if you are using a proxy server and fill in<br>the necessary information. |
| Trust server with SSL | Select this check box to validate the server certificate to the<br>client via an SSL protocol and fill in the corresponding<br>fields:<br><br><br>TrustStore file: enter the path<br>(including filename) to the certificate TrustStore file that<br>contains the list of certificates that the client trusts.<br><br><br>TrustStore password: enter the<br>password used to check the integrity of the TrustStore data. |
| Time out (second) | Set a value in seconds for Web service connection time out. |
| Method Name | Enter the exact name of the Method to be invoked.<br><br>The Method name MUST match the corresponding method described in<br>the Web Service. The Method name is also case-sensitive. |
| Parameters | Enter the parameters expected and the sought values to be<br>returned. Make sure that the parameters entered fully match the<br>names and the case of the parameters described in the method. |

## Advanced Settings

| Properties | Description |
| --- | --- |
| API | Select the framework for invoking the Web service method: AXIS or<br>CXF. See [Web Services - Axis](http://axis.apache.org/axis/) and [Apache AXF](http://cxf.apache.org/) for related information. |
| Advanced Use | Select this check box to display the fields dedicated<br>for the advanced use of tWebServiceInput:<br><br><br>WSDL2java: click the [...]<br>button to generate<br>Talend<br>routines that<br>hold the Java code necessary to connect and query the Web<br>service.<br><br><br>Code: replace the generated model<br>Java code with the code necessary to connect and query the specified<br>Web service using the code in the generated<br>Talend<br>routines.<br><br><br>Match Brackets: select the number<br>of brackets to be used to close the for loop based on<br>the number of open brackets.<br><br>Information noteNote: The Advanced Use option is available when AXIS is selected from the API drop-down list. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a<br>Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is generally used as a Start component. It must be<br>linked to an output component. |

**Related concepts**

* [Getting the sum of two numbers using tWebServiceInput](https://help.qlik.com/talend/en-US/components/8.0/getting-sum-of-two-numbers-using-twebserviceinput-standard-component "This scenario describes a two-component Job which uses a Web service method to obtain the sum of two numbers and displays the output on the Run console view.")
