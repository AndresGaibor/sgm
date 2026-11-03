# tmomconnection

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tmomconnection  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmomconnection -->

# tMomConnection

Opens a connection to the MQ Server for communication.

## tMomConnection Standard properties

These properties are used to configure tMomConnection running in the Standard Job framework.

The Standard tMomConnection component belongs to the Internet family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Failover | Select this check box to use the ActiveMQ failover transport.<br>For more information about the failover transport, see [Failover Transport<br>Reference](http://activemq.apache.org/failover-transport-reference.html).<br><br>This check box is available only when ActiveMQ is selected from the MQ<br>server drop-down list and the Static<br>Discovery check box is cleared. |
| Static Discovery | Select this check box to use the ActiveMQ static transport<br>discovery mechanism. For more information about the static transport, see [Static Transport<br>Reference](http://activemq.apache.org/static-transport-reference.html).<br><br>This check box is available only when ActiveMQ is selected from the MQ<br>server list and the Failover check box is cleared. |
| URI parameters | Enter the URI parameters.<br><br>This field is available only when the Failover or Static<br>Discovery check box is selected. |
| MQ server | Select the type of the MQ server(s) to be connected from the<br>drop-down list, either ActiveMQ or<br>WebSphere MQ. |
| Use SSL Transport | Select this check box to use the ActiveMQ SSL transport. For<br>more information about the SSL transport, see [SSL Transport<br>Reference](http://activemq.apache.org/ssl-transport-reference.html).<br><br>This check box is available only when ActiveMQ is selected from the MQ server list. |
| Host | The host name or IP address of the MQ server. |
| Port | The listening port of the MQ server. |
| Username and Password | User authentication credentials.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Use Transacted | Select this check box to set the session created to be<br>transacted.<br><br>This check box is available only when ActiveMQ is selected from the MQ server drop-down list. |
| Channel | Specify the name of the channel through which the connection is<br>established. The default value is *DC.SVRCONN*.<br><br>This field is available only when WebSphere MQ is selected from the MQ<br>server drop-down list. |
| QueueManager | Specify the name of the queue manager to which the connection<br>is established.<br><br>This field is available only when WebSphere MQ is selected from the MQ<br>server drop-down list. |
| Use or register a shared Connection | Select this check box to share your connection or use a<br>connection shared by a parent or child Job. This allows you to share one single<br>connection among several connection components from different Job levels that<br>can be either parent or child.<br><br>This option is incompatible with the Use dynamic job<br>and Use an independent process to run subJob options of<br>the tRunJob component. Using a shared connection<br>together with a tRunJob component with either of these<br>two options enabled will cause your Job to fail. |
| Shared Connection Name | Enter the shared connection name.<br><br>This field is available only when the Use or register a shared Connection check box is<br>selected. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional options | Define the additional transport options in the table. This<br>table is available only when the Failover or Static<br>Discovery check box in the Basic<br>settings view is selected.<br><br><ul> <li> <p> <span>Option name</span>: the name of the                           option.</p> </li> <li> <p> <span>Option value</span>: the value of the                           option.</p> </li> </ul><br><br>For example, enter *maxReconnectAttempts*<br>in the Option name field and then *0* in the Option<br>value field so that no attempt is made to retry the connection<br>when no server is available.<br><br>For more information about the failover transport options, see<br>[Failover Transport<br>Reference](http://activemq.apache.org/failover-transport-reference.html).<br><br>For more information about the static discovery transport<br>options, see [Static Transport<br>Reference](http://activemq.apache.org/static-transport-reference.html). |
| Set Cipher Suite | Select this check box to enable the Cipher Suite list from which you can<br>specify the Cipher Suite to be used with WebSphere MQ SSL.<br><br>For further information about Cipher Suite, see [CipherSpecs and their equivalent CipherSuites<br>supported by IBM WebSphere MQ](https://www.ibm.com/support/knowledgecenter/SSFKSJ_7.1.0/com.ibm.mq.doc/ja34740_.htm).<br><br>Available when WebSphere MQ is selected in the<br>MQ Server list. |
| Custom Cipher Suite | Select this check box to allow you to customize Cipher Suite.<br><br><br>IBM Cipher Mappings: Use the IBM Java Cipher Suite to<br>IBM MQ Cipher Spec Mappings.<br><br><br>Oracle Cipher Mappings: Use the Oracle Cipher Suite to<br>IBM MQ Cipher Spec Mappings. |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is more commonly used with other tMom\*<br>components, especially with the tMomCommit and tMomRollback components. |
| Limitation | This component supports ActiveMQ and WebSphere MQ servers. |
