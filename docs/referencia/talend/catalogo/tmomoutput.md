# tmomoutput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tmomoutput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmomoutput -->

# tMomOutput

Adds a message to a Message-Oriented Middleware system queue in order for it to be fetched asynchronously.

tMomOutput makes it possible to set up asynchronous communications via a MOM server.

For further information, see [https://help.talend.com/r/en-US/8.0/studio-user-guide/messaging-brokers-supported-by-talend-messaging-components](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/messaging-brokers-supported-by-talend-messaging-components).

## tMomOutput Standard properties

These properties are used to configure tMomOutput running in the Standard Job framework.

The Standard tMomOutput component belongs to the Internet family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Use existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Note that when a Job contains the parent Job and the child Job,<br>Component List presents only the<br>connection components in the same Job level. |
| Failover | Select this check box to use the ActiveMQ failover transport.<br>For more information about the failover transport, see [Failover Transport<br>Reference](http://activemq.apache.org/failover-transport-reference.html).<br><br>This check box is available only when ActiveMQ is selected from the MQ<br>server list and the Static<br>Discovery check box is cleared. |
| Static Discovery | Select this check box to use the ActiveMQ static transport<br>discovery mechanism. For more information about the static transport, see [Static Transport<br>Reference](http://activemq.apache.org/static-transport-reference.html).<br><br>This check box is available only when ActiveMQ is selected from the MQ server list and the Failover check box is cleared. |
| URI parameters | Enter the URI parameters.<br><br>This field is available only when the Failover or Static<br>Discovery check box is selected. |
| MQ Server | Select the type of the MQ server(s) to be connected from the<br>list: ActiveMQ or WebSphere MQ. According to the server type selected, the<br>parameters required differ slightly. |
| Use SSL Transport | Select this check box to use the ActiveMQ SSL transport. For<br>more information about the SSL transport, see [SSL Transport<br>Reference](http://activemq.apache.org/ssl-transport-reference.html).<br><br>This check box is available only when ActiveMQ is selected from the MQ server list. |
| Host | Enter the host name or IP address of the MQ server. |
| Port | Enter the listening port of the MQ server. |
| Username and Password | Enter the user authentication credentials.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Channel | Specify the name of the channel through which the connection is<br>established. The default value is *DC.SVRCONN*.<br><br>This field is available only when WebSphere MQ is selected from the MQ<br>server list. |
| To | Type in the message destination, respecting the syntax required<br>by the server; this must include the type and name of the target folder, e.g.:<br>queue/A or topic/testtopic. Note that this field is case-sensitive.<br><br>This field is available only when ActiveMQ is selected from the MQ<br>Server list. |
| Message Type | Select the message type: either Topic or Queue.<br><br>This list is available only when ActiveMQ is selected from the MQ<br>Server list. |
| Message Body Type | Select the message body type: Text<br>Message, Bytes Message or<br>Map Message. |
| Schema and Edit Schema | A schema is a row description, it defines the number of fields<br>that will be processed and passed on to the next component.<br><br>In the context of tMomOutput usage, the schema is read-only but will change<br>according to the incoming schema. Only one-column schema is expected by the<br>server to contain the Messages. |
| QueueManager | Specify the name of the queue manager to which the connection<br>is established.<br><br>This field is available only when WebSphere MQ is selected from the MQ<br>server list. |
| MessageQueue | Enter the name of the message queue into which message queueing<br>applications can put messages.<br><br>This field is available only when WebSphere MQ is selected from the MQ<br>server list. |
| Set Transacted | Select this check box to transact the session. For further<br>information about this parameter, see https://publib.boulder.ibm.com/iseries/v5r2/ic2924/books/csqzaw07.pdf.<br><br>Note that selecting this check box will ignore the settings in<br>the Acknowledgement Mode list in the<br>Advanced settings view of tMomInput. |
| Is using message id to set | Select this check box to set messages according to their<br>ids.<br><br>This check box is available only when Text Message or Bytes<br>Message is selected from the Message<br>Body Type list. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional options | Define the additional transport options in the table. This<br>table is available only if you select the Failover or Static<br>Discovery check box in the Basic<br>settings view.<br><br><ul> <li> <p> <span>Option name</span>: the name of the                           option.</p> </li> <li> <p> <span>Option value</span>: the value of the                           option.</p> </li> </ul><br><br>For example, enter *maxReconnectAttempts*<br>in the Option name field and then *0* in the Option<br>value field so that no attempt is made to retry the connection<br>when no server is available.<br><br>For more information about the failover transport options, see<br>[Failover Transport<br>Reference](http://activemq.apache.org/failover-transport-reference.html).<br><br>For more information about the static discovery transport<br>options, see [Static Transport<br>Reference](http://activemq.apache.org/static-transport-reference.html). |
| Delivery Mode | Select a delivery mode supported by JMS:<br><br><br>Not Persistent: This delivery mode does<br>not require that the message be logged to stable storage.<br><br><br>Persistent: This delivery mode requires<br>that the message be logged to stable storage as part of the client's send<br>operation.<br><br>For further information about the delivery modes, see https://publib.boulder.ibm.com/iseries/v5r2/ic2924/books/csqzaw07.pdf.<br><br>(Available when ActiveMQ<br>is selected in the MQ Server list.) |
| Set Jms Header | Select this check box to send the Jms headers through the<br>mapping from Jms fields onto MQ Series fields on the MQ server. When this check<br>box is checked, you can specify the header name and the header value in the<br>line(s) you added by clicking the plus button in the Parameters table. For further information about the usage of<br>Jms headers, see https://publib.boulder.ibm.com/iseries/v5r2/ic2924/books/csqzaw07.pdf.<br><br>(Available when ActiveMQ<br>is selected in the MQ Server list.) |
| Set Jms Properties | Select this check box to send the Jms properties mapped onto<br>MQMD fields on the MQ server. When this check box is checked, you can specify<br>the property name, the property type and the property value in the line(s) you<br>added by clicking the plus button in the Parameters table. For further information about the usage of<br>Jms properties, see https://publib.boulder.ibm.com/iseries/v5r2/ic2924/books/csqzaw07.pdf.<br><br>(Available when ActiveMQ<br>is selected in the MQ Server list.) |
| Use format | Select this check box to specify the WebSphere message format<br>in the WebSphere Message Format field.<br>The default format is *MQSTR*.<br><br>For further information about WebSphere message format, see<br>http://publib.boulder.ibm.com/infocenter/wtxdoc/v8r2m0/index.jsp?topic=/com.ibm.websphere.dtx.adapibmmq.doc/references/r\_ibmmq\_Message\_Format\_FORMAT.htm.<br><br>(Available when WebSphere<br>MQ is selected in the MQ<br>Server list.) |
| Set MQMD Fields | Select this check box to enable the Parameters table in which you can specify the value of the MQMD<br>fields.<br><br>This check box is available only when WebSphere MQ is selected from the MQ Server list. |
| Parameters | Specify the value of the MQMD fields.<br><br><ul> <li> <p> <span>Field Name</span>: Select an MQMD                              field from the list.</p> </li> <li> <p> <span>Field Value</span>: Enter the value of                              the corresponding MQMD field.</p> </li> </ul><br><br>This table is available only when the Set MQMD Fields check box is selected.<br><br>For more information about the MQMD fields, see [Fields for MQMD](http://www-01.ibm.com/support/knowledgecenter/SSFKSJ_7.0.1/com.ibm.mq.csqzak.doc/fr13050_.htm). |
| Include Header | Select this check box to specify the header of the message:<br><br><br>MQRFH2 fixed Portion: Select this check<br>box and click the plus button to add one or more lines to specify the<br>Version, Encoding, Format,<br>Flags, NameValueCCSID and CodedCharSetId as needed for the fixed portion of MQRFH2<br>header.<br><br><br>MCD folder: Select this check box and<br>click the plus button to add one or more lines to specify the field name and<br>the value for the properties that describe the format of the message.<br><br><br>JMS folder: Select this check box and<br>click the plus button to add one or more lines to specify the field name and<br>the value for the transportation of JMS header fields and JMSX properties.<br><br><br>USR folder: Select this check box and<br>click the plus button to add one or more lines to specify the field name and<br>the value for the transportation of application-defined properties associated<br>with the message.<br><br>For further information about MQRFH2 header, see http://publib.boulder.ibm.com/infocenter/wmbhelp/v6r1m0/index.jsp?topic=%2Fcom.ibm.etools.mft.doc%2Faq06920\_.htm.<br><br>Available when WebSphere<br>MQ is selected in the MQ<br>Server list. |
| Set Cipher Suite | Select this check box to enable the Cipher Suite list from which you can<br>specify the Cipher Suite to be used with WebSphere MQ SSL.<br><br>For further information about Cipher Suite, see [CipherSpecs and their equivalent CipherSuites<br>supported by IBM WebSphere MQ](https://www.ibm.com/support/knowledgecenter/SSFKSJ_7.1.0/com.ibm.mq.doc/ja34740_.htm).<br><br>Available when WebSphere MQ is selected in the<br>MQ Server list. |
| Custom Cipher Suite | Select this check box to allow you to custome Cipher Suite.<br><br><br>IBM Cipher Mappings: Use the IBM Java Cipher Suite to<br>IBM MQ Cipher Spec Mappings.<br><br><br>Oracle Cipher Mappings: Use the Oracle Cipher Suite to<br>IBM MQ Cipher Spec Mappings. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at<br>a Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component must be linked to an input or intermediary<br>component. |
| Dynamic settings | Click the [+] button<br>to add a row in the table and fill the Code field with a context variable to choose your MQ Server<br>connection dynamically from multiple connections planned in your Job.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | Make sure the relevant Websphere MQ or<br>ActiveMQ server is launched.<br><br>This component requires installation of its related jar files. |

**Related concepts**

* [Asynchronous communication via a MOM server](https://help.qlik.com/talend/en-US/components/8.0/tmomoutput-tmominput-tlogrow-trowgenerator-asynchronous-communication-via-mom-server-standard-component-this)
* [Transmitting XML files via a MOM server](https://help.qlik.com/talend/en-US/components/8.0/tmomoutput-tmominput-tfileinputxml-tlogrow-transmitting-xml-files-via-mom-server-standard-component-this)
