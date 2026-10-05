"""
Shared functions for interacting with an OMD site remotely.
"""

# https://docs.checkmk.com/latest/en/rest_api.html

#########################################################################
### Configuration #######################################################
#########################################################################

config = {}

API_URL_BASE = 'https://%s/%s/check_mk/api/1.0'

HOST_STATE = { 0: 'UP', 1: 'DOWN', 2: 'UNREACHABLE' }
SVC_STATE  = { 0: 'UP', 1: 'WARN', 2: 'CRIT', 3: 'UNKNOWN' }

#########################################################################
### Declarations ########################################################
#########################################################################

import datetime, json, optparse, re, requests, sys, yaml
from pprint import pprint

#########################################################################
### Script Helpers ######################################################
#########################################################################

def loadCfg(config_file):
    """
    Load a .yaml configuration file into the config hash.
    """

    try:
        config = yaml.safe_load(open(config_file, 'r'))
    except IOError as exc:
        raise Exception('%s' % exc)
    except yaml.YAMLError as exc:
        raise Exception('yaml error: %s' % exc)
        sys.exit(3)
    except Exception as exc:
        raise Exception('unknown error: %s' % exc)
        sys.exit(3)

    return config

def generateParser(text, usage_text, config):
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
    group.add_option('--remove', action="store_true", dest='remove', default=False,
        help='removes a downtime')
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
        'user':   opthash.user,
        # 'remove': opthash.remove
    }
    return args

#########################################################################
### URL Management ######################################################
#########################################################################

def generateRequests(action, args):
    """
    Generate the Requests call data used to interact with the server.
    Returns a URL, a headers hash, and a json content hash.

       action   What action are we taking?  Valid options:

           activate_changes
           create_host
           delete_host
           discover_services
           get_all_hosts
           get_host
           update_host

       args     Argument dict.  You must have at least these keys:

           apikey
           server
           site
           user

                ...and you can optionally include:

           effective_attributes      For 'get_host'
           foreign_ok                For 'activate_changes'
           create_folders            For 'add_host'

           hostname

    If 'debug' is set, we'll print the fields to stdout (with the password
    blanked out).
    """
    baseurl = 'https://%s/%s/check_mk/api/1.0' \
        % (args['server'], args['site'])
    headers = {
        'Authorization': ("Bearer %s %s" % (args['user'], args['apikey'])),
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    content = {}

    if action == 'activate_changes': # TODO
        url = baseurl + f"/domain-types/activation_run/actions/activate-changes/invoke"
        content['sites'] = [ args['site'] ]
        if 'foreign_ok' in list(args.keys()):
            if args['foreign_ok']:
                content['force_foreign_changes'] = True

    elif action == 'create_host': # TODO
        url_parts.append('action=add_host')
        if 'create_folders' in list(args.keys()):
            if args['create_folders']: url_parts.append('create_folders=0')

    elif action == 'delete_host': # TODO
        url_parts.append('action=delete_host')

    elif action == 'discover_services': # TODO
        url = baseurl + '/domain-types/service_discovery_run/actions/start/invoke'

    elif action == 'get_all_hosts':
        url = baseurl + '/domain-types/host_config/collections/all'

    elif action == 'get_host': # TODO
        url_parts.append('action=get_host')
        if 'effective_attributes' in list(args.keys()):
            url_parts.append('effective_attributes=%s'
                % args['effective_attributes'])

    elif action == 'update_host':
        hostname = args['host_name']
        url = baseurl + '/objects/host_config/' + hostname

    else:
        raise Exception('invalid action: %s' % action)

    if args['debug']:
        print(("url: %s" % url), file=sys.stderr)
        headers_clean = dict(headers)
        headers_clean['Authorization'] = '...'
        print(("headers: ", headers_clean), file=sys.stderr)
        print(("base content: ", content), file=sys.stderr)

    return url, headers, content

def loadRequestsGet(url, headers, code):
    """
    Load a requests get() call with url/headers/code.  Returns a requests 
    response, to be parsed elsewhere.
    """
    session = requests.session()
    session.max_redirects = 100
    session.headers['Accept'] = 'application/json'
    response = session.get (
        url,
        headers=headers,
        json=code,
        allow_redirects=True
    )

    return response

def loadRequestsPut(url, headers, code):
    """
    Load a requests post() call with url/headers/code.  Returns a requests 
    response, to be parsed elsewhere.
    """
    session = requests.session()
    session.max_redirects = 100
    session.headers['Accept'] = 'application/json'
    response = session.post (
        url,
        headers=headers,
        json=code,
        allow_redirects=True
    )

    return response

def processRequestsResponse(response, debug):
    """
    Process the response from loadRequests().  Returns two objects: did we get
    a 'True' response from the server, and the response itself.

    If 'debug' is set, we'll print a lot of extra debugging information.

    This is meant to be a "generic" setup.  I don't love it.  It may go away.
    """

    try:
        json = response.json()
    except:
        json = {}

    if debug:
        print('response: ', response)
        print('headers: ', response.headers)
        print('json: ', json)

    if response.status_code in (200, 201):
        return True, response.json()
    elif response.status_code == 204:
        return True, {}
    elif response.status_code == 303:
        print('Redirected to', response.headers['location'])
    elif 'detail' in response.json():
        return False, response.json()['detail']
    elif response.status_code == 400:
        return False, response.json()
    else:
        raise RuntimeError(pprint.pformat(response.json()))

    return False, {}

#########################################################################
### WATO API Interactions ###############################################
#########################################################################

def activateChanges(arghash):
    """
    Activate changes.  This can be slow.
    """
    url, headers, content = generateRequests('activate_changes', arghash)
    response = loadRequestsPut(url, headers, content)
    return processRequestsResponse(response, arghash['debug'])

def createHost(host, arghash):
    """
    Create a host entry.

        folder      Default: omdclient-api
        role
        instance
        extra

    Note that `tag_role` and `tag_instance` are tags used locally to tie
    together local local puppet instance and our OMD folders.  You don't
    have to use them and may cheerfully ignore them.
    """

    request = {}
    request['hostname'] = host

    if 'folder' in arghash: request['folder'] = arghash['folder']
    else:                   request['folder'] = 'omdclient-api'

    attributes = {}
    if 'role' in arghash:
        if arghash['role'] != 'UNSET':
            attributes['tag_role'] = arghash['role']
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

    url = generateUrl('add_host', arghash)

    request_string = "request=%s" % json.dumps(request)
    if arghash['debug']: print(request_string)

    response = loadUrl(url, request_string)
    return processUrlResponse(response, arghash['debug'])

def readHost(host, arghash):
    """
    Get information about a host.
    """
    url = generateUrl('get_host', arghash)

    request_string = 'request={"hostname" : "%s"}' % (host)
    response = loadUrl(url, request_string)
    return processUrlResponse(response, arghash['debug'])

def updateHost(host, arghash):
    """
    Update information from a host.  If the host does not already exist,
    we'll call createHost instead.
    """

    arghash['host_name'] = host

    print(arghash)

    # if readHost(host, arghash): pass
    # else:
        # # return createHost(host, arghash)

    url, headers, content = generateRequests('update_host', arghash)

    create_attributes = {}
    attributes = {}

    if 'attributes' in arghash:
        content['attributes'] = [arghash['attributes']]
    if 'update_attributes' in arghash:
        content['update_attributes'] = [arghash['update_attributes']]
    if 'unset_attributes' in arghash:
        content['unset_attributes'] = [arghash['unset_attributes']]

    response = loadRequestsPut(url, headers, content)

    print (processRequestsResponse(response, arghash['debug']))

def listHosts(filt, arghash):
    """
    List all hosts.  Returns the json that is generated, which is a lot of
    data.
    """
    debug = arghash['debug']

    url, headers, content = generateRequests('get_all_hosts', arghash)

    # content['fields'] = '(title)'
    content['include_links'] = False
    content['site'] = arghash['site']
    content['effective_attributes'] = False
    if filt: content['hostname'] = filt

    if debug: print(('content: ', content), file=sys.stderr)
    response = loadRequestsGet(url, headers, content)

    try:
        json = response.json()
    except:
        json = {}

    if debug:
        print(('response: ', response), file=sys.stderr)
        print(('json: ', pprint(json)), file=sys.stderr)

    if response.status_code == 200:
        return json
    elif response.status_code == 303:
        print(('Redirect to', response.headers['location']), file=sys.stderr)
    elif 'detail' in json:
        raise RuntimeError("error: %s" % json['detail'])
    else:
        raise RuntimeError(response.status_code)

def deleteHost(host, arghash):
    """
    Remove a host from check_mk.
    """
    url = generateUrl('delete_host', arghash)
    request_string = 'request={"hostname" : "%s"}' % (host)
    response = loadUrl(url, request_string)
    return processUrlResponse(response, arghash['debug'])

def discoverServicesHost(host, arghash):
    """
    Scan a host for services.
    """
    url, headers, content = generateRequests('discover_services', arghash)
    content['host_name'] = host
    if 'tabula_rasa' in arghash: content['mode'] = 'refresh'
    response = loadRequestsPut(url, headers, content)

    try:
        json = response.json()
    except:
        json = {}

    debug = arghash['debug']
    if debug:
        print('response: ', response)
        # print('headers: ', response.headers)
        print('json: ', json)

    if response.status_code == 200:
        return True, 'inventory complete'
    if response.status_code == 204:     # the API does not know about this code but it seems to be a default answer
        return True, 'operation complete, no changes'
    elif response.status_code == 303:
        print('Redirected to', response.headers['location'])
    elif 'detail' in json:
        return False, json['detail']
    elif response.status_code == 400:
        return False, json
    else:
        raise RuntimeError(response.status_code)

#########################################################################
### Nagios API Commands #################################################
#########################################################################

def nagiosQuery(action, args):
    """
    Do a nagios query based on the check_mk REST API.

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
    baseurl = API_URL_BASE % (args['server'], args['site'])
    session = requests.Session()
    session.headers['Accept'] = 'application/json'
    session.headers['Content-Type'] = 'application/json'
    session.headers['Authorization'] = \
        "Bearer %s %s" % (args['user'], args['apikey'])

    # hostreport - updated, pulls down a specific list of fields
    if action == 'hostreport':
        url = '%s/domain-types/host/collections/all' % (baseurl)
        q1 = '{"op": "!=", "left": "state", "right": "0"}'
        if 'ack' in args:
            q2 = '{"op": "=", "left": "acknowledged", "right": "%s"}' % args['ack']
            q = '{"op": "and", "expr": [%s, %s]}' % (q1, q2)
        else:
            q = q1
        c = [ 'name', 'state', 'plugin_output', 'last_state_change', 'comments_with_info' ]

    elif action == 'servicereport':
        url = '%s/domain-types/service/collections/all' % (baseurl)
        q1 = '{"op": "!=", "left": "state", "right": "0"}'
        if 'ack' in args:
            q2 = '{"op": "=", "left": "acknowledged", "right": "%s"}' % args['ack']
            q = '{"op": "and", "expr": [%s, %s]}' % (q1, q2)
        else:
            q = q1
        c = [ 'host_name', 'display_name', 'state', 'plugin_output', 'last_state_change', 'comments_with_info' ]
        # if 'ack' in list(args.keys()):
            # url_parts['is_service_acknowledged'] = args['ack']
        # if 'all' in list(args.keys()):
            # url_parts['is_service_acknowledged'] = args['all']

    elif action == 'downtime':
        url_parts['_transid'] = '-1'
        url_parts['_do_confirm'] = 'yes'
        url_parts['_do_actions'] = 'yes'

        if args['remove']:
            url_parts['_remove_downtimes'] = 'Remove'
            url_parts['_down_remove'] = 'Remove'
        else:
            if 'start' in list(args.keys()): start = args['start']
            else:                      start = datetime.datetime.now()
            if 'end' in list(args.keys()):   end = args['end']
            else:
                end = start + datetime.timedelta(hours=int(args['hours']))

            url_parts['_down_custom'] = 'Custom+time_range'
            url_parts['_down_from_date'] = start.date()
            url_parts['_down_from_time'] = start.strftime('%H:%M')
            url_parts['_down_to_date'] = end.date()
            url_parts['_down_to_time'] = end.strftime('%H:%M')
            url_parts['_down_comment'] = args['comment']

        if args['type'] == 'host':
            url_parts['host'] = args['host']
            url_parts['view_name'] = 'hoststatus'
        elif args['type'] == 'svc' or args['type'] == 'service':
            url_parts['host'] = args['host']
            url_parts['service'] = args['service']
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
            url_parts['host'] = args['host']
            url_parts['view_name'] = 'hoststatus'
        elif args['type'] == 'svc' or args['type'] == 'service':
            url_parts['host'] = args['host']
            url_parts['service'] = args['service']
            url_parts['view_name'] = 'service'
        else:
            raise Exception('invalid ack type: %s' % args['type'])

    elif action == 'get_host':
        url_parts['action'] = 'get_host'
        url_parts['host'] = 'ssiadmin4'

    else:
        raise Exception('invalid action: %s' % action)

    if args['debug']:
        print ("    url: %s" % url)
        print ("  query: %s" % q)
        print ("   cols: %s" % c)

    resp=session.get(url, params={'query': q, 'columns': c})

    if resp.status_code == 200:
        v = resp.json()
        values = []
        for i in v['value']:
            values.append(i['extensions'])
        return values
    elif resp.status_code == 204:       # zero entries
        return []
    else:
        raise RuntimeError(resp.json())

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

def nagiosHostReportFormatted(entries):
    """
    """

    ret = []
    for i in entries:
        state_pretty = HOST_STATE[i['state']]

        comments = []
        for j in i['comments_with_info']:
            comments.append('%s: %s' % (j[1], j[2]))

        age = datetime.datetime.fromtimestamp(i['last_state_change'])
        age_human = age.strftime("%Y-%m-%d %H:%M:%S %Z")

        # need to parse out comments still
        ret.append([
            i['name'], state_pretty, i['plugin_output'],
            age_human,
            '; '.join(comments)
        ])

    return ret

def nagiosServiceReportFormatted(entries):
    """
    """

    ret = []
    for i in entries:
        state_pretty = SVC_STATE[i['state']]

        name = '%s/%s' % (i['host_name'], i['display_name'])

        age = datetime.datetime.fromtimestamp(i['last_state_change'])
        age_human = age.strftime("%Y-%m-%d %H:%M:%S %Z")

        comments = []
        for j in i['comments_with_info']:
            comments.append('%s: %s' % (j[1], j[2]))

        ret.append([
            i['host_name'],
            i['display_name'],
            state_pretty,
            i['plugin_output'],
            age_human,
            '; '.join(comments)
        ])

    return ret

def nagiosReport(type, argdict):
    """
    Generate a nagios report.  Type can be one of 'svc_ack', 'svc_unack',
    'host_ack', or 'host_unack'.
    """
    args = argdict.copy()

    if type == 'host_ack':
        args['ack'] = 1
        values = nagiosQuery('hostreport', args)
        return nagiosHostReportFormatted(values)

    elif type == 'host_unack':
        args['ack'] = 0
        values = nagiosQuery('hostreport', args)
        return nagiosHostReportFormatted(values)

    elif type == 'host':
        values = nagiosQuery('hostreport', args)
        return nagiosHostReportFormatted(values)

    elif type == 'svc_ack':
        args['ack'] = 1
        values = nagiosQuery('servicereport', args)
        return nagiosServiceReportFormatted(values)

    elif type == 'svc_unack':
        args['ack'] = 0
        values = nagiosQuery('servicereport', args)
        return nagiosServiceReportFormatted(values)

    elif type == 'host':
        action = 'hostreport'

    elif type == 'hostservice':
        action = 'svcreport'

    elif type == 'get_host':
        action = 'get_host'

    else:
        raise Exception('invalid report type: %s' % type)

    # return nagiosQuery(action, args)
    # url = generateNagiosUrl(action, args)
    # response = loadUrl(url, '')
    # return processNagiosReport(response, argdict['debug'])

def processNagiosReport(response, debug):
    """
    Process the response from loadUrl().  Returns an array of matching
    objects, where we've trimmed off the first one (which described the
    fields of the later objects).

    If 'debug' is set, we'll print a lot of extra debugging information.

    Incidentally, we're doing some really ugly stuff here because check_mk
    isn't always returning with json, even when we ask it to.
    """

    data = response.read().decode()

    try:
        jsonresult = json.loads(data)
        if debug: pprint(jsonresult)
    except ValueError:
        lines = data.split('\n')
        if re.match('^MESSAGE: .*$', lines[0]):
            return lines[0]
        soup = BeautifulSoup(data, 'lxml')
        div1 = soup.find('div', attrs={'class': 'error'})
        if div1 is not None:
            print("Error returned")
            print(div1.string)
            return []
        else:
            print("ValueError.  Invalid JSON object returned, and could not extract error.  Full response was:")
            print(data)
            return []

    if len(jsonresult) <= 1: return []

    jsonresult.pop(0)
    return jsonresult
