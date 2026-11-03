# tamazonemrresize

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tamazonemrresize  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tamazonemrresize -->

# tAmazonEMRResize

Adds or resizes a task instance group in a cluster on Amazon EMR (Elastic MapReduce).

## tAmazonEMRResize Standard properties

These properties are used to configure tAmazonEMRResize running in the Standard Job framework.

The Standard tAmazonEMRResize component belongs to the Cloud family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Access key and<br>Secret key | Specify the access keys (the access key ID in the Access<br>key field and the secret access key in the Secret<br>key field) required to access the Amazon Web Services. For more<br>information on AWS access keys, see [Access keys (access key ID and secret access key)](http://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys).<br><br>To enter the secret key, click the [...]<br>button next to the secret key field, and then in the pop-up dialog box enter the password<br>between double quotes and click OK to save the<br>settings. |
| Inherit credentials from AWS role | Select this checkbox to leverage the instance profile credentials. These<br>credentials can be used on Amazon EC2 instances, and are delivered through the<br>Amazon EC2 metadata service. To use this option, your Job must be running within<br>Amazon EC2 or other services that can leverage IAM Roles for access to resources.<br>For more information, see [Using an IAM Role to Grant Permissions to<br>Applications Running on Amazon EC2 Instances](http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html). |
| Assume role | If you temporarily need some access permissions associated to an AWS IAM<br>role that is not granted to your user account, select this checkbox to assume that<br>role. Then specify the values for the following parameters to create a new assumed<br>role session. |
| Action | Select an action to be performed from the drop-down list.<br><br><ul> <li> <p> <span>Add task instance group</span>: add a task instance group in a cluster.                           </p> </li> <li> <p> <span>Resize task instance group</span>: resize a task instance group in a cluster.                           </p> </li> </ul> |
| Region | Specify the AWS region by selecting a region name from the list or<br>entering a region between double quotation marks (for example<br>*"us-east-1"*). For more information about how to specify the AWS region,<br>see<br>[Choose an AWS Region](http://docs.aws.amazon.com/ElasticMapReduce/latest/ManagementGuide/emr-plan-region.html). |
| Cluster id | Enter the ID of the cluster to be resized. |
| Group name | Enter the name of the task instance group to be added.<br><br>This field is available only when<br>Add task instance group is selected from the<br>Action drop-down list. |
| Group id | Enter the ID of the task instance group to be resized.<br><br>This field is available only when<br>Resize task instance group is selected from the<br>Action drop-down list. |
| Instance count | Enter the number of instances for the task instance group. |
| Task instance type | Select an instance type for all instances in the task instance group<br>to be added from the drop-down list.<br><br>This list is available only when<br>Add task instance group is selected from the<br>Action drop-down list. |
| Request spot | Select this check box to launch Spot instances, and in the<br>Bid price($) field displayed, enter the maximum hourly rate (in dollars)<br>you are willing to pay per instance.<br><br>This check box is available only when<br>Add task instance group is selected from the<br>Action drop-down list. |

## Advanced settings

| Properties | Description |
| --- | --- |
| STS Endpoint | Select this check box to specify the AWS Security<br>Token Service (STS) endpoint from which to retrieve the session credentials.<br>For example, enter sts.amazonaws.com.<br><br>This checkbox is available only when the Assume<br>role checkbox is selected. |
| Signing region | Select the AWS region of the STS service. If the region is<br>not in the list, you can enter its name between double quotation marks. The<br>default value is us-east-1.<br><br>This dropdown list is available only when the Assume role<br>checkbox is selected. |
| External ID | If the administrator of the account to which the role<br>belongs provided you with an external ID, enter its value here. The<br>External Id is a unique<br>identifier that allows a limited set of users to assume the role.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Serial number | When you assume a role, the trust policy of this role might<br>require Multi-Factor Authentication (MFA). In this case, you must indicate<br>the identification number of the hardware or virtual MFA device that is<br>associated with the user who assumes the role.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Token code | When you assume a role, the trust policy of this role might<br>require Multi-Factor Authentication (MFA). In this case, you must indicate a<br>token code. This token code is a time-based one-time password produced by<br>the MFA device.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Tags | List session tags in the form of key-value pairs. You can<br>then use these session tags in policies to allow or deny access to requests.<br><br><br>Transitive: select this checkbox to indicate that a tag<br>will persist to the next role in a role chain.<br><br>For more information about tags, see [Passing Session Tags in AWS<br>STS](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_session-tags.html#id_session-tags_role-chaining)<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| IAM policy ARNs | Enter the Amazon Resource Names (ARNs) of the IAM managed<br>policies that you want to use as managed session policies. Use managed<br>session policies to limit the permissions of the session. The policies must<br>exist in the same account as the role. The resulting session's permissions<br>are the intersection of the role's identity-based policy and the session<br>policies.<br><br>For more information about session policies, see the<br>corresponding section in [Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_session)<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Policy | Enter an IAM policy in JSON format that you want to use as a<br>session policy. Use session policies to limit the permissions of the<br>session. The resulting session's permissions are the intersection of the<br>role's identity-based policy and the session policies.<br><br>For more information about session policies, see the<br>corresponding section in [Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_session)<br><br>This field is available only when the Assume role check box<br>is selected. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at the Job<br>level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | TASK\_GROUP\_ID: the ID of the task<br>instance group. This is an After variable and it returns a string.<br><br><br>TASK\_GROUP\_NAME:<br>the name of the task instance group. This is an After variable and it returns a<br>string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | tAmazonEMRResize is usually used as a standalone component. |

**Related concepts**

* [Managing an Amazon EMR cluster](https://help.qlik.com/talend/en-US/components/8.0/tamazonemrmanage-tamazonemrresize-tamazonemrlistinstances-tjava-managing-amazon-emr-cluster-standard-component "Here's an example of using Talend components to manage an Amazon EMR cluster.")
