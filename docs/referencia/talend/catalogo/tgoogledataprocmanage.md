# tgoogledataprocmanage

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tgoogledataprocmanage  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tgoogledataprocmanage -->

# tGoogleDataprocManage

Creates or deletes a Dataproc cluster in the Global region on Google Cloud Platform.

## tGoogleDataprocManage Standard properties

These properties are used to configure tGoogleDataprocManage running in the Standard Job framework.

The Standard tGoogleDataprocManage component belongs to the Cloud family.

The component in this framework is available in all Talend products with Big Data and in Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Project ID | Enter the ID of your Google Cloud Platform project.<br><br>If you are not certain about your project ID, confirm it in the Manage<br>Resources page of your Google Cloud Platform services. |
| Cluster ID | Enter the ID of your Dataproc cluster to be used. |
| Provide Google Credentials in file | Leave this check box clear, when you<br>launch your Job from a given machine in which Google Cloud SDK has been<br>installed and authorized to use your user account credentials to access<br>Google Cloud Platform. In this situation, this machine is often your<br>local machine.<br><br>When you launch<br>your Job from a remote machine, such as a Talend JobServer, select this check box and in the Path to Google<br>Credentials file field that is displayed, enter the<br>directory in which this JSON file is stored in the Talend JobServer machine. You can also click the [...] button,<br>and then in the pop-up dialog box, browse for the JSON file.<br><br>For further information about this Google<br>Credentials file, see the administrator of your Google Cloud Platform or<br>visit [Google Cloud Platform Auth<br>Guide](https://cloud.google.com/docs/authentication). |
| Action | Select the action you want tGoogleDataprocManage to<br>perform on the your cluster:<br><br><ul> <li> <p> <kbd>Start</kbd> to create a cluster</p> </li> <li> <p> <kbd>Stop</kbd> to destroy a cluster</p> </li> </ul> |
| Version | Select the version of the image to be used to create a Dataproc cluster. |
| Region | From this drop-down list, select the Google Cloud region to<br>be used. |
| Zone | Select the geographic zone in which the computing resources<br>are used and your data is stored and processed. The available zones vary<br>depending on the region you have selected from the<br>Regional drop-down list.<br><br>A zone in terms of Google Cloud is an isolated location<br>within a region, another geographical term employed by Google Cloud. |
| Instance configuration | Enter the parameters to determine how many masters and workers to be used by<br>the Dataproc cluster to be created and the performance of these masters and<br>workers. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Wait for cluster ready | Select this check box to keep this component running until the cluster is<br>completely set up.<br><br>When you clear this check box, this component stops running immediately after<br>sending the command to create. |
| Master disk size | Enter a number without quotation marks to determine the size of the disk of<br>each master instance. |
| Master local SSD | Enter a number without quotation marks to determine the number of local<br>solid-state drive (SSD) storage devices to be added to each master<br>instance.<br><br>According to Google, these local SSDs are suitable only<br>for temporary storage such as caches, processing space or low value data. It<br>is recommended to store important data to durable storage options of Google.<br>For further information about the Google storage options, see [Durable storage options](https://cloud.google.com/compute/docs/disks/). |
| Worker disk size | Enter a number without quotation marks to determine the size of the disk of<br>each worker instance. |
| Worker local SSD | Enter a number without quotation marks to determine the number of local<br>solid-state drive (SSD) storage devices to be added to each worker<br>instance.<br><br>According to Google, these local SSDs are suitable only<br>for temporary storage such as caches, processing space or low value data. It<br>is recommended to store important data to durable storage options of Google.<br>For further information about the Google storage options, see [Durable storage options](https://cloud.google.com/compute/docs/disks/). |
| Network or Subnetwork | Select either check box to use a Google Compute Engine network or subnetwork<br>for the cluster to be created to enable intra-cluster communications.<br><br>As Google does not allow network and subnetwork to be used concurrently,<br>selecting one check box hides the other check box.<br><br>For further information about Google Dataproc cluster network configuration,<br>see [Dataproc Network](https://cloud.google.com/dataproc/docs/concepts/network). |
| Internal IP only | Select the check box to configure all instances in the cluster to have only<br>internal IP addresses.<br><br>The subnetwork of the cluster must have Private Google Access enabled to<br>allow cluster nodes to access Google APIs and services from internal<br>IPs.<br><br>For more information, see [Dataproc Cluster Network Configuration](https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/network#create_a_cloud_dataproc_cluster_with_internal_ip_address_only). |
| Initialization action | In this table, select the initialization actions that are available in the<br>shared bucket on Google Cloud Storage to run on all the nodes in your<br>Dataproc cluster immediately after this cluster is set up.<br><br>If you need to use custom initialization scripts, upload them to this shared<br>Google bucket so that tGoogleDataprocManage can read<br>them.<br><br><ul> <li> <p>In the <span>Executable file</span> column, enter the                                Google Cloud Storage URI to these scripts to be used, for example                                    <span>gs://dataproc-initialization-actions/MyScript</span> </p> </li> <li> <p>In the <span>Executable timeout</span> column, enter the                                amount of time in double quotation marks to determine the duration                                of the execution. If the executable is not completed at the end of                                this timeout, an explanatory error message is returned. The value is                                a string with up to nine fractional digits, for example,                                "3.5s" for 3.5 seconds.</p> </li> </ul><br><br>For further information about this shared bucket and the initialization<br>actions, see [Initialization actions](https://cloud.google.com/dataproc/docs/concepts/init-actions). |
| tStatCatcher Statistics | Select this check box to collect log data at the component level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used standalone in a subJob. |
