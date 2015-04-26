#! python3
import base64
import codecs

x = input('Enter password to encode:\n')
print('password encoded:')
y = base64.b64encode(x)
print(y)
input('')

