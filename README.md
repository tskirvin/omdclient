# omdclient

omdclient provides a suite of tools to interact with the APIs associated
with the `check_mk`/Open Monitoring Distribution tool suite


## WATO APIs

WATO is used to create, remove, and modify entries within the OMD user
suite.  This is documented at:

http://mathias-kettner.com/checkmk_wato_webapi.html

### omd-host-crud

Creates/Reads/Updates/Deletes entries from an existing monitoring
interface.

### omd-activate

Activates changes made by the API user.

### omd-puppet-enc

Provides a linkage between a puppet External Node Classifier (ENC) and a
monitoring instance.  In essence, we want to add hosts to monitoring when
a host is added to puppet; remove the host from monitoring when the host
is removed from puppet; and re-tag the host when its role changes.  

https://docs.puppetlabs.com/guides/external_nodes.html

## Multisite/Nagios

https://mathias-kettner.de/checkmk_multisite_automation.html

### omd-nagios-ack

Acknowledges host/service alerts from the command-line.

### omd-nagios-downtime

Schedules host/service downtimes from the command-line.

### omd-nagios-report

Prints a human-readable report on current host and service alerts. 

## How To Use

### /etc/omdclient/config.yaml

You'll have to populate this file on your own:

    server: 'xxxxxx.example'
    site: 'xxxxxx'
    user: 'xxxx-api'
    apikey: 'xxxxxx'

### Adding Expanded Views

omdclient expects some non-default views to be available in Check MK. These views expand on the normal _hostproblems_ and _serviceproblems_ views by adding a 'comment' column.
They can both be made manually by following these steps:

* Login to your Check MK instance
* Open 'Host Problems'
* Edit the view - since this is a default view, you will automatically be taken to 'clone' the view rather than edit. 
  * Change the name of the view from _hostproblems_ to _hostproblems_expanded_ 
  * Go down to the list of columns, and add one more: "Host comments" (find the appropriate column entry).
* Repeat the above for _serviceproblems_, add column 'Service Problems'
