# #############################################################################
#
#  tracker_api.py - host web API code for Assignment Tracker app
#
#  AssignmentTracker is developed for Nevada County Sheriff's Search and Rescue
#    Copyright (c) 2020 Tom Grundy
#
#  http://github.com/ncssar/AssignmentTracker
#
#  Contact the author at nccaves@yahoo.com
#   Attribution, feedback, bug reports and feature requests are appreciated
#
#  REVISION HISTORY
#-----------------------------------------------------------------------------
#   DATE   | AUTHOR | VER |  NOTES
#-----------------------------------------------------------------------------
#
# #############################################################################

import flask
from flask import request, jsonify
from flask_sslify import SSLify # require https to protect api key etc.
import json
import time
import sys
import os
from pathlib import Path

app = flask.Flask(__name__)
sslify=SSLify(app) # require https
app.config["DEBUG"] = True

USERS=[]

# see the help page for details on storing the API key as an env var:
# https://help.pythonanywhere.com/pages/environment-variables-for-web-apps/
TRACKER_API_KEY=os.getenv("TRACKER_API_KEY")

# on pythonanywhere, the relative path ./tracker should be added instead of ../tracker
#  since the current working dir while this script is running is /home/caver456
#  even though the script is in /home/caver456/tracker_api
# while it should be ok to load both, it's a lot cleaner to check for the
#  one that actually exists
p=Path('../AssignmentTracker')
if not p.exists():
    p=Path('./AssignmentTracker')
pr=str(p.resolve())
sys.path.append(pr)
app.logger.info("python search path:"+str(sys.path))

from assignmentTracker_db import *


###############################
# decorator to require API key
# from https://coderwall.com/p/4qickw/require-an-api-key-for-a-route-in-flask-using-only-a-decorator
# modified to use Bearer token
from functools import wraps
from flask import request, abort

# The actual decorator function
def require_appkey(view_function):
    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        auth_header=flask.request.headers.get('Authorization')
        if auth_header: # should be 'Bearer <auth_token>'
            auth_token=auth_header.split(" ")[1]
        else:
            auth_token=''
        if auth_token and auth_token == TRACKER_API_KEY:
        # if flask.request.args.get('key') and flask.request.args.get('key') == TRACKER_API_KEY:
            return view_function(*args, **kwargs)
        else:
            flask.abort(401)
    return decorated_function
###############################

# NOTE regarding ID values:
# tid = team ID; aid = assignment ID; pid = pairing ID
# these values are set to -1 when created on a client, or a positive integer when
#  created on the host.  The positive integer id is sent to all clients
#  as part of the new object http request response, whether the request was made
#  by the creating client, or by sync.  So, if id is -1 in steady state, either host
#  communication has been lost, or the host had an error, or there is no host.


@app.route('/', methods=['GET'])
def home():
    return '''<h1>AssignmentTracker Database API</h1>
<p>API for interacting with the AssignmentTracker database</p>'''

@app.route('/api/v1/join',methods=['POST'])
@require_appkey
def api_join():
    if not request.json:
        app.logger.info("no json")
        return "<h1>400</h1><p>teams/new POST: Request has no json payload.</p>", 400
    if type(request.json) is str:
        d=json.loads(request.json)
    else: #kivy UrlRequest sends the dictionary itself
        d=request.json
    d['IP']=request.remote_addr
    app.logger.info("join called with json:"+str(json.dumps(d)))
    USERS.append(d)
    # if len(USERS)==1:
    if 'Init' in d.keys() and d['Init']==True:
        serverName=request.environ['SERVER_NAME'] # normally just the IP address
        app.logger.info("init called.")
        app.logger.info("  server name: "+serverName)
        tdbInit(serverName) # pass server IP to database code, so database code can determine WS destination
        r="<h1>AssignmentTracker Database API</h1><p>You are the first node to join.  Database initialized.</p>"
    else:
        r="<h1>AssignmentTracker Database API</h1><p>You are now joined to the activity in progress.  Other nodes:</p><ul>"
        for u in USERS:
            r+="<li>"+u['NodeName']+" : "+u['IP']
        r+="</ul>"
    return r

@app.route('/api/v1/teams',methods=['GET'])
@require_appkey
def api_getTeams():
    app.logger.info("teams called")
    return jsonify(tdbGetTeams())

@app.route('/api/v1/teams/view',methods=['GET'])
@require_appkey
def api_getTeamsView():
    app.logger.info("teams view called")
    return jsonify(tdbGetTeamsView())

@app.route('/api/v1/assignments',methods=['GET'])
@require_appkey
def api_getAssignments():
    app.logger.info("assignments called")
    return jsonify(tdbGetAssignments())

@app.route('/api/v1/assignments/view',methods=['GET'])
@require_appkey
def api_getAssignmentsView():
    app.logger.info("assignments view called")
    return jsonify(tdbGetAssignmentsView())

@app.route('/api/v1/pairings',methods=['GET'])
@require_appkey
def api_getPairings():
    app.logger.info("pairings called")
    return jsonify(tdbGetPairings())

@app.route('/api/v1/teams/new',methods=['POST'])
@require_appkey
def api_newTeam():
    app.logger.info("newTeam POST called")
    if not request.json:
        app.logger.info("no json")
        return "<h1>400</h1><p>teams/new POST: Request has no json payload.</p>", 400
    if type(request.json) is str:
        d=json.loads(request.json)
    else: #kivy UrlRequest sends the dictionary itself
        d=request.json
    if not set(['TeamName','Resource']).issubset(d):
        app.logger.info("incorrect json")
        return "<h1>400</h1><p>teams/new POST: expected keys 'TeamName' and 'Resource' in json payload.</p><p>"+json.dumps(d)+"</p>", 400
    return jsonify(tdbNewTeam(d['TeamName'],d['Resource']))

@app.route('/api/v1/history',methods=['GET'])
@require_appkey
def api_getHistory():
    app.logger.info("getHistory called")
    return jsonify(tdbGetHistory())

@app.route('/api/v1/since/<int:since>',methods=['GET'])
@require_appkey
def api_getAll(since):
    app.logger.info("getAll called: since="+str(since))
    d={}
    d['timestamp']=str(round(time.time(),2))
    d['Teams']=tdbGetTeams(since=since)
    d['Assignments']=tdbGetAssignments(since=since)
    d['Pairings']=tdbGetPairings(since=since)
    d['History']=tdbGetHistory(since=since)
    return jsonify(d)

@app.route('/api/v1/assignments/new',methods=['POST'])
@require_appkey
def api_newAssignment():
    app.logger.info("newAssignment POST called")
    if not request.json:
        app.logger.info("no json")
        return "<h1>400</h1><p>assignments/new POST: Request has no json payload.</p>", 400
    if type(request.json) is str:
        d=json.loads(request.json)
    else: #kivy UrlRequest sends the dictionary itself
        d=request.json
    if not set(['AssignmentName','IntendedResource']).issubset(d):
        app.logger.info("incorrect json")
        return "<h1>400</h1><p>assignments/new POST: expected keys 'AssignmentName' and 'IntendedResource' in json payload.</p><p>"+json.dumps(d)+"</p>", 400
    return jsonify(tdbNewAssignment(d['AssignmentName'],d['IntendedResource']))

@app.route('/api/v1/pairings/new',methods=['POST'])
@require_appkey
def api_newPairing():
    app.logger.info("newPairing POST called")
    if not request.json:
        app.logger.info("no json")
        return "<h1>400</h1><p>pairings/new POST: Request has no json payload.</p>", 400
    if type(request.json) is str:
        d=json.loads(request.json)
    else: #kivy UrlRequest sends the dictionary itself
        d=request.json
    if not set(['aid','tid']).issubset(d):
        app.logger.info("incorrect json")
        return "<h1>400</h1><p>pairings/new POST: expected keys 'aid' and 'tid' in json payload.</p><p>"+json.dumps(d)+"</p>", 400
    r=tdbNewPairing(d['aid'],d['tid'])
    return jsonify(r)

@app.route('/api/v1/teams/<int:tid>',methods=['GET'])
@require_appkey
def api_getTeam(tid):
    app.logger.info("teams/"+str(tid)+" GET called")
    return jsonify(tdbGetTeams(tid))

@app.route('/api/v1/assignments/<int:aid>',methods=['GET'])
@require_appkey
def api_getAssignment(aid):
    app.logger.info("assignments/"+str(aid)+" GET called")
    return jsonify(tdbGetAssignments(aid))

@app.route('/api/v1/pairings/<int:pid>',methods=['GET'])
@require_appkey
def api_getPairing(pid):
    app.logger.info("pairings/"+str(pid)+" GET called")
    return jsonify(tdbGetPairings(pid))

@app.route('/api/v1/teams/<int:tid>/status',methods=['PUT'])
@require_appkey
def api_setTeamStatusByID(tid):
    app.logger.info("teams/"+str(tid)+"/status PUT called")
    if not request.json:
        app.logger.info("no json")
        return "<h1>400</h1><p>teams/"+str(tid)+"/status PUT: Request has no json payload.</p>", 400
    if type(request.json) is str:
        d=json.loads(request.json)
    else: #kivy UrlRequest sends the dictionary itself
        d=request.json
    if not set(['NewStatus']).issubset(d):
        app.logger.info("incorrect json")
        return "<h1>400</h1><p>teams/"+str(tid)+"/status PUT: expected key 'NewStatus' in json payload.</p><p>"+json.dumps(d)+"</p>", 400
    return jsonify(tdbSetTeamStatusByID(tid,d['NewStatus']))

@app.route('/api/v1/teams/<int:tid>/history',methods=['GET'])
@require_appkey
def api_getTeamHistoryByID(tid):
    app.logger.info("teams/"+str(tid)+"/history GET called")
    return jsonify(tdbGetHistory(tid=tid))

@app.route('/api/v1/assignments/<int:aid>/status',methods=['PUT'])
@require_appkey
def api_setAssignmentStatusByID(aid):
    app.logger.info("assignments/"+str(aid)+"/status PUT called")
    if not request.json:
        app.logger.info("no json")
        return "<h1>400</h1><p>assignments/"+str(aid)+"/status PUT: Request has no json payload.</p>", 400
    if type(request.json) is str:
        d=json.loads(request.json)
    else: #kivy UrlRequest sends the dictionary itself
        d=request.json
    if not set(['NewStatus']).issubset(d):
        app.logger.info("incorrect json")
        return "<h1>400</h1><p>assignments/"+str(aid)+"/status PUT: expected key 'NewStatus' in json payload.</p><p>"+json.dumps(d)+"</p>", 400
    return jsonify(tdbSetAssignmentStatusByID(aid,d['NewStatus']))

@app.route('/api/v1/asignments/<int:aid>/history',methods=['GET'])
@require_appkey
def api_getAssignmentHistoryByID(aid):
    app.logger.info("assignment/"+str(aid)+"/history GET called")
    return jsonify(tdbGetHistory(aid=aid))

@app.route('/api/v1/pairings/<int:pid>/status',methods=['PUT'])
@require_appkey
def api_setPairingStatusByID(pid):
    app.logger.info("pairings/"+str(pid)+"/status PUT called")
    if not request.json:
        app.logger.info("no json")
        return "<h1>400</h1><p>pairings/"+str(pid)+"/status PUT: Request has no json payload.</p>", 400
    if type(request.json) is str:
        d=json.loads(request.json)
    else: #kivy UrlRequest sends the dictionary itself
        d=request.json
    if not set(['NewStatus']).issubset(d):
        app.logger.info("incorrect json")
        return "<h1>400</h1><p>pairings/"+str(pid)+"/status PUT: expected key 'NewStatus' in json payload.</p><p>"+json.dumps(d)+"</p>", 400
    return jsonify(tdbSetPairingStatusByID(pid,d['NewStatus']))

@app.route('/api/v1/pairings/<int:pid>/history',methods=['GET'])
@require_appkey
def api_getPairingHistoryByID(pid):
    app.logger.info("pairing/"+str(pid)+"/history GET called")
    return jsonify(tdbGetHistory(pid=pid))

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


# app.run() must be run on localhost flask and LAN flask, but not on cloud (WSGI);
#  check to see if the resolved path directory contains '/home'; this may
#  need to change when LAN server is incorporated, since really it is just checking
#  for linux vs windows
if '/home' not in pr:
    app.run()
