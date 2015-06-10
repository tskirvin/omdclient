#########################################################################
### cms-cmk-api #########################################################
#########################################################################

#########################################################################
### Configuration #######################################################
#########################################################################

SERVER?=https://ecfmon1.fnal.gov/dcsomon
API_USER?=dcso-api
PASS?=IJRKUMWVWKKWLKQGWQR@

HOST=NONE

URL_BASE=${SERVER}/check_mk/webapi.py
URL_AUTH=_username=${API_USER}&_secret=${PASS}

#########################################################################
### Functions ###########################################################
#########################################################################

default: hostinfo

## activate - deploy changes made by the API to date

activate:
	@curl -s -H 'Accept: application/json' \
	    '$(URL_BASE)?action=activate_changes&$(URL_AUTH)' \
	    -d '' | jq . ;

## delete-host

delete-host:
	if [[ $(HOST) == 'NONE' ]]; then \
	    echo "Usage: make delete-host HOST=..." ; \
	else \
	    curl -s -H 'Accept: application/json' \
	        '$(URL_BASE)?action=delete_host&$(URL_AUTH)' \
		    -d 'request={"hostname": "$(HOST)"}' | jq . ; \
	fi

## discover - re-scan the services of a given host

discover:
	@if [[ $(HOST) == 'NONE' ]]; then \
	    echo "Usage: make discover HOST=..." ; \
	else \
	    curl -s -H 'Accept: application/json' \
	        '$(URL_BASE)?action=discover_services&$(URL_AUTH)' \
		    -d 'request={"hostname": "$(HOST)"}' | jq . ; \
	fi

## hostinfo - print information about a given host

hostinfo:
	@if [[ $(HOST) == 'NONE' ]]; then \
	    echo "Usage: make hostinfo HOST=..." ; \
	else \
	    curl -s -H 'Accept: application/json' \
	        '$(URL_BASE)?action=get_host&$(URL_AUTH)' \
		    -d 'request={"hostname": "$(HOST)"}' | jq . ; \
	fi

## hostinfo-all

hostinfo-all:
	@curl -s -H 'Accept: application/json' \
	    '$(URL_BASE)?action=get_all_hosts&$(URL_AUTH)' \
	    | jq . ;

