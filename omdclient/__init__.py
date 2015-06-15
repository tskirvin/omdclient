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

import json, optparse, os, requests, sys, urllib2, yaml
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
        soup=BeautifulSoup(data)
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
### Server Interactions #################################################
#########################################################################

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
    if 'extra' in arghash:
        if arghash['extra'] != 'UNSET':
            attributes['extra'] = arghash['extra']
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

    if readHost(host, arghash):
        pass
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
    if 'extra' in arghash:
        if arghash['extra'] != 'UNSET':
            attributes['extra'] = arghash['extra']
    request['attributes'] = attributes

    if 'unset' in arghash:
        attributes['unset_attributes'] = arghash['unset']

    request_string = "request=%s" % json.dumps(request)
    if arghash['debug']: print request_string

    response = loadUrl(url, request_string)
    return processUrlResponse(response, arghash['debug'])

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

def activateChanges(arghash):
    """
    Activate changes.  This can be slow.
    """
    url = generateUrl('activate_changes', arghash)
    response = loadUrl(url, '')
    return processUrlResponse(response, arghash['debug'])
