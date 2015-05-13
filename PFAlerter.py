#! python3
import os, sys, json, codecs, string
import urllib.request, smtplib, base64
import pdb, time, sched
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
        
    def TSLTIterator(self, listenerList):
        """Loops over all listeners and calls thresholdCompare for determining threshold violations."""
        
        for listener in listenerList:
            #parse listenerName and timeSinceLastTransaction
            listenerName = listener['name']
            timeSinceLastTransaction = listener['TimeSinceLastTransaction']
            self.thresholdCompare(listenerName, timeSinceLastTransaction, 300000)
        
    def thresholdCompare(self, listenerName, timeSinceLastTransaction, threshold):
        """Compares transaction time to threshold and sounds alarm if necessary."""
        
        if timeSinceLastTransaction > threshold:
            lastTransactionTime = epoch - timeSinceLastTransaction
            if lastTransactionTime > self.config['listenername']['Last Transaction Time']:
                soundAlarm(listenerName)
            writeToLog(str(listenerName) + " hasn't had a transaction since " """+ human readable formatted(lastTransactionTime)""")
        pass
        
    def soundAlarm(self, listenerName=None, emailRecipients=None):
        """Generates alert email when listener reports an unacceptable transaction time"""
        pass
        
    def writeToLog(self, data, timestamp=None, log_file=None):
        timestamp = timestamp #or current time
        log_file = log_file or 'PFAlerter.log'
        with codecs.open(log_file, 'w+', 'utf-8') as file:
            file.write(timestamp, data)
        
def pullJSONFromTextFile(fileIn):
    return open(fileIn).read()

    
def jsonToTextFile(data, fileName):
    """sends the json data to text file with 'pretty printing'"""
    
    data = json.dumps(data, sort_keys=True, indent=4)
    with codecs.open(fileName, 'w+', 'utf-8') as save_file:
        save_file.write(str(data))
    return
    
def buildTestJSON(fileIn, fileOut):
    """gnenerates JSON txt file adding the key and values specified by the user"""
    data = open(fileIn).read()
    data = json.loads(data)
    testList = data['ListenersContainer']['Listener']
    newElementKey = input('Enter name of new element key: ')
    
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
    
#sendEmail()
#with codecs.open('listener_list.txt', 'w+', 'utf-8') as save_file:
  #  save_file.write(listenerStr)

alertTest = PFAlert('config.ini')
s = sched.scheduler(time.time, time.sleep)
#while(True):
    #s.enter(10, 1, test_time, argument=(5,)) #trailing comma is necessary because argument is a sequence
    #s.run()
pdb.set_trace()