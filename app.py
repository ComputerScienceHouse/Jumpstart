from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from flask import *
from json import *
from flask_sqlalchemy import SQLAlchemy
from dateutil import parser
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class File(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(80), nullable=False)

	def __repr__(self):
		return f"{self.title}"

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["2 per minute", "1 per second"],
)

@limiter.request_filter
def ip_whitelist():
	return request.remote_addr == "127.0.0.1"

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/calendar', methods=['GET'])
@limiter.limit("0/minute")
def calendar():
	now = datetime.datetime.now()
	year = now.year
	month = now.month
	day = now.day
	hour = '{:02d}'.format(now.hour)
	minute = '{:02d}'.format(now.minute)

	"""Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
	creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
	if os.path.exists('token.pickle'):
		with open('token.pickle', 'rb') as token:
			creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
			creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
		with open('token.pickle', 'wb') as token:
			pickle.dump(creds, token)

	service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
	now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
	events_result = service.events().list(calendarId='rti648k5hv7j3ae3a3rum8potk@group.calendar.google.com', timeMin=now,maxResults=9, singleEvents=True,orderBy='startTime').execute()
	events = events_result.get('items', [])

	finalEvents = ""

	# finalEvents = "<br><span class='calendar-text-date' style='padding-left: 6%;'>Current time: " + str(hour) + ":" + str(minute) + "</span><br><hr style='border: 3px #e21a52 solid;'>"

	if not events:
		print('No upcoming events found.')
	for event in events:
		start = event['start'].get('dateTime', event['start'].get('date'))
		parser.parserinfo(dayfirst=False, yearfirst=False)
		parsedOld = str(parser.parse(start, fuzzy_with_tokens=False))
		parsed = parsedOld.replace(str(year), "", 1).replace(str(year+1), "", 1).replace(str(month), "", 1).replace(str(month+1), "", 1).replace(str(day), "Today at ", 1).replace(str(day+1), "Tomorrow at ", 1).replace(str(day+2), "In two days at ", 1).replace(str(day+3), "In three days at ", 1).replace(str(day+4), "In four days at ", 1).replace(str(day+5), "In five days at ", 1).replace(str(day+6), " ", 1).replace("-", "").replace(":0004:00", " -- <br>")
		finalEvents += "<div class='calendar-event-container-lvl2'><span class='calendar-text-date'>" + parsed + "</span>"
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
	return redirect("/")

if __name__ == '__main__':
	app.run(debug=True)



