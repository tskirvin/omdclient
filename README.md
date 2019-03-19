# omdclient

omdclient provides a suite of command-line tools to interact with the APIs
associated with the `check_mk`/Open Monitoring Distribution tool suite.

## WATO APIs

WATO is used to create, remove, and modify entries within the OMD user
suite.  This is documented at:

<http://mathias-kettner.com/checkmk_wato_webapi.html>

### omd-activate

Activates changes made by the API user.

### omd-bulkimport

Takes a list of hosts on STDIN and adds them to a specific folder in OMD.

### omd-host-crud

Creates/Reads/Updates/Deletes entries from an existing monitoring
interface.

### omd-host-tag

update/remove a given host tag in OMD

### omd-reinventory

Reinventory a host in OMD.

## Multisite/Nagios

<https://mathias-kettner.de/checkmk_multisite_automation.html>

### omd-nagios-ack

Acknowledges host/service alerts from the command-line.

### omd-nagios-downtime

Schedules host/service downtimes from the command-line.

### omd-nagios-hostlist

Print a list of all hosts in the given nagios instance.

### omd-nagios-hosts-with-problem

Print a list of hosts that are currently exhibiting a specific problem.

### omd-nagios-report

Prints a human-readable report on current host and service alerts.

## Setup / How To Use

### /etc/omdclient/config.yaml

You'll have to populate this file on your own:

    server: 'xxxxxx.example'
    site: 'xxxxxx'
    user: 'xxxx-api'
    apikey: 'xxxxxx'

If you set the 'OMDCONFIG' environment variable you can point at different
configs, e.g.:

    OMDCONFIG=/tmp/myconfig.yaml omd-activate

### Configuration of 'expanded views'

The report scripts depend on 'expanded view' versions of the
`hostproblems` and `svcproblems` views, which add comments.  In order to
add these, you generally have to:

1.  Edit view `hostproblems` - it's a default view, so you'll go to 'clone'.
    * Change the name from `hostproblems` to `hostproblems_expanded`.
    * Update the list of columns to read:
        1. Hostname
        2. Host icons
        3. Host state
        4. Output of host check plugin
        5. Number of services in state OK
        6. Number of services in state WARN
        7. Number of services in state UNKNOWN
        8. Number of services in state CRIT
        9. Number of services in state PENDING
        10. The age of the current host state
        11. Host comments
    * (newer versions) set to 'public' and 'hidden'.
    * Save.
2.  Edit the view `svcproblems` and created `svcproblems_expanded`, same
    as above but just add the column `Service Comments`.

In newer versions of check\_mk, you may also need to make these views
Public (check `Visibility` / `Make this view available for other users` /
`Publish to all users`).  Also, the `hostproblems` base view may have
changed: I have for `hostproblems_expanded`:

(Thanks to Christian Bryn - https://github.com/epleterte - for the docs!)

## How To Build

There is a `Makefile.bak` and a `*.spec` file that mirrors my local build
process for RPMs, if this matches your requirements; just run
`make -f Makefile.bak build-nomock`.

Otherwise, you may want to just follow the general instructions
in `*.spec`.  Scripts from `usr/bin/*` go into your path; create
`/etc/omdclient/config.yaml` as described above; make man pages with
`pod2man` if you're ambitious; and run `python setup.py install` to
install the python library.

### Debian

    make -f Makefile.deb build

That should build a full .deb package.
