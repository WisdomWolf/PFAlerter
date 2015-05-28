#! python3
#Requires PyWin32 (http://sourceforge.net/projects/pywin32/)
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
import itertools
from configparser import ConfigParser
from socket import gaierror
from email.message import Message

class PFAlert:

    JSON_REQ = 'application/json'
    HEADERS = {'Accept':JSON_REQ}

    def __init__(self, configFile, threshold=None, timerResolution=None,
                 emailRecipients=None, transactFile=None
                ):
        self.config = ConfigParser()
        self.config.read(configFile)
        self.file = configFile
        self.transactFile = transactFile or os.path.join(os.path.dirname(configFile), 'lastTransactionTimes.ini')
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
        recipients = self.config['Email']['receiverAddresses']
        self.emailRecipients = recipients.split(';')
        self.FROM = self.config['Email']['from']
        self.threshold = self.config['Settings']['threshold']
        self.timerResolution = self.config['Settings']['interval']
        self.server = self.prepareSMTPServer()
        self.killed = False
        
    def prepareSMTPServer(self):
        """Setup SMTP Server connection for email sending"""
        
        try:
            server = smtplib.SMTP(self.smtpServer, self.serverPort)
        except gaierror:
            self.writeToLog('Error with socket.  Shutting Down.')
            self.tearDown()
        server.ehlo()
        
        if server.has_extn('STARTTLS'):
            server.starttls()
        
        try:
            server.login(self.emailUser, self.emailPassword)
        except smtplib.SMTPAuthenticationError:
            self.writeToLog('Unable to authenticate with provided credentials.  Shutting Down.')
            self.tearDown()
            
        return server
            
    def tearDown(self):
        """Tear Down existing connections"""
        
        try:
            self.server.quit()
        except smtplib.SMTPServerDisconnected:
            self.writeToLog('SMTP Server disconnected unexpectedly')
            
        self.writeToLog('Shutting down service')
        self.killed = True
        time.sleep(5)
        os._exit(0)
        
    def sendEmail(self, subject=None, text=None):
        """Sends Email
        
        Keyword arguments:
        subject -- Email subject
        text -- Email body
        """
        
        SUBJECT = subject or 'Python Priority Test'
        TEXT = text or 'Sending this message with high priority because reasons.'
        
        msg = Message()
        msg['From'] = self.FROM
        # msg['To'] = self.emailRecipients
        msg['To'] = ", ".join(self.emailRecipients)
        msg['X-Priority'] = '1'
        msg['Subject'] = SUBJECT
        msg.set_payload(TEXT)
        
        #Prepare actual message
        message = '\r\n'.join(['To: %s' % self.emailRecipients, 'From: %s' % self.FROM, 'Subject: %s' % SUBJECT, '', TEXT])
        
        try:
            failures = self.server.sendmail(self.FROM, self.emailRecipients, msg.as_string())
            if failures:
                for x in failures:
                    self.writeToLog('Mail send error: ' + str(x))
            self.writeToLog('Sucessfully sent the mail')
        #except smtplib.SMTPDataError:
        #    print("Failed to send mail.  Possible permissions error.")
        except:
            print('Failed to send mail.\nUnexpected Error:', sys.exc_info()[0], '\n', sys.exc_info()[1])
            self.writeToLog('Failed to send mail.\nUnexpected Error:', sys.exc_info()[0], '\n', sys.exc_info()[1])
    
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
        try:
            response = urllib.request.urlopen(req)
        except urllib.error.URLError:
            self.sendEmail('PF Server is down', 'Unable to reach the Pilot Fish server.')
            return None
        else:
            #Reset flag
            pass
        str_response = response.readall().decode('utf-8')
        
        return json.loads(str_response)
        
    def testJSON(self, file=None):
        """test json information against threshold
        
        Keyword arguments:
        file -- JSON information file (Optional)
        """
        
        #self.buildRequester()
        #jsonData = self.pullJSON()
        #jsonToTextFile(jsonData)
        if file:
            data = pullJSONFromTextFile(file)
        else:
            data = pullJSON()
            
        listenerList = self.getListenerList(data)
        self.listenersIterator(listenerList)
        
    def getListenerList(self, data):
        data = json.loads(data)
        return data['ListenersContainer']['Listener']
        
    def listenersIterator(self, listenerList):
        """Loops over all listeners and calls thresholdCompare for determining threshold violations.
        
        Keyword arguments:
        listenerList -- list of all listeners to be used for comparison
        """
        
        alarmList = {}
        listenerName = ''
        
        for listener in listenerList:
            #parse listenerName and timeSinceLastTransaction
            listenerName = listener['name']
            timeSinceLastTransaction = listener['TimeSinceLastTransaction']
            a, t = self.thresholdCompare(listenerName, timeSinceLastTransaction, int(self.threshold))
            if a:
                alarmList[a] = t
        
        if alarmList:
            self.soundAlarm(alarmList)
        
    def thresholdCompare(self, listenerName, timeSinceLastTransaction, threshold):
        """Compares transaction time to threshold and sounds alarm if necessary.
        
        Keyword arguments:
        listenerName -- the name of the listener being compared
        timeSinceLastTransaction -- time in milliseconds since last transaction completed
        threshold -- time in seconds representing maximum acceptable time since last transaction completed
        """
        
        alarmer = None
        epoch = int(time.time())
        timeSinceLastTransaction = int(timeSinceLastTransaction / 1000)
        lastTransactionTime = 0
        lastTransactionLogged = self.readTransactionTime(listenerName)
        
        if timeSinceLastTransaction > threshold:
            lastTransactionTime = int(epoch - timeSinceLastTransaction)
            
            if lastTransactionTime > lastTransactionLogged:
                print('Sounding Alarm for:', listenerName, lastTransactionTime, lastTransactionLogged)
                alarmer = listenerName
                
            self.writeToLog(str(listenerName) + " hasn't had a transaction since " + time.strftime('%m-%d-%Y %H:%M', time.localtime(lastTransactionTime)))
            
        return alarmer, lastTransactionTime
        
    def soundAlarm(self, listenerAlarmMap, emailRecipients=None):
        """Generates alert email when listener reports an unacceptable transaction time.
        
        Keyword arguments:
        listenerAlarmMap -- dictionary containing listeners that haven't transacted in an acceptable timeframe
        emailRecipients -- addresses to send alert to (Optional)
        """
        try:
            winsound.PlaySound("C:\Windows\Media\Alarm10.wav", winsound.SND_FILENAME)
        except RuntimeError:
            print('Not playing sound file because reasons')
        print('\n***\nAlarm Sounded!\n***\n')
        
        if len(listenerAlarmMap) > 5:
            minItems = round(len(listenerAlarmMap) / 5)
            mapLists = list(split_seq(listenerAlarmMap, minItems))
            for listeners in mapLists:
                subject = 'Alert! Multiple listeners have gone too long without a transaction'
                body = ''
                for listener in listeners:
                    append = 'Last transaction on ' + str(listener) + ' was at ' + time.strftime('%I:%M%p on %a, %b %d, %Y', time.localtime(listenerAlarmMap[listener])) + '.\r\n'
                    body += append
                    self.saveTransactionTime(listener, listenerAlarmMap[listener])
                        
                self.sendEmail(subject, body)
                
        else:
            for listenerName, lastTransactionTime in listenerAlarmMap.items():
                print('***\nAlarm on', listenerName, '\n***')
                subject = 'Alert! ' + str(listenerName) + ' last transaction was ' + time.strftime('%I:%M%p on %a, %b %d, %Y', time.localtime(lastTransactionTime))
                body = 'You are receiving this alert because it has been more than ' + self.threshold + ' seconds since there was a transaction on ' + listenerName
                self.sendEmail(subject, body)
                self.saveTransactionTime(listenerName, lastTransactionTime)
                
        self.writeToLog('Alert Email sent')
                    
    def saveTransactionTime(self, listenerName, lastTransactionTime):
        config = ConfigParser()
        file = self.transactFile
        config.read(file)
        config[listenerName] = {'Last Transaction Time': str(lastTransactionTime)}
        with open(file, 'w') as f:
            config.write(f)
            
    def readTransactionTime(self, listenerName):
        config = ConfigParser()
        file = self.transactFile
        config.read(file)
        try:
            result = int(config[listenerName]['Last Transaction Time'])
        except (KeyError, NameError):
            result = 1
            
        return result
        
    def writeToLog(self, data, timestamp=None, log_file=None):
        """Writes important information to log file.
        
        Keyword arguments:
        data -- the information to write
        timestamp -- time of event occurence (Default %m-%d-%Y %H:%M)
        log_file -- the file to be written (Default PFAlerter.log)
        """
        
        timestamp = timestamp or time.strftime('%c')
        log_file = log_file or 'C:/Users/Public/Documents/PFAlerter.log'
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
    
def sendEmail(subject=None, text=None):
    """convenience method for accessing object's sendMail method"""
    alertTest.sendEmail(subject, text)
    
def split_seq(iterable, size):
    it = iter(iterable)
    item = list(itertools.islice(it, size))
    while item:
        yield item
        item = list(itertools.islice(it, size))
    
def buildObject(file=None):
    file = file or 'C:\\Users\\Public\\Documents\\config.ini'
    return PFAlert(file)
    
def runTest():
    alertTest = buildObject()
    s = sched.scheduler(time.time, time.sleep)
    print('Running...\n')
    while(True):
        s.enter(float(alertTest.timerResolution), 1, alertTest.testJSON, argument=('C:\\Users\\Public\\Documents\\testJSON2.txt',))
        s.run()