# omdclient

omdclient provides a suite of command-line tools to interact with the APIs
associated with the `check_mk`/Open Monitoring Distribution tool suite.

## check\_mk API

<https://docs.checkmk.com/latest/en/rest_api.html>

This interface has been standard since about check\_mk 2.0.  It's more
powerful and more complex than their old WATO API.

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

## How To Build

There is a `Makefile.bak` and a `*.spec` file that mirrors my local build
process for RPMs, if this matches your requirements; just run
`make -f Makefile.bak build-nomock`.

Otherwise, you may want to just follow the general instructions
in `*.spec`.  Scripts from `usr/bin/*` go into your path; create
`/etc/omdclient/config.yaml` as described above; make man pages with
`pod2man` if you're ambitious; and run `python setup.py install` to
install the python library.

Also possible to do it all with pipx:

    pipx install .
    pipx runpip omdclient install -r requirements.txt

### Debian

    make -f Makefile.deb build

That should build a full .deb package.
