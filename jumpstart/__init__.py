""" Jumpstart
Dashbord for TV in the loby of NRH 3
Author: Beckett Jenen
"""

from __future__ import print_function
import os
import re
import json
import random
import textwrap
from datetime import datetime, timedelta, timezone
from sentry_sdk.integrations.flask import FlaskIntegration
import sentry_sdk
import requests
from babel.dates import format_timedelta
from dateutil import parser
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from flask import Flask
from flask import request
from flask import render_template
from flask import jsonify
from flask import redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from jumpstart.google import calendar_service

sentry_sdk.init(
    dsn="https://51494372c5b94b7cbf2d3e246da4f127@sentry.io/1818983",
    integrations=[FlaskIntegration()]
)

App = Flask(__name__)

auth = HTTPTokenAuth(scheme='Token')
api_keys = os.environ.get('JUMPSTART_API_KEYS')

tokens = api_keys.split(',') if api_keys else []
App.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
App.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(App)

from jumpstart.models import File, Ann

if not os.path.exists(os.path.join(os.getcwd(), "site.db")):
    db.create_all()

# Initializes the database for Files
def init_dbf():
    file = File(title="___")
    db.session.query(File).delete()
    db.session.commit()
    db.session.add(file)
    db.session.commit()

def init_dba():
    ann = Ann(title="___")
    db.session.query(Ann).delete()
    db.session.commit()
    db.session.add(ann)
    db.session.commit()

@auth.verify_token
def verify_token(token):
    if token in tokens:
        return True
    return False


Limiter = Limiter(
    App,
    key_func=get_remote_address,
    default_limits=["30 per minute", "1 per second"],
)

@Limiter.request_filter
def ip_whitelist():
    return request.remote_addr == "127.0.0.1"

@App.route('/')
def index():
    return render_template('index.html')

@App.route('/calendar', methods=['GET'])
@Limiter.limit("14/minute")
def calendar():

    # Call the Calendar API
    now = datetime.now(timezone.utc)
    events_result = calendar_service.events().list(
        calendarId='rti648k5hv7j3ae3a3rum8potk@group.calendar.google.com',
        timeMin=now.isoformat(),
        maxResults=10,
        singleEvents=True,
        orderBy='startTime',
    ).execute()
    events = events_result.get('items', [])

    final_events = "<br>"

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        fin_date = parser.parse(start)
        delta = fin_date - now
        formatted = format_timedelta(delta) if delta > timedelta(0) else "------"

        final_events += (
            """<div class='calendar-event-container-lvl2'><span class='calendar-text-date'> """
            + formatted +
            """ </span><br>"""
        )
        final_events += (
            "<span class='calendar-text' id='calendar'>"+
            ''.join(event['summary'])+
            "</span></div>"
        )
        final_events += "<hr style='border: 1px #B0197E solid;'>"

    event_list = {'data': final_events}
    return jsonify(event_list)

@App.route('/get-announcement', methods=['GET', 'POST'])
@Limiter.limit("14/minute")
def get_announcement():
    if request.method == 'POST':
        init_dba()
        return "It worked"
    ann = Ann.query.first()
    announcement_post = {'data' : str(ann)}
    return jsonify(announcement_post)

@App.route("/update-announcement", methods=["POST"])
# @auth.login_required
def update_announcement():
    req_data = request.get_json()
    ann_data = req_data['ann_body']
    ann = Ann.query.first()
    ann.title = ann_data
    db.session.commit()
    return "Announcement Updated"

@App.route('/get-harold', methods=['GET', 'POST'])
@Limiter.limit("14/minute")
def get_harold():
    if request.method == 'POST':
        init_dbf()
        return "It worked"
    file = File.query.first()
    filename = {'data': str(file)}
    return jsonify(filename)

@App.route("/update-harold", methods=["POST"])
@auth.login_required
def update_harold():
    req_data = request.get_json()
    filename = req_data['file_name']
    file = File.query.first()
    file.title = filename
    db.session.commit()
    return "Harold File Updated"

if __name__ == '__main__':
    App.run(debug=True)

@App.route('/showerthoughts', methods=['GET'])
@Limiter.limit("2/minute")
def showerthoughts():
    randompost = random.randint(1, 20)
    url = requests.get(
        'https://www.reddit.com/r/showerthoughts/hot.json',
        headers={'User-agent':'Showerthoughtbot 0.1'},
    )
    reddit = json.loads(url.text)
    shower_thoughts = textwrap.fill((reddit['data']['children'][randompost]['data']['title']), 50)
    if ("#" in shower_thoughts) || (" fuck" in shower_thoughts) || (" bitch" in shower_thoughts) || (" masterbate" in shower_thoughts) || (" dildo" in shower_thoughts) || (" cunt" in shower_thoughts) || (" pussy" in shower_thoughts) || (" penis" in shower_thoughts):
        shower_thoughts = "LIGMA LIGMA LIGMA LIGMA LIGMA"
    s_t = {'data': shower_thoughts}
    return jsonify(s_t)
