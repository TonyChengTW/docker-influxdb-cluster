# Edit by TonyCheng
# Version : 0.0.1
# CloudCube Co., Inc.
import socket
ADMIN = ''
ADMIN_PASS = ''
DBNAME = 'monasca'
USERS = {}
USERS['tony'] = '1qaz@WSX'
#USERS['mon_api'] = 'password'
#USERS['mon_persister'] = 'password'
HOSTNAME = socket.gethostname()
URL = 'http://%s:8086' % (HOSTNAME)
SHARDSPACE_NAME = 'persister_all'
REPLICATION = 1
RETENTION = '7d'
import json
import sys
import time
import six.moves.urllib.parse as urlparse
import urllib2
def format_response(req):
    try:
        json_value = json.loads(req.read())
        if (len(json_value['results'][0]) > 0 and
           'values' in json_value['results'][0]['series'][0]):
            return json_value['results'][0]['series'][0]['values']
        else:
            return []
    except KeyError:
        print "Query returned a non-successful result: {0}".format(json_value['results'])
        raise
def influxdb_get(uri, query, db=None):
    getparams = {"q": query}
    if db:
        getparams['db'] = db
    try:
        params = urlparse.urlencode(getparams)
        uri = "{}&{}".format(uri,params)
        req = urllib2.urlopen(uri)
        return format_response(req)
    except KeyError:
        sys.exit(1)
def influxdb_get_post(uri, query, db=None):
    query_params = {"q": query}
    if db:
        query_params['db'] = db
    try:
        encoded_params = urlparse.urlencode(query_params)
        try:
            req = urllib2.urlopen(uri, encoded_params)
            return format_response(req)
        except urllib2.HTTPError:
            uri = "{}&{}".format(uri, encoded_params)
            req = urllib2.urlopen(uri)
            return format_response(req)
    except KeyError:
        sys.exit(1)
def main(argv=None):
    """If necessary, create the database, retention policy, and users"""
    auth_str = '?u=%s&p=%s' % (ADMIN, ADMIN_PASS)
    api_uri = "{0}/query{1}".format(URL, auth_str)
    # List current databases
    dbs = influxdb_get(uri=api_uri, query="SHOW DATABASES")
    if [DBNAME] not in dbs:
        print "Creating database '{}'".format(DBNAME)
        influxdb_get_post(uri=api_uri, query="CREATE DATABASE {0}".format(DBNAME))
        print "...created!"
    # Check retention policy
    policies = influxdb_get(uri=api_uri,
                            query="SHOW RETENTION POLICIES ON {0}".format(DBNAME))
    if not any(pol[0] == SHARDSPACE_NAME for pol in policies):
        # Set retention policy
        policy = "CREATE RETENTION POLICY {0} ON {1} DURATION {2} REPLICATION {3} DEFAULT".format(SHARDSPACE_NAME,
                                                                                          DBNAME,
                                                                                          RETENTION,
                                                                                          REPLICATION)
        influxdb_get_post(uri=api_uri, db=DBNAME, query=policy)
    # Create the users
    users = influxdb_get(uri=api_uri, query="SHOW USERS", db=DBNAME)
    for name, password in USERS.iteritems():
        if not any(user[0] == name for user in users):
            influxdb_get_post(uri=api_uri,
                              query=unicode("CREATE USER {0} WITH PASSWORD '{1}'".format(name, password)),
                              db=DBNAME)
if __name__ == "__main__":
    sys.exit(main())
