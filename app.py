from flask import Flask,request,Response,make_response,url_for,render_template

import plivo

from config_parser import get_config

from helper import rent_number

from model import create_forward_entry,get_details_from,get_mobile

configs=get_config()

PLIVO_API=plivo.RestAPI(configs["AUTH_ID"],configs["AUTH_TOKEN"])



CALLER_ID="19512977322"
BASE_URL="http://ancient-taiga-3101.herokuapp.com"
app = Flask(__name__)

app.debug=True

@app.route('/')

def index():
	return render_template('index.html') 

@app.route('/save')

def save():
	sip=request.args.get('sip','')
	mobile=request.args.get('mobile','')
	caller_name=request.args.get('caller_name','')
	voicemail_number,plivo_number=map(lambda app_name:rent_number(PLIVO_API,app_name),["Voice Mail","Call Forward"])
	create_forward_entry(sip,mobile,caller_name,
			     voicemail_number,plivo_number)
	return "Your plivo phone number is %s" %(plivo_number)

@app.route('/forward')

def forward():
	plivo_number=request.args.get('To','')
	CALLER_NAME,SIP,MOBILE,VOICEMAIL_NUMBER=get_details_from(plivo_number)
	response=plivo.Response()
	response.addSpeak("Please wait while we are forwarding your call")
	response.addDial(callerName=CALLER_NAME).addUser(SIP)
	response.addDial(callerId=CALLER_ID).addNumber(MOBILE)
	response.addSpeak("The number you're trying is not reachable at the moment. You are being redirected to the voice mail")
	response.addDial(callerId=CALLER_ID,
			action=BASE_URL+url_for('voice_mail')).addNumber(VOICEMAIL_NUMBER)
	response=make_response(response.to_xml())
	response.headers['Content-Type']='text/xml'
	
	return response


@app.route('/voice/mail')

def voice_mail():
	response=plivo.Response()
	response.addSpeak("Please leave your message after the beep")
	response.addRecord(action=BASE_URL+url_for('message'),method='GET')
	response.addSpeak("Thank you, your message has been recorded")
	response.addHangup()
	response=make_response(response.to_xml())
	response.headers['Content-Type']='text/xml'
	
	return response


@app.route('/message')


def message():
	record_url=request.args.get('RecordUrl','')
	VOICEMAIL_NUMBER=request.args.get('To','')
	MESSAGE="Hey, we have received a voice message for you. You can access them at %s" %(record_url)
	MOBILE=get_mobile(VOICEMAIL_NUMBER)
	response=plivo.Response()
	response.addMessage(src=CALLER_ID,dst=MOBILE,body=MESSAGE)
	response=make_response(response.to_xml())

	response.headers['Content-Type']='text/xml'
	
	return response




if __name__ == '__main__':
       app.run(host='0.0.0.0')

