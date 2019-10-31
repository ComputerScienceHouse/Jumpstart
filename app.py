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
	today = datetime.datetime.today().strftime ('%d') # format the date to ddmmyyyy
	 
	tomorrow_date = datetime.datetime.today() + datetime.timedelta(days=1)
	tomorrow = tomorrow_date.strftime ('%d') # format the date to ddmmyyyy

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

	finalEvents = "<br>"

	if not events:
		print('No upcoming events found.')
	for event in events:
		start = event['start'].get('dateTime', event['start'].get('date'))
		
		finalDate = ""

		semiFinalDate = list(start)

		for j in range(0, 8):
			del semiFinalDate[0]

		for i in range(0, 6):
			del semiFinalDate[len(semiFinalDate)]

		finalDate = ''.join(semiFinalDate)
		

		finalEvents += "<div class='calendar-event-container-lvl2'><span class='calendar-text-date'>" + finalDate + "</span>"
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



