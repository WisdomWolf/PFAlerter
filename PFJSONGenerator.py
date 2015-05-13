#! python3

import sched
import time
import json
import string
import codecs
import random
from configparser import ConfigParser


def getListenerList(data):
    data = json.loads(data)
    return data, data['ListenersContainer']['Listener']
    
def importConfigValues():
    config = ConfigParser()
    config.read('C:/Users/Public/Documents/config.ini')
    global threshold
    threshold = int(config['Settings']['threshold'] * 1000)
    timerResolution = config['Settings']['interval']
    
def buildTestJSON(fileIn, fileOut, newElementKey=None, newElementValue=None):
    """generates JSON txt file adding the key and values specified by the user
    
    Keyword arguments:
    fileIn -- the file containing JSON data to be read
    fileOut -- the file to direct results to
    """
    
    data = open(fileIn).read()
    data, testList = getListenerList(data)
    newElementKey = newElementKey or 'TimeSinceLastTransaction'
    
    for i, j in zip(testList, range(1, len(testList)+1)):
        newElementValue = newElementValue or '350000'
        i[newElementKey] = int(newElementValue)
    
    data['ListenersContainer']['Listener'] = testList
    jsonToTextFile(data, fileOut)
    return
    
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
    
def lastTransactionCounter(fail=None):
    global timeSinceLastTransaction
    if timeSinceLastTransaction >= threshold and not fail:
        timeSinceLastTransaction = 1000
    else:
        timeSinceLastTransaction += (interval * 1000)
def runTest():
    fail = False
    if random.randint(0, 10) > 1:
        fail = True
    lastTransactionCounter(fail)
    lastTransactionTime = int(time.time() - (timeSinceLastTransaction / 1000))
    buildTestJSON('tempJSON2.txt', 'testJSON2.txt', newElementValue=timeSinceLastTransaction)
    print(timeSinceLastTransaction, '|', lastTransactionTime, '|', fail)
    
s = sched.scheduler(time.time, time.sleep)
interval = 1
timeSinceLastTransaction = 1000
importConfigValues()
while(True):
    s.enter(interval, 1, runTest)
    s.run()