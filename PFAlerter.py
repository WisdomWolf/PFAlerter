#! python3
import os 
import sys
import json
import codecs
import string
import urllib.request
import smtplib
import base64
import pdb
import time
import sched
import winsound
from configparser import ConfigParser
from socket import gaierror

class PFAlert:

    JSON_REQ = 'application/json'
    HEADERS = {'Accept':JSON_REQ}

    def __init__(self, configFile, threshold=None, timerResolution=None,
                 emailRecipients=None
                ):
        self.config = ConfigParser()
        self.config.read(configFile)
        self.file = configFile
        self.theurl = self.config['PF Listener']['url']
        self.serverUsername = self.config['PF Listener']['username']
        self.serverPassword = self.config['PF Listener']['password']
        self.smtpServer = self.config['Email']['smtpServer']
        try:
            self.serverPort = int(self.config['Email']['serverPort'])
        except ValueError:
            input('malformed config file. <Bad Server Port> Aborting...')
            os._exit(0)
        self.emailUser = self.config['Email']['senderAddress']
        self.emailPassword = (base64.b64decode(self.config['Email']['senderPassword'])).decode()
        self.emailRecipients = self.config['Email']['receiverAddresses']
        self.FROM = self.config['Email']['from']
        self.threshold = self.config['Settings']['threshold']
        self.timerResolution = self.config['Settings']['interval']
        
    def sendEmail(self, subject=None, text=None):
        SUBJECT = subject or 'Python Test'
        TEXT = text or 'Testing sending message with python'
        
        #Prepare actual message
        message = '\r\n'.join(['To: %s' % self.emailRecipients, 'From: %s' % self.FROM, 'Subject: %s' % SUBJECT, '', TEXT])
        
        try:
            server = smtplib.SMTP(self.smtpServer, self.serverPort)
        except gaierror:
            input('Error with socket.  Aborting...')
            os._exit(0)
        server.ehlo()
        
        if server.has_extn('STARTTLS'):
            server.starttls()
        
        try:
            server.login(self.emailUser, self.emailPassword)
        except smtplib.SMTPAuthenticationError:
            input('Unable to authenticate with provided credentials.  Aborting...')
            os._exit(0)
        
        try:
            server.sendmail(self.FROM, self.emailRecipients, message)
            print("Sucessfully sent the mail")
        #except smtplib.SMTPDataError:
        #    print("Failed to send mail.  Possible permissions error.")
        except:
            print('Failed to send mail.\nUnexpected Error:', sys.exc_info()[0], '\n', sys.exc_info()[1])
            
        server.quit()
    
    def buildRequester(self):
        """builds the authentication and request handlers"""
        
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        # this creates a password manager
        passman.add_password(None, self.theurl, self.serverUsername, self.serverPassword)
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

    def pullJSON(self):
        """pulls the JSON data and puts it into Python object format"""
        
        self.buildRequester()
        
        req = urllib.request.Request(self.theurl, None, PFAlert.HEADERS)
        response = urllib.request.urlopen(req)
        str_response = response.readall().decode('utf-8')
        
        return json.loads(str_response)
        
    def JSONTest(self, jsonSourceFile=None):    
        #self.buildRequester()
        #jsonData = self.pullJSON()
        #jsonToTextFile(jsonData)
        jsonData = pullJSONFromTextFile(jsonSourceFile)
        listenerList = jsonData['ListenersContainer']['Listener']
        self.TSLTIterator(listenerList)
        
    def listenersIterator(self, listenerList):
        """Loops over all listeners and calls thresholdCompare for determining threshold violations."""
        
        alarmList = {}
        listenerName = ''
        lastTransactionTime = 0
        
        for listener in listenerList:
            #parse listenerName and timeSinceLastTransaction
            listenerName = listener['name']
            timeSinceLastTransaction = listener['TimeSinceLastTransaction']
            a, t = self.thresholdCompare(listenerName, timeSinceLastTransaction, int(self.threshold))
            if a:
                alarmList[a] = t
        
        if alarmList:
            self.soundAlarm(alarmList, lastTransactionTime)
        
    def thresholdCompare(self, listenerName, timeSinceLastTransaction, threshold):
        """Compares transaction time to threshold and sounds alarm if necessary."""
        
        alarmer = None
        epoch = int(time.time())
        timeSinceLastTransaction = int(timeSinceLastTransaction / 1000)
        lastTransactionTime = 0
        
        try:
            lastTransactionLogged = int(self.config[listenerName]['Last Transaction Time'])
        except (KeyError, NameError):
            print('No value found for', listenerName)
            lastTransactionLogged = 1
        
        if timeSinceLastTransaction > threshold:
            lastTransactionTime = int(epoch - timeSinceLastTransaction)
            
            if lastTransactionTime > lastTransactionLogged:
                print('Sounding Alarm for:', listenerName, lastTransactionTime, lastTransactionLogged)
                alarmer = listenerName
                
            self.writeToLog(str(listenerName) + " hasn't had a transaction since " + time.strftime('%m-%d-%Y %H:%M', time.localtime(lastTransactionTime)))
            
        return alarmer, lastTransactionTime
        
    def soundAlarm(self, listenerNames, lastTransactionTime, emailRecipients=None):
        """Generates alert email when listener reports an unacceptable transaction time"""
        
        print('\n***\nAlarm Sounded!\n***\n')
        winsound.PlaySound("C:\Windows\Media\Alarm10.wav", winsound.SND_FILENAME)
        for listenerName in listenerNames:
            self.config[listenerName] = {'Last Transaction Time': str(lastTransactionTime)}
            print('***\nAlarm on', listenerName, '\n***')
        with open(self.file, 'w') as configfile:
            self.config.write(configfile)
        
    def writeToLog(self, data, timestamp=None, log_file=None):
        timestamp = timestamp or time.strftime('%m-%d-%Y %H:%M')
        log_file = log_file or 'PFAlerter.log'
        with codecs.open(log_file, 'a+', 'utf-8') as file:
            file.write(str(timestamp) + ' - ' + str(data) + '\r\n')
        
def pullJSONFromTextFile(fileIn):
    return open(fileIn).read()

    
def jsonToTextFile(data, fileName):
    """sends the json data to text file with 'pretty printing'
    
    Keyword arguments:
    data -- the json object to parse
    fileName -- the file to save results to
    """
    
    data = json.dumps(data, sort_keys=True, indent=4)
    with codecs.open(fileName, 'w+', 'utf-8') as save_file:
        save_file.write(str(data))
    return
    
def getListenerList(data):
    data = json.loads(data)
    return data['ListenersContainer']['Listener']
    
def buildTestJSON(fileIn, fileOut, newElementKey=None):
    """generates JSON txt file adding the key and values specified by the user
    
    Keyword arguments:
    fileIn -- the file containing JSON data to be read
    fileOut -- the file to direct results to
    """
    
    data = open(fileIn).read()
    testList = getListenerList(data)
    newElementKey = newElementKey or input('Enter name of new element key: ')
    
    for i, j in zip(testList, range(1, len(testList)+1)):
        print('\r\n', j, ".", i['name'])
        newElementValue = input(str(newElementKey) + ': ')
        i[newElementKey] = int(newElementValue)
    
    data['ListenersContainer']['Listener'] = testList
    jsonToTextFile(data, fileOut)
    return
    
def pullJSONValues(key, list):
    """returns a list from the JSON of the element specified"""
    elementList = []
    for i in list:
        print(i[key])
        elementList.append(i[key])
    
    return elementList

def testJSON(alert, file):
    data = pullJSONFromTextFile(file)
    listenerList = getListenerList(data)
    alert.listenersIterator(listenerList)
    
#sendEmail()
#with codecs.open('listener_list.txt', 'w+', 'utf-8') as save_file:
  #  save_file.write(listenerStr)

alertTest = PFAlert('C:/Users/Public/Documents/config.ini')
s = sched.scheduler(time.time, time.sleep)
#pdb.set_trace()
print('Running...\n')
while(True):
    s.enter(float(alertTest.timerResolution), 1, testJSON, argument=(alertTest, 'testJSON2.txt'))
    s.run()