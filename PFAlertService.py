#! python3
import sched, time, codecs, winsound

s = sched.scheduler(time.time, time.sleep)
compareTime = 0

def print_time(a='...'):
    print('30 seconds have passed', int(time.time()), a)
    
def test_time(a=5):
    compareTime = get_compare_time()
    print('Comparing current time', int(time.time()))
    if int(time.time()) > (int(compareTime) + (a * 60)):
        print('its been too long since last compare:', compareTime)
        winsound.PlaySound("C:\Windows\Media\Alarm10.wav", winsound.SND_FILENAME)
    else:
        print('All good.  Last compare:', compareTime)
    
def print_some_times():
    print(time.time())
    s.enter(10, 1, print_time)
    s.run()
    print(time.time())
    
def get_compare_time():
    with codecs.open('time.txt', 'r', 'utf-8') as file:
        result = ''
        for line in file:
            result = line
        return result
    
print('beginning test, current time =', int(time.time()))
    

while (time.time() < 1430092800):
    s.enter(10, 2, test_time, argument=(5,))
    s.run()
    