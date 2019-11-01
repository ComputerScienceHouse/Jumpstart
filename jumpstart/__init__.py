from __future__ import print_function
import os
import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from flask import Flask, request, render_template, jsonify, redirect
from json import *
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from jumpstart.google import calendar_service

app = Flask(__name__)

auth = HTTPTokenAuth(scheme='Token')
api_keys = os.environ.get('JUMPSTART_API_KEYS')

tokens = api_keys.split(',') if api_keys else []
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

from jumpstart.models import File

if not os.path.exists(os.path.join(os.getcwd(), "site.db")):
	db.create_all()

@auth.verify_token
def verify_token(token):
	if token in tokens:
		return True
	return False


limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["21 per minute", "1 per second"],
)

@limiter.request_filter
def ip_whitelist():
	return request.remote_addr == "127.0.0.1"

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/calendar', methods=['GET'])
@limiter.limit("125/minute")
def calendar():
	now = datetime.datetime.now()
	today = datetime.datetime.today().strftime ('%d') # format the date to ddmmyyyy
	 
	tomorrow_date = datetime.datetime.today() + datetime.timedelta(days=1)
	tomorrow_fin = tomorrow_date.strftime ('%d') # format the date to ddmmyyyy

	two_day_date = datetime.datetime.today() + datetime.timedelta(days=2)
	two_day_fin = two_day_date.strftime ('%d') # format the date to ddmmyyyy

    # Call the Calendar API
	now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
	events_result = calendar_service.events().list(calendarId='rti648k5hv7j3ae3a3rum8potk@group.calendar.google.com', timeMin=now,maxResults=9, singleEvents=True,orderBy='startTime').execute()
	events = events_result.get('items', [])

	finalEvents = "<br>"

	if not events:
		print('No upcoming events found.')
	for event in events:
		start = event['start'].get('dateTime', event['start'].get('date'))
		
		finalDate = ""

		semiFinalDate = list(start)

		for j in range(0, 8):
			del semiFinalDate[0]

		for i in range(0, 9):
			del semiFinalDate[len(semiFinalDate)-1]

		finalDate = ''.join(semiFinalDate)
		
		finalfinalDate = finalDate.replace("T", "", 1).replace(today, "Today at ").replace(tomorrow_fin, "Tomorrow at ").replace(two_day_fin, "In two days at ")

		finalEvents += "<div class='calendar-event-container-lvl2'><span class='calendar-text-date'>" + finalfinalDate + " " + "</span>"
		finalEvents += "<span class='calendar-text' id='calendar'>" + ''.join(event['summary']) + "</span></div>"
		finalEvents += "<hr style='border: 1px #B0197E solid;'>"

	eventList = {'data': finalEvents}
	return jsonify(eventList)

@app.route('/getdata-reset', methods=['GET', 'POST'])
def add():
	if request.method == 'POST':
		req_data = request.get_json()
		filename = req_data['file_name']
		try:
			file = File(title=filename)
			db.session.query(File).delete()
			db.session.commit()
			db.session.add(file)
			db.session.commit()
		except Exception as e:
			print("Failed to add File")
			print(e)
		file = File.query.all()
		return str(file)
	else:
		file = File.query.first()
		filename = {'data': str(file)}
		return jsonify(filename)

@app.route("/update", methods=["POST"])
@auth.login_required
def update():
	try:
		req_data = request.get_json()
		filename = req_data['file_name']
		file = File.query.first()
		file.title = filename
		db.session.commit()
	except Exception as e:
		print("Couldn't update File")
		print(e)
	return "It worked"

if __name__ == '__main__':
	app.run(debug=True)



