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
# import sqlite3
import json
import sys
import os
from pathlib import Path

app = flask.Flask(__name__)
sslify=SSLify(app) # require https
app.config["DEBUG"] = True

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


# # response = jsonified list of dict and response code
# @app.route('/api/v1/events/new', methods=['POST'])
# @require_appkey
# def api_newEvent():
#     app.logger.info("new called")
#     if not request.json:
#         app.logger.info("no json")
#         return "<h1>400</h1><p>Request has no json payload.</p>", 400
#     if type(request.json) is str:
#         d=json.loads(request.json)
#     else: #kivy UrlRequest sends the dictionary itself
#         d=request.json
#     r=sdbNewEvent(d)
#     app.logger.info("sending response from api_newEvent:"+str(r))
#     return jsonify(r)


@app.route('/', methods=['GET'])
# @require_appkey
def home():
    return '''<h1>AssignmentTracker Database API</h1>
<p>API for interacting with the AssignmentTracker database</p>'''

@app.route('/api/v1/init')
@require_appkey
def api_init():
    tdbInit()
    return '''<h1>AssignmentTracker Database API</h1>
<p>Database initialized.</p>'''

@app.route('/api/v1/teams',methods=['GET'])
@require_appkey
def api_getTeams():
    app.logger.info("teams called")
    return jsonify(tdbGetTeams())

@app.route('/api/v1/assignments',methods=['GET'])
@require_appkey
def api_getAssignments():
    app.logger.info("assignments called")
    return jsonify(tdbGetAssignments())

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
    if not set(['AssignmentID','TeamID']).issubset(d):
        app.logger.info("incorrect json")
        return "<h1>400</h1><p>pairings/new POST: expected keys 'AssignmentID' and 'TeamID' in json payload.</p><p>"+json.dumps(d)+"</p>", 400
    return jsonify(tdbPair(d['AssignmentID'],d['TeamID']))

@app.route('/api/v1/teams/<int:teamID>',methods=['GET'])
@require_appkey
def api_getTeam(teamID):
    app.logger.info("teams/"+str(teamID)+" GET called")
    return jsonify(tdbGetTeams(teamID))

@app.route('/api/v1/assignments/<int:assignmentID>',methods=['GET'])
@require_appkey
def api_getAssignment(assignmentID):
    app.logger.info("assignments/"+str(assignmentID)+" GET called")
    return jsonify(tdbGetAssignments(assignmentID))

@app.route('/api/v1/pairings/<int:pairingID>',methods=['GET'])
@require_appkey
def api_getPairing(pairingID):
    app.logger.info("pairings/"+str(pairingID)+" GET called")
    return jsonify(tdbGetPairings(pairingID))

@app.route('/api/v1/teams/<int:teamID>/status',methods=['PUT'])
@require_appkey
def api_setTeamStatusByID(teamID):
    app.logger.info("teams/"+str(teamID)+"/status PUT called")
    if not request.json:
        app.logger.info("no json")
        return "<h1>400</h1><p>teams/"+str(teamID)+"/status PUT: Request has no json payload.</p>", 400
    if type(request.json) is str:
        d=json.loads(request.json)
    else: #kivy UrlRequest sends the dictionary itself
        d=request.json
    if not set(['NewStatus']).issubset(d):
        app.logger.info("incorrect json")
        return "<h1>400</h1><p>teams/"+str(teamID)+"/status PUT: expected key 'NewStatus' in json payload.</p><p>"+json.dumps(d)+"</p>", 400
    return jsonify(tdbSetTeamStatusByID(teamID,d['NewStatus']))

@app.route('/api/v1/assignments/<int:assignmentID>/status',methods=['PUT'])
@require_appkey
def api_setAssignmentStatusByID(assignmentID):
    app.logger.info("assignments/"+str(assignmentID)+"/status PUT called")
    if not request.json:
        app.logger.info("no json")
        return "<h1>400</h1><p>assignments/"+str(assignmentID)+"/status PUT: Request has no json payload.</p>", 400
    if type(request.json) is str:
        d=json.loads(request.json)
    else: #kivy UrlRequest sends the dictionary itself
        d=request.json
    if not set(['NewStatus']).issubset(d):
        app.logger.info("incorrect json")
        return "<h1>400</h1><p>assignments/"+str(assignmentID)+"/status PUT: expected key 'NewStatus' in json payload.</p><p>"+json.dumps(d)+"</p>", 400
    return jsonify(tdbSetAssignmentStatusByID(assignmentID,d['NewStatus']))

@app.route('/api/v1/pairings/<int:pairingID>/status',methods=['PUT'])
@require_appkey
def api_setPairingStatusByID(pairingID):
    app.logger.info("pairings/"+str(pairingID)+"/status PUT called")
    if not request.json:
        app.logger.info("no json")
        return "<h1>400</h1><p>pairings/"+str(pairingID)+"/status PUT: Request has no json payload.</p>", 400
    if type(request.json) is str:
        d=json.loads(request.json)
    else: #kivy UrlRequest sends the dictionary itself
        d=request.json
    if not set(['NewStatus']).issubset(d):
        app.logger.info("incorrect json")
        return "<h1>400</h1><p>pairings/"+str(pairingID)+"/status PUT: expected key 'NewStatus' in json payload.</p><p>"+json.dumps(d)+"</p>", 400
    return jsonify(tdbSetPairingStatusByID(pairingID,d['NewStatus']))

# def api_add_or_update(eventID):
#     app.logger.info("put called for event "+str(eventID))
#     if not request.json:
#         app.logger.info("no json")
#         return "<h1>400</h1><p>Request has no json payload.</p>", 400
#     if type(request.json) is str:
#         d=json.loads(request.json)
#     else: #kivy UrlRequest sends the dictionary itself
#         d=request.json
#     return jsonify(sdbAddOrUpdate(eventID,d))

# @app.route('/api/v1/events',methods=['GET'])
# @require_appkey
# def api_getEvents():
#     lastEditSince=request.args.get("lastEditSince",0)
#     eventStartSince=request.args.get("eventStartSince",0)
#     nonFinalizedOnly=request.args.get("nonFinalizedOnly",False)
#     nonFinalizedOnly=str(nonFinalizedOnly).lower()=='true' # convert to boolean
#     app.logger.info("events called: lastEditSince="+str(lastEditSince)
#             +" eventStartSince="+str(eventStartSince)
#             +" nonFinalizedOnly="+str(nonFinalizedOnly))
#     # response = jsonified list
#     return jsonify(sdbGetEvents(lastEditSince,eventStartSince,nonFinalizedOnly))


# @app.route('/api/v1/events/<int:eventID>', methods=['GET'])
# @require_appkey
# def api_getEvent(eventID):
#     return jsonify(sdbGetEvent(eventID))


# @app.route('/api/v1/roster',methods=['GET'])
# @require_appkey
# def api_getRoster():
#     app.logger.info("roster called")
#     return jsonify(sdbGetRoster())


# @app.route('/api/v1/events/<int:eventID>/html', methods=['GET'])
# @require_appkey
# def api_getEventHTML(eventID):
#     return getEventHTML(eventID)


# # it's cleaner to let the host decide whether to add or to update;
# # if ID, Agency, Name, and InEpoch match those of an existing record,
# #  then update that record; otherwise, add a new record;
# # PUT seems like a better fit than POST based on the HTTP docs
# #  note: only store inEpoch to the nearest hunredth of a second since
# #  comparison beyond 5-digits-right-of-decimal has shown truncation differences

# @app.route('/api/v1/events/<int:eventID>', methods=['PUT'])
# @require_appkey
# def api_add_or_update(eventID):
#     app.logger.info("put called for event "+str(eventID))
#     if not request.json:
#         app.logger.info("no json")
#         return "<h1>400</h1><p>Request has no json payload.</p>", 400
#     if type(request.json) is str:
#         d=json.loads(request.json)
#     else: #kivy UrlRequest sends the dictionary itself
#         d=request.json
#     return jsonify(sdbAddOrUpdate(eventID,d))



# # finalize: eventID = cloud database event ID
# # 1. set the event to finalized
# # 2. call sdbPush: if it's not a d4h activity, sdbPush will end early but cleanly

# @app.route('/api/v1/finalize/<int:eventID>',methods=['POST'])
# @require_appkey
# def api_finalize(eventID):
#     app.logger.info("finalize called for event "+str(eventID))
#     rval=sdbPush(eventID)
#     if rval["statusCode"]>299:
#         return rval["message"],rval["statusCode"]
#     return jsonify(rval)


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


# app.run() must be run on localhost flask and LAN flask, but not on cloud (WSGI);
#  check to see if the resolved path directory contains '/home'; this may
#  need to change when LAN server is incorporated, since really it is just checking
#  for linux vs windows
if '/home' not in pr:
    app.run()
