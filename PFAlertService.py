#! python3
import sched, time, codecs, winsound
import pythoncom
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket


class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "PFAlertService"
    _svc_display_name_ = "Python Test Alert Service"
    s = sched.scheduler(time.time, time.sleep)

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        while (time.time() < 1430179200):
            s.enter(10, 2, test_time, argument=(5,))
            s.run()
            
    def test_time(a=5):
        compareTime = get_compare_time()
        print('Comparing current time', int(time.time()))
        if int(time.time()) > (int(compareTime) + (a * 60)):
            print('its been too long since last compare:', compareTime)
            winsound.PlaySound("C:\Windows\Media\Alarm10.wav", winsound.SND_FILENAME)
        else:
            print('All good.  Last compare:', compareTime)
        
    def get_compare_time():
        with codecs.open('time.txt', 'r', 'utf-8') as file:
            result = ''
            for line in file:
                result = line
            return result

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)

    