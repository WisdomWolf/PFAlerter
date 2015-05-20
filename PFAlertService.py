#! python3
import sched
import time
import codecs
import winsound
import pythoncom
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
from tkinter import messagebox
from PFAlerter import PFAlert


class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "PFAlertService"
    _svc_display_name_ = "Pilot Fish Alert Service"
    s = sched.scheduler(time.time, time.sleep)
    isAlive = True

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.isAlive = False
        self.alerter.tearDown()
        self.alerter.writeToLog('Service stopped.')

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        self.alerter = PFAlert('C:/Users/Public/Documents/config.ini')
        self.alerter.writeToLog('Service started.')
        while self.isAlive:
            if self.alerter.killed:
                self.alerter.writeToLog('Service received kill command.  Stopping service.')
                messagebox.showinfo(title='Critical Error', message='PFAlert service has died.')
            #self.s.enter(10, 1, test_time, argument=(5,)) #trailing comma is necessary because argument is a sequence
            self.s.enter(float(self.alerter.timerResolution), 1, self.alerter.testJSON, argument=('C:/Users/Public/Documents/testJSON2.txt',))
            self.s.run()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)