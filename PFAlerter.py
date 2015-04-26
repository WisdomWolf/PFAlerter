#! python3
import os
import sys
import json
import codecs
import urllib.request
import smtplib
import configparser
import base64

#print("JSON testing")

config = configparser.ConfigParser()
config.read('config.ini')
theurl = config['PF Listener']['url']
username = config['PF Listener']['username']
password = config['PF Listener']['password']
json_req = 'application/json'
headers = { 'Accept' : json_req }
smtpServer = config['Email']['smtpServer']
serverPort = int(config['Email']['serverPort'])
user = config['Email']['senderAddress']
pwd = (base64.b64decode(config['Email']['senderPassword'])).decode() #basic password encoding
emailRecipient = config['Email']['receiverAddress']
FROM = config['Email']['from']

#builds the authentication and request handlers
def buildRequester():
    passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    # this creates a password manager
    passman.add_password(None, theurl, username, password)
    # because we have put None at the start it will always
    # use this username/password combination for  urls
    # for which `theurl` is a super-url

    authhandler = urllib.request.HTTPBasicAuthHandler(passman)
    # create the AuthHandler

    opener = urllib.request.build_opener(authhandler)

    urllib.request.install_opener(opener)
    # All calls to urllib.request will now use our handler
    # Make sure not to include the protocol in with the URL, or
    # HTTPPasswordMgrWithDefaultRealm will be very confused.
    # You must (of course) use it when fetching the page though.
    # authentication is now handled automatically for us
    return

    #pulls the JSON data and puts it into Python object format
def pullJSON():
    req = urllib.request.Request(theurl, None, headers)
    response = urllib.request.urlopen(req)
    str_response = response.readall().decode('utf-8')
    data = json.loads(str_response)
    return data
    
    #sends the json data to text file with "pretty printing"
def jsonToTextFile(data):
    data = json.dumps(data, sort_keys=True, indent=4)
    with codecs.open('json.txt', 'w+', 'utf-8') as save_file:
        save_file.write(str(data))
    return

    # pulls a specific element from the JSON list
def pullJSONValue(key, list):
    keyStr = ""
    for i, j in zip(list, range(1, len(list)+1)):
        if j < 10:
            keyStr += str(j) + ".  " + i[key] + "\r\n"
        else:
            keyStr += str(j) + ". " + i[key] + "\r\n"
    return keyStr

def sendEmail():
    SUBJECT = "Python Test"
    TEXT = "Testing sending message with python"
    
    #Prepare actual message
    message = '\r\n'.join(['To: %s' % emailRecipient, 'From: %s' % FROM, 'Subject: %s' % SUBJECT, '', TEXT])
    
    server = smtplib.SMTP(smtpServer, serverPort)
    server.ehlo()
    
    if server.has_extn('STARTTLS'):
        server.starttls()
            
    server.login(user, pwd)
    
    try:
        server.sendmail(FROM, emailRecipient, message)
        print("Sucessfully sent the mail")
    except:
        print("Failed to send mail")
        
    server.quit()
    
#buildRequester()
#jsonData = pullJSON()
#jsonToTextFile(jsonData)

#listenerStr = "Listeners: \r\n----------\r\n"

#listenerList = jsonData['ListenersContainer']['Listener']

#listenerStr += pullJSONValue('name', listenerList)

#print(listenerStr)
sendEmail()
#with codecs.open('listener_list.txt', 'w+', 'utf-8') as save_file:
  #  save_file.write(listenerStr)

input("")