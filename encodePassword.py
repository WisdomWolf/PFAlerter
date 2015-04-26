#! python3
import base64
import codecs
<<<<<<< HEAD
import clipboard

with codecs.open('password.txt', 'w', 'utf-8') as simpleOutput:
    x = input('Enter password to encode:\n')
    b = str.encode(x)
    print('password encoded:')
    y = (base64.b64encode(b)).decode()
    simpleOutput.write(y)
    print(y)
    clipboard.copy(y)
    input('complete')
=======

x = input('Enter password to encode:\n')
print('password encoded:')
y = base64.b64encode(x)
print(y)
input('')
>>>>>>> 646f5deb74d9f863cb4ccfb3ae862487f8ddbdd7

