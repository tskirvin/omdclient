# check\_mk + ENC hooks - want to be able to control when we re-inventory a host

Right now, the omdclient Puppet ENC hook that connects to check\_mk
re-inventories the host every time there is a change in the ENC.  It would
be helpful if there was a way to override this; we *generally* want to
re-inventory, but not every time.  And there are (probable) bugs on the
check\_mk side that (e.g.) clear all 'acks' from a re-inventoried host.
