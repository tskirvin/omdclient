"""
Shared functions for interacting with an OMD site remotely.
"""

#########################################################################
### Configuration #######################################################
#########################################################################

config = {}

#########################################################################
### Declarations ########################################################
#########################################################################

import datetime, json, optparse, os, re, ssl, sys, urllib, urllib2, yaml
from bs4 import BeautifulSoup
from pprint import pprint

#########################################################################
### Script Helpers ######################################################
#########################################################################

def loadCfg(config_file):
    """
    Load a .yaml configuration file into the config hash.
    """

    try:
        config = yaml.load(open(config_file, 'r'))
    except IOError, exc:
        raise Exception('%s' % exc)
    except yaml.YAMLError, exc:
        raise Exception('yaml error: %s' % exc)
        sys.exit (3)
    except:
        raise Exception('unknown error: %s' % exc)
        sys.exit (3)

    return config

def generateParser (text, usage_text, config):
    """
    Generate an OptionParser object for use across all scripts.  We want
    something consistent so we can use the same server/site/user options
    globally.
    """
    p = optparse.OptionParser(usage=usage_text, description=text)
    p.add_option('--debug', dest='debug', action='store_true',
        default=False, help='set to print debugging information')
    group = optparse.OptionGroup(p, "connection options")
    group.add_option('--server', dest='server', default=config['server'],
        help='server name (default: %default)')
    group.add_option('--site', dest='site', default=config['site'],
        help='site name (default: %default)')
    group.add_option('--user', dest='user', default=config['user'],
        help='user name (default: %default)')
    group.add_option('--apikey', dest='apikey', default=config['apikey'],
        help='api key (not printing the default)')
    p.add_option_group(group)
    return p


def parserArgDict(opthash):
    """
    Converts the data from the OptionParser object into a dictionary
    object, so that we can easily use it elsewhere.
    """
    args = {
        'apikey': opthash.apikey,
        'debug':  opthash.debug,
        'server': opthash.server,
        'site':   opthash.site,
        'user':   opthash.user
    }
    return args

#########################################################################
### URL Management ######################################################
#########################################################################

def generateUrl (action, args):
    """
    Generate the URL used to interact with the server.
       action   What action are we taking?  Valid options:

           activate_changes
           add_host
           delete_host
           discover_services
           get_all_hosts
           get_host

       args     Argument dict.  You must have at least these keys:

           apikey
           server
           site
           user

                ...and you can optionally include:

           effective_attributes      For 'get_host'
           foreign_ok                For 'activate_changes'
           create_folders            For 'add_host'

    If 'debug' is set, we'll print the URL to stdout (with the password
    blanked out).
    """
    baseurl = 'https://%s/%s/check_mk/webapi.py?_username=%s' % \
        (args['server'], args['site'], args['user'])
    url_parts = [baseurl]

    if action == 'activate_changes':
        url_parts.append('action=activate_changes')
        url_parts.append('mode=dirty')
        if 'foreign_ok' in args.keys():
            if args['foreign_ok']: url_parts.append('allow_foreign_changes=1')

    elif action == 'add_host':
        url_parts.append('action=add_host')
        if 'create_folders' in args.keys():
            if args['create_folders']: url_parts.append('create_folders=0')

    elif action == 'delete_host':
        url_parts.append('action=delete_host')

    elif action == 'edit_host':
        url_parts.append('action=edit_host')

    elif action == 'discover_services':
        url_parts.append('action=discover_services')
        if 'tabula_rasa' in args.keys():
            if args['tabula_rasa']: url_parts.append('mode=refresh')

    elif action == 'get_all_hosts':
        url_parts.append('action=get_all_hosts')

    elif action == 'get_host':
        url_parts.append('action=get_host')
        if 'effective_attributes' in args.keys():
            url_parts.append('effective_attributes=%s' \
                % args['effective_attributes'])

    else:
        raise Exception('invalid action: %s' % action)

    if args['debug']:
        url_parts_clean = url_parts
        url_parts_clean.append('_secret=...')
        print "url: %s" % '&'.join(url_parts_clean)

    url_parts.append ('_secret=%s' % args['apikey'])

    return '&'.join(url_parts)

def loadUrl (url, request_string):
    """
    Load the URL and request string pair.  Returns a urllib2 response.
    """
    try:
        response = urllib2.urlopen(url, request_string)
    except urllib2.HTTPError, err:
        if err.code == 404:
            raise Exception('Page not found')
        elif err.code == 403:
            raise Exception('Access Denied')
        else:
            raise Exception('http error, code %s' % err.code)
    except urllib2.URLError, err:
        raise Exception('url error: %s' % err.reason)
    return response

def processUrlResponse(response, debug):
    """
    Process the response from loadUrl().  Returns two objects: did we get
    a 'True' response from the server, and the response itself.

    If 'debug' is set, we'll print a lot of extra debugging information.

    Code taken from Ed Simmonds <esimm@fnal.gov>.
    """

    data=response.read()

    try:
        jsonresult=json.loads(data)
        if debug: pprint(jsonresult)
    except ValueError:
        soup=BeautifulSoup(data, 'lxml')
        div1=soup.find('div', attrs={'class':'error'})
        if div1 != None:
            print "Error returned"
            print div1.string
            return False, None
        else:
            print "ValueError.  Invalid JSON object returned, and could not extract error.  Full response was:"
            print data
            return False, None

    if jsonresult['result_code']==0:
        return True, jsonresult['result']
    else:
        if debug: print "result code was: %s" % jsonresult['result_code']
        return False, jsonresult['result']

    return False, result

#########################################################################
### WATO API Interactions ###############################################
#########################################################################

def activateChanges(arghash):
    """
    Activate changes.  This can be slow.
    """
    url = generateUrl('activate_changes', arghash)
    response = loadUrl(url, '')
    return processUrlResponse(response, arghash['debug'])

def createHost(host, arghash):
    """
    Create a host entry.

        folder      Default: omdclient-api
        role
        instance
        extra
    """

    request = {}
    request['hostname'] = host

    if 'folder' in arghash: request['folder'] = arghash['folder']
    else:                   request['folder'] = 'omdclient-api'

    attributes = {}
    if 'role' in arghash:
        if arghash['role'] != 'UNSET':
            attributes['tag_role']     = arghash['role']
    if 'instance' in arghash:
        if arghash['instance'] != 'UNSET':
            attributes['tag_instance'] = arghash['instance']
    if 'ip' in arghash:
        if arghash['ip'] != 'UNSET':
            attributes['ipaddress'] = arghash['ip']
    if 'extra' in arghash:
        if arghash['extra'] != 'UNSET' and '=' in arghash['extra']:
          import shlex
          attributes.update(dict(token.split('=') for token in shlex.split(arghash['extra'])))
    request['attributes'] = attributes

    url = generateUrl ('add_host', arghash)

    request_string = "request=%s" % json.dumps(request)
    if arghash['debug']: print request_string

    response = loadUrl(url, request_string)
    return processUrlResponse(response, arghash['debug'])

def readHost(host, arghash):
    """
    Get information about a host.
    """
    url = generateUrl ('get_host', arghash)

    request_string='request={"hostname" : "%s"}' % ( host )
    response = loadUrl(url, request_string)
    return processUrlResponse(response, arghash['debug'])

def updateHost(host, arghash):
    """
    Update information from a host.  If the host does not already exist,
    we'll call createHost instead.
    """

    if readHost(host, arghash): pass
    else:
        return createHost(host, arghash)

    url = generateUrl ('edit_host', arghash)

    request = {}
    request['hostname'] = host

    attributes = {}
    if 'role' in arghash:
        if arghash['role'] != 'UNSET':
            attributes['tag_role']     = arghash['role']
    if 'instance' in arghash:
        if arghash['instance'] != 'UNSET':
            attributes['tag_instance'] = arghash['instance']
    if 'ip' in arghash:
        if arghash['ip'] != 'UNSET':
            attributes['ipaddress'] = arghash['ip']
    if 'extra' in arghash:
        if arghash['extra'] != 'UNSET' and '=' in arghash['extra']:
            import shlex
            attributes.update(dict(token.split('=') for token in shlex.split(arghash['extra'])))
    request['attributes'] = attributes

    if 'unset' in arghash:
        request['unset_attributes'] = [ arghash['unset'] ]

    request_string = "request=%s" % json.dumps(request)
    if arghash['debug']: print request_string

    response = loadUrl(url, request_string)
    return processUrlResponse(response, arghash['debug'])

def listHosts(arghash):
    """
    List all hosts.
    """
    url = generateUrl('get_all_hosts', arghash)
    response = loadUrl(url, '')
    return processUrlResponse(response, arghash['debug'])

def listHostsFiltered(filter, arghash):
    """
    List all hosts filtered by site.
    """
    url = generateUrl('get_all_hosts', arghash)
    response = loadUrl(url, '')
    status, response = processUrlResponse(response, arghash['debug'])
    response_filtered = dict(response)
    for h in response:
        if response[h].get('attributes',{}).get('site','') != filter:
            del response_filtered[h]
    return status, response_filtered

def deleteHost(host, arghash):
    """
    Remove a host from check_mk.
    """
    url = generateUrl('delete_host', arghash)
    request_string='request={"hostname" : "%s"}' % ( host )
    response = loadUrl(url, request_string)
    return processUrlResponse(response, arghash['debug'])

def discoverServicesHost(host, arghash):
    """
    Scan a host for services.
    """
    url = generateUrl('discover_services', arghash)
    request_string='request={"hostname" : "%s"}' % ( host )
    response = loadUrl(url, request_string)
    return processUrlResponse(response, arghash['debug'])

#########################################################################
### Nagios API Commands #################################################
#########################################################################

def generateNagiosUrl (action, args):
    """
    Generate the URL used to interact with the server.
       action   What action are we taking?  Valid options:

           ack
           downtime
           hostreport
           svcreport

       args     Argument dict.  You must have at least these keys:

           apikey
           server
           site
           user
           view_name

                ...and you can optionally include:

            ack     Associated with hostreport and svcreport; if set,
                    we will only load acknowledged (1) or unacknowledged
                    (0) alerts.
            end     Associated with 'downtime': a datetime object
                    indicating the end of the work.  If not offered,
                    we'll use start + 'hours' hours.
            hours   Associated with 'downtime'; indicates a number of
                    hours of downtime.  Used if we don't have a set
                    'end' time.
            host    Associated with 'downtime' and 'ack': hostname.
            service Associated with 'downtime' and 'ack': service name.
            start   Associated with 'downtime'; a datetime object
                    indicating the start of the work.  If not offered,
                    we'll just use 'now()'.
            type    Associated with 'ack' or 'downtime'; must be one of
                    'host' or 'service'.

    If 'debug' is set, we'll print the URL to stdout (with the password
    blanked out).
    """
    baseurl = 'https://%s/%s/check_mk/view.py' % (args['server'], args['site'])
    url_parts = {}
    url_parts['_username']     = args['user']
    url_parts['_secret']       = args['apikey']
    url_parts['output_format'] = 'json'

    if action == 'hostreport':
        url_parts['view_name'] = 'hostproblems_expanded'
        if 'ack' in args.keys():
            url_parts['is_host_acknowledged'] = args['ack']

    elif action == 'svcreport':
        url_parts['view_name'] = 'svcproblems_expanded'
        if 'ack' in args.keys():
            url_parts['is_service_acknowledged'] = args['ack']

    elif action == 'downtime':
        url_parts['_transid'] = '-1'
        url_parts['_do_confirm'] = 'yes'
        url_parts['_do_actions'] = 'yes'

        if 'start' in args.keys(): start = args['start']
        else:                      start = datetime.datetime.now()
        if 'end' in args.keys():   end   = args['end']
        else:
            end = start + datetime.timedelta(hours=int(args['hours']))

        url_parts['_down_custom']    = 'Custom+time_range'
        url_parts['_down_from_date'] = start.date()
        url_parts['_down_from_time'] = start.strftime('%H:%M')
        url_parts['_down_to_date']   = end.date()
        url_parts['_down_to_time']   = end.strftime('%H:%M')
        url_parts['_down_comment']   = args['comment']

        if args['type'] == 'host':
            url_parts['host']      = args['host']
            url_parts['view_name'] = 'hoststatus'
        elif args['type'] == 'svc' or args['type'] == 'service':
            url_parts['host']      = args['host']
            url_parts['service']   = args['service']
            url_parts['view_name'] = 'service'
        else:
            raise Exception('invalid downtime type: %s' % args['type'])

    elif action == 'ack':
        url_parts['_transid'] = '-1'
        url_parts['_do_confirm'] = 'yes'
        url_parts['_do_actions'] = 'yes'

        url_parts['_ack_comment'] = args['comment']
        url_parts['_acknowledge'] = 'Acknowledge'
        if args['type'] == 'host':
            url_parts['host']      = args['host']
            url_parts['view_name'] = 'hoststatus'
        elif args['type'] == 'svc' or args['type'] == 'service':
            url_parts['host']      = args['host']
            url_parts['service']   = args['service']
            url_parts['view_name'] = 'service'
        else:
            raise Exception('invalid ack type: %s' % args['type'])

    else:
        raise Exception('invalid action: %s' % action)

    if args['debug']:
        url_parts_clean = dict(url_parts)
        url_parts_clean['_secret'] = '...'
        print "url: %s?%s" % (baseurl, urllib.urlencode(url_parts_clean))

    url = "%s?%s" % (baseurl, urllib.urlencode(url_parts))
    return url


def nagiosAck(params):
    """
    Acknowledge an alert in Nagios.  Returns a report, but the report may
    not be very helpful.
    """
    url = generateNagiosUrl('ack', params)
    response = loadUrl(url, '')
    return processNagiosReport(response, params['debug'])

def nagiosDowntime(params):
    """
    Schedule downtime in Nagios.  Returns a report, but the report may
    not be very helpful.
    """
    url = generateNagiosUrl('downtime', params)
    response = loadUrl(url, '')
    return processNagiosReport(response, params['debug'])

def nagiosReport(type, argdict):
    """
    Generate a nagios report.  Type can be one of 'svc_ack', 'svc_unack',
    'host_ack', or 'host_unack'.
    """
    args = argdict.copy()
    if   type == 'svc_ack':
        action = 'svcreport'
        args['ack'] = 1
    elif type == 'svc_unack':
        action = 'svcreport'
        args['ack'] = 0
    elif type == 'host_ack':
        action = 'hostreport'
        args['ack'] = 1
    elif type == 'host_unack':
        action = 'hostreport'
        args['ack'] = 0
    elif type == 'host':
        action = 'hostreport'
    elif type == 'hostservice':
        action = 'svcreport'
    else:
        raise Exception('invalid report type: %s' % type)

    url = generateNagiosUrl (action, args)
    response = loadUrl(url, '')
    return processNagiosReport(response, argdict['debug'])

def processNagiosReport(response, debug):
    """
    Process the response from loadUrl().  Returns an array of matching
    objects, where we've trimmed off the first one (which described the
    fields of the later objects).

    If 'debug' is set, we'll print a lot of extra debugging information.

    Incidentally, we're doing some really ugly stuff here because check_mk
    isn't always returning with json, even when we ask it to.
    """

    data=response.read()

    try:
        jsonresult=json.loads(data)
        if debug: pprint(jsonresult)
    except ValueError:
        lines = data.split('\n')
        if re.match('^MESSAGE: .*$', lines[0]):
            return lines[0]
        soup=BeautifulSoup(data, 'lxml')
        div1=soup.find('div', attrs={'class':'error'})
        if div1 != None:
            print "Error returned"
            print div1.string
            return []
        else:
            print "ValueError.  Invalid JSON object returned, and could not extract error.  Full response was:"
            print data
            return []

    if len(jsonresult) <= 1: return []

    headers = jsonresult.pop(0)
    return jsonresult
