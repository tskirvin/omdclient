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
           pending_changes
           update_folder
           update_host

       args     Argument dict.

           apikey       (required)
           server       (required)
           site         (required)
           user         (required)
           debug        If set, we'll print lots of data to stderr.
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

    elif action == 'create_host':
        url = baseurl + '/domain-types/host_config/collections/all'

    elif action == 'delete_host':
        hostname = args['host_name']
        url = baseurl + '/objects/host_config/' + hostname

    elif action == 'discover_services':
        url = baseurl + '/domain-types/service_discovery_run/actions/start/invoke'

    elif action == 'get_all_hosts': # TODO
        url = baseurl + '/domain-types/host_config/collections/all'

    elif action == 'get_host':
        hostname = args['host_name']
        url = baseurl + '/objects/host_config/' + hostname

    elif action == 'pending_changes':
        url = baseurl + '/domain-types/activation_run/collections/pending_changes'

    elif action == 'update_host':
        hostname = args['host_name']
        url = baseurl + '/objects/host_config/' + hostname

    elif action == 'update_folder':
        hostname = args['host_name']
        url = "%s/objects/host_config/%s/actions/move/invoke" % (baseurl, hostname)

    else:
        raise Exception('invalid action: %s' % action)

    if args['debug']:
        print(("url: %s" % url), file=sys.stderr)
        headers_clean = dict(headers)
        headers_clean['Authorization'] = '...'
        print(("headers: ", headers_clean), file=sys.stderr)
        print(("base content: ", content), file=sys.stderr)

    return url, headers, content

#############################################################################
### Requests Helper Functions ###############################################
#############################################################################

def _session():
    """
    Defaults for requests sessions within this module
    """
    session = requests.session()
    session.max_redirects = 500
    session.headers['Accept'] = 'application/json'
    return session

def _loadRequestsDelete(url, headers, code):
    """
    Load a requests delete() call with url/headers/code.  Returns a requests
    response, to be parsed elsewhere.
    """
    return _session().delete (url, headers=headers, json=code, allow_redirects=True)

def _loadRequestsGet(url, headers, code):
    """
    Load a requests get() call with url/headers/code.  Returns a requests
    response, to be parsed elsewhere.
    """
    return _session().get(url, headers=headers, json=code, allow_redirects=True)

def _loadRequestsPost(url, headers, code):
    """
    Load a requests post() call with url/headers/code.  Returns a requests
    response, to be parsed elsewhere.
    """
    return _session().post(url, headers=headers, json=code, allow_redirects=True)

def _loadRequestsPut(url, headers, code):
    """
    Load a requests put() call with url/headers/code.  Returns a requests
    response, to be parsed elsewhere.
    """
    return _session().put(url, headers=headers, json=code, allow_redirects=True)

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

def parseError(json):
    """
    Take the 'title' and 'fields' fields from a failed check_mk call and
    make them into a nice error string, suitable for exceptions.
    """

    title = json['title']
    err = []
    if 'fields' in json:
        for i in json['fields']:
            for j in json['fields'][i]:
                err.append(j)
        text = ';'.join(err)
    else:
        text = json['detail']
    return ("%s: %s" % (title, text))


#########################################################################
### check_mk API Interactions ###########################################
#########################################################################

def pendingChanges(arghash):
    """
    """
    url, headers, content = generateRequests('pending_changes', arghash)
    response = _loadRequestsGet(url, headers, content)

    try:    json = response.json()
    except: json = {}

    if response.status_code == 200:
        return response
    if response.status_code == 204:
        return response
    elif 'detail' in json:
        raise RuntimeError(parseError(json))
    else:
        return False


def activateChanges(arghash):
    """
    Activate changes.  This can be slow.
    """
    url, headers, content = generateRequests('activate_changes', arghash)

    # we need to query this first to get the information to activate with
    object = pendingChanges(arghash)
    headers['If-Match'] = object.headers['ETag']

    if 'foreign_ok' in arghash:
        content['force_foreign_changes'] = arghash['foreign_ok']

    content['redirect'] = True

    response = _loadRequestsPost(url, headers, content)
    (ret, text) = processRequestsResponse(response, arghash['debug'])
    if ret: return "changes activated"
    else: return text

def createHost(host, arghash):
    """
    Create a host entry.

        folder      Default: '/'
        role
        instance
        extra

    Note that `tag_role` and `tag_instance` are tags used locally to tie
    together local puppet instance and our OMD folders.  You don't
    have to use them and may cheerfully ignore them.
    """

    arghash['host_name'] = host
    url, headers, content = generateRequests('create_host', arghash)

    if 'folder' in arghash: content['folder'] = arghash['folder']
    else:                   content['folder'] = '/'

    content['host_name'] = host

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

    content['attributes'] = attributes

    response = _loadRequestsPost(url, headers, content)

    try:    json = response.json()
    except: json = {}

    if response.status_code == 200:
        return True
    elif 'detail' in json:
        raise RuntimeError(parseError(json))
    else:
        return False

def readHost(host, arghash):
    """
    Get information about a host.  Returns the the whole requests object;
    you will probably need response.headers['ETag'] a lot of the time.
    """
    url, headers, content = generateRequests('get_host', arghash)
    arghash['host_name'] = host
    content = 'request={"hostname" : "%s"}' % (host)
    response = _loadRequestsGet(url, headers, content)

    return response

def readHostData(host, arghash):
    """
    Like readHost(), but only returns the response.  This is closer to what
    you probably want most times when called from a script.
    """
    arghash['host_name'] = host
    response = readHost(host, arghash)
    return response.json()

def updateFolder(host, folder, arghash):
    """
    Update the folder of a host.
    """

    arghash['host_name'] = host
    object = readHost(host, arghash)

    # get the host wtih a single query
    url, headers, content = generateRequests('update_folder', arghash)

    content['target_folder'] = folder
    headers['If-Match'] = object.headers['ETag']

    response = _loadRequestsPut(url, headers, content)
    print (processRequestsResponse(response, arghash['debug']))

def updateHost(host, arghash):
    """
    Update information from a host.  If the host does not already exist,
    we'll call createHost instead.
    """

    arghash['host_name'] = host
    object = readHost(host, arghash)

    url, headers, content = generateRequests('update_host', arghash)

    headers['If-Match'] = object.headers['ETag']

    content['host_name'] = host
    if 'attributes' in arghash:
        content['attributes'] = [arghash['attributes']]
    if 'update_attributes' in arghash:
        content['update_attributes'] = [arghash['update_attributes']]
    if 'unset_attributes' in arghash:
        content['unset_attributes'] = [arghash['unset_attributes']]

    response = _loadRequestsPut(url, headers, content)
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
    response = _loadRequestsGet(url, headers, content)

    try:    json = response.json()
    except: json = {}

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
    arghash['host_name'] = host
    url, headers, content = generateRequests('delete_host', arghash)
    response = _loadRequestsDelete(url, headers, content)

    try:    json = response.json()
    except: json = {}

    if arghash['debug']:
        print(('response: ', response), file=sys.stderr)
        print(('json: ', pprint(json)), file=sys.stderr)

    if response.status_code == 204:
        return True
    elif 'detail' in json:
        raise RuntimeError(parseError(json))
    else:
        return False

def discoverServicesHost(host, arghash):
    """
    Scan a host for services.
    """
    url, headers, content = generateRequests('discover_services', arghash)
    content['host_name'] = host
    if 'tabula_rasa' in arghash: content['mode'] = 'refresh'
    response = _loadRequestsPost(url, headers, content)

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
        return True
    elif response.status_code == 204:     # the API does not know about this code but it seems to be a default answer
        return True
    elif 'detail' in json:
        raise RuntimeError(parseError(json))
    else:
        raise False

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
