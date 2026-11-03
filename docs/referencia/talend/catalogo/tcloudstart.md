# tcloudstart

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tcloudstart  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tcloudstart -->

# tCloudStart

Starts instances on Amazon EC2 (Amazon Elastic Compute Cloud).

This component accesses the cloud provider to be used (Amazon EC2) and launches instances, which are virtual servers in that cloud. If an instance to be launched does not exist, tCloudStart creates it.

## tCloudStart Standard properties

These properties are used to configure tCloudStart running in the Standard Job framework.

The Standard tCloudStart component belongs to the Cloud family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Access key and Secret key | Enter or paste the access key and the secret key required by<br>Amazon to authenticate your requests to its web services. These<br>access credentials are generated from the Security Credential tab of<br>your Amazon account page.<br><br>To enter the secret key, click the [...]<br>button next to the secret key field, and then in the pop-up dialog box enter the password<br>between double quotes and click OK to save the<br>settings. |
| Cloud provider | Select the cloud provider to be used. |
| Image | Enter the name of the Amazon Machine Image (AMI) to be used to<br>launch an instance. This AMI defines the basic configuration of that<br>instance. |
| Region and Zone | Enter the region and the zone to be used as the geographic<br>location where you want to launch an instance.<br><br>The syntax used to express a location is predefined by Amazon, for<br>example, *us-east-1* representing<br>the *US East (Northern Virginia)*<br>region and *us-east-1a*<br>representing one of the Availability Zones within that region. For<br>further information about available regions for Amazon, see Amazon's<br>documentation about regions and endpoints and as well Amazon's FAQ<br>about region and Availability Zone. |
| Instance name | Enter the name of the instance to be launched. For example, you<br>can enter *Talend*.<br><br>Note that the upper letter will be converted to lower<br>letter. |
| Instance count | Enter the number of instances to be launched. At runtime, the name<br>specified in the Instance name<br>field, for example *Talend*, will<br>be used as the initial part of each instance name, and letters and<br>numbers will be randomly added to complete each name. |
| Instance type | Select the type of the instance(s) to be launched. Each type is<br>predefined by Amazon and defines the performance of every instance<br>you want to launch.<br><br>This drop-down list presents the API name of each instance type.<br>For further information, see Amazon's documentation about instance<br>types. |
| Proceed with a Key pair | Select this check box to use Amazon Key Pair for your login to<br>Amazon EC2. Once selecting it, a drop-down list appears to allow you to select<br>:<br><br><ul> <li> <p> <span>Use an existing Key Pair</span> to                              enter the name of that Key Pair in the field next to the drop-down                              list. If required, Amazon will prompt you at runtime to find and use                              that Key Pair. </p> </li> <li> <p> <span>Create a Key Pair</span> to enter the                              name of the new Key Pair in the field next to the drop-down list and                              define the location where you want to store this Key Pair in the                                 <span>Advanced settings</span> tab                              view.</p> </li> </ul> |
| Security group | Add rows to this table and enter the names of the security<br>groups to which you need to assign the instance(s) to be launched. The security<br>groups set in this table must exist on your Amazon EC2.<br><br>A security group applies specific rules on inbound traffic to<br>instances assigned to the group, such as the ports to be used. For further<br>information about security groups, see Amazon's documentation about security<br>groups.<br><br>Note that an instance can be assigned to a group by setting its security group<br>name or key pair name to jclouds#&lt;$group\_name&gt;, where<br>&lt;$group\_name&gt; identifies the group to which the<br>instance belongs. In this way, you can change the status of all instances or<br>running instances in one group at the same time using the<br>tCloudStop component. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Key Pair folder | Browse to, or enter the path to the folder you use to store the<br>created Key Pair file.<br><br>This field appears when you select Creating<br>a Key Pair in the Basic<br>settings tab view. |
| Volumes | Add rows and define the volume(s) to be created for the instances<br>to be launched in addition to the volumes predefined and allocated<br>by the given Amazon EC2.<br><br>The parameters to be set in this table are the same parameters<br>used by Amazon for describing a volume.<br><br>If you need to remove automatically an additional volume after<br>terminating its related instance, select the check box in the<br>Delete on termination<br>column. |
| tStatCatcher Statistics | Select this check box to collect the log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NODE\_GROUP: the name of the instance. This is an After variable and it<br>returns a string.<br><br><br>NODES: the instances launched. This is an After<br>variable and it returns an object.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component works standalone to launch an instance on Amazon<br>EC2. You can use this component to start the instance you need to deploy Jobs<br>on. |
