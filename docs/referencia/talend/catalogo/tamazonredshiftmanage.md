# tamazonredshiftmanage

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tamazonredshiftmanage  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tamazonredshiftmanage -->

# tAmazonRedshiftManage

Manages Amazon Redshift clusters and snapshots.

tAmazonRedshiftManage manages the work of creating a new Amazon Redshift cluster, creating a snapshot of an Amazon Redshift cluster, resizing an existing Amazon Redshift cluster, and deleting an existing cluster or snapshot.

## tAmazonRedshiftManage Standard properties

These properties are used to configure tAmazonRedshiftManage running in the Standard Job framework.

The Standard tAmazonRedshiftManage component belongs to the Cloud and the Databases families.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Access Key and Secret Key | Specify the access keys (the access key ID in the Access<br>key field and the secret access key in the Secret<br>key field) required to access the Amazon Web Services. For more<br>information on AWS access keys, see [Access keys (access key ID and secret access key)](http://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys).<br><br>To enter the secret key, click the [...]<br>button next to the secret key field, and then in the pop-up dialog box enter the password<br>between double quotes and click OK to save the<br>settings. |
| Inherit credentials from AWS role | Select this checkbox to leverage the instance profile credentials. These<br>credentials can be used on Amazon EC2 instances, and are delivered through the<br>Amazon EC2 metadata service. To use this option, your Job must be running within<br>Amazon EC2 or other services that can leverage IAM Roles for access to resources.<br>For more information, see [Using an IAM Role to Grant Permissions to<br>Applications Running on Amazon EC2 Instances](http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html). |
| Assume role | If you temporarily need some access permissions associated to an AWS IAM<br>role that is not granted to your user account, select this checkbox to assume that<br>role. Then specify the values for the following parameters to create a new assumed<br>role session. |
| Action | Select an action to be performed from the list.<br><br><ul> <li> <p> <span>Create cluster</span>: create a new Amazon Redshift cluster.</p> </li> <li> <p> <span>Delete cluster</span>: delete a previously provisioned Amazon Redshift cluster.</p> </li> <li> <p> <span>Resize cluster</span>: resize an existing Amazon Redshift cluster.</p> </li> <li> <span>Pause cluster</span>: pause an existing Amazon Redshift cluster.</li> <li> <span>Resume cluster</span>: resume a paused Amazon Redshift cluster.</li> <li> <p> <span>Restore from snapshot</span>: create a new Amazon Redshift cluster from a snapshot.</p> </li> <li> <p> <span>Delete snapshot</span>: delete the specified manual snapshot.</p> </li> </ul> |
| Region | Specify the AWS region by selecting a region name from the list or entering a region between double quotation marks (e.g. *"us-east-1"*) in the list. For more information about the supported AWS regions where you can provision an Amazon Redshift cluster, see [Regions and Endpoints](http://docs.aws.amazon.com/general/latest/gr/rande.html#redshift_region). |
| Create snapshot | Select this check box to create a final snapshot of the Amazon Redshift cluster before it is deleted.<br><br>This check box is available only when Delete cluster is selected from the Action list. |
| Snapshot id | Enter the identifier of the snapshot.<br><br>This field is available when:<br><br><ul> <li> <p> <span>Delete cluster</span> is selected from the <span>Action</span> list and the <span>Create snapshot</span> check box is selected.</p> </li> <li> <p> <span>Restore from snapshot</span> or <span>Delete snapshot</span> is selected from the <span>Action</span> list.</p> </li> </ul> |
| Cluster id | Enter the ID of the cluster.<br><br>This field is available when Create cluster, Delete cluster, Resize cluster, or Restore from snapshot is selected from the Action list. |
| Database | Enter the name of the first database to be created when the cluster is created.<br><br>This field is available only when Create cluster is selected from the Action list. |
| Port | Enter the port number on which the cluster accepts connections.<br><br>This field is available when Create cluster or Restore from snapshot is selected from the Action list. |
| Master username and Master password | The user name and the password associated with the master user account for the cluster to be created.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings.<br><br>The two fields are available only when Create cluster is selected from the Action list. |
| Node type | Select the node type for the cluster.<br><br>This list is available when Create cluster, Resize cluster, or Restore from snapshot is selected from the Action list. |
| Node count | Enter the number of compute nodes in the cluster.<br><br>This field is available only when Create cluster or Resize cluster is selected from the Action list. |

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
| Wait for cluster ready | Select this check box to let your Job wait until the launch of the cluster is completed.<br><br>This check box is available when Create cluster, Restore from snapshot, or Resume cluster is selected from the Action list. |
| Original cluster id of snapshot | Enter the name of the cluster the source snapshot was created from.<br><br>This field is available when Restore from snapshot or Delete snapshot is selected from the Action list. |
| Parameter group name | Enter the name of the parameter group to be associated with the cluster.<br><br>This field is available when Create cluster or Restore from snapshot is selected from the Action list. |
| Subnet group name | Enter the name of the subnet group where you want the cluster to be restored.<br><br>This field is available when Create cluster or Restore from snapshot is selected from the Action list. |
| Publicly accessible | Select this check box so that the cluster can be accessed from a public network.<br><br>This check box is available when Create cluster or Restore from snapshot is selected from the Action list. |
| Set public ip address | Select this check box and in the field displayed enter the Elastic IP (EIP) address for the cluster.<br><br>This check box is available only when the Publicly accessible check box is selected. |
| Availability zone | Enter the EC2 Availability Zone in which you want Amazon Redshift to provision the cluster.<br><br>This field is available when Create cluster or Restore from snapshot is selected from the Action list. |
| VPC security group ids | Enter Virtual Private Cloud (VPC) security groups to be associated with the cluster and separate them with a comma, for example, *gname1, gname2, gname3*.<br><br>This field is available when Create cluster or Restore from snapshot is selected from the Action list. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at the Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | CLUSTER\_FINAL\_ID:<br>the ID of the cluster. This is an After variable and it returns a string.<br><br><br>ENDPOINT: the endpoint address of the cluster. This is an After<br>variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | tAmazonRedshiftManage is usually used as a standalone component. |
