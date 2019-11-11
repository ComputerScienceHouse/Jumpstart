from __future__ import print_function
import os
from datetime import datetime, timedelta, timezone
from babel.dates import format_timedelta
from dateutil import parser
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from flask import Flask, request, render_template, jsonify, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from jumpstart.google import calendar_service
import json, random, textwrap, requests

app = Flask(__name__)

auth = HTTPTokenAuth(scheme='Token')
api_keys = os.environ.get('JUMPSTART_API_KEYS')

tokens = api_keys.split(',') if api_keys else []
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

from jumpstart.models import File, Ann

if not os.path.exists(os.path.join(os.getcwd(), "site.db")):
	db.create_all()

def initDBF():
	file = File(title="___")
	db.session.query(File).delete()
	db.session.commit()
	db.session.add(file)
	db.session.commit()

def initDBA():
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


limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["30 per minute", "1 per second"],
)

@limiter.request_filter
def ip_whitelist():
	return request.remote_addr == "127.0.0.1"

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/calendar', methods=['GET'])
@limiter.limit("14/minute")
def calendar():

    # Call the Calendar API
	now = datetime.now(timezone.utc)
	events_result = calendar_service.events().list(calendarId='rti648k5hv7j3ae3a3rum8potk@group.calendar.google.com', timeMin=now.isoformat(), maxResults=10, singleEvents=True, orderBy='startTime').execute()
	events = events_result.get('items', [])

	finalEvents = "<br>"

	if not events:
		print('No upcoming events found.')
	for event in events:
		start = event['start'].get('dateTime', event['start'].get('date'))

		finDate = parser.parse(start)
		delta = finDate - now
		formatted = format_timedelta(delta) if delta > timedelta(0) else "------"

		finalEvents += "<div class='calendar-event-container-lvl2'><span class='calendar-text-date'>" + formatted + "</span><br>"
		finalEvents += "<span class='calendar-text' id='calendar'>" + ''.join(event['summary']) + "</span></div>"
		finalEvents += "<hr style='border: 1px #B0197E solid;'>"

	eventList = {'data': finalEvents}
	return jsonify(eventList)

@app.route('/get-announcement', methods=['GET', 'POST'])
@limiter.limit("14/minute")
def get_announcement():
	if request.method == 'POST':
		initDBA()
		return "It worked"
	else:
		ann = Ann.query.first()
		announcement_post = {'data' : str(ann)}
		return jsonify(announcement_post)

@app.route("/update-announcement", methods=["POST"])
# @auth.login_required
def update_announcement():
	try:
		req_data = request.get_json()
		ann_data = req_data['ann_body']
		ann = Ann.query.first()
		ann.title = ann_data
		db.session.commit()
		return "Announcement Updated"
	except Exception as e:
		print("Couldn't update Announcement")
		print(e)
		return "Announcement Wasn't Updated"

@app.route('/get-harold', methods=['GET', 'POST'])
@limiter.limit("14/minute")
def get_harold():
	if request.method == 'POST':
		initDBF()
		return "It worked"
	else:
		file = File.query.first()
		filename = {'data': str(file)}
		return jsonify(filename)

@app.route("/update-harold", methods=["POST"])
@auth.login_required
def update_harold():
	try:
		req_data = request.get_json()
		filename = req_data['file_name']
		file = File.query.first()
		file.title = filename
		db.session.commit()
	except Exception as e:
		print("Couldn't update File")
		print(e)
	return "Harold File Updated"

if __name__ == '__main__':
	app.run(debug=True)

@app.route('/showerthoughts', methods=['GET'])
@limiter.limit("2/minute")
def showerthoughts():
	randompost = random.randint(1,20)
	url = requests.get('https://www.reddit.com/r/showerthoughts/hot.json', headers = {'User-agent': 'Showerthoughtbot 0.1'})
	reddit = json.loads(url.text)
	shower_thoughts = textwrap.fill((reddit['data']['children'][randompost]['data']['title']),50)
	st = {'data': shower_thoughts}
	return jsonify(st)

