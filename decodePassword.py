#! python3
import base64
import codecs
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
theurl = config['PF Listener']['url']
username = config['PF Listener']['username']
password = config['Email']['senderPassword']
p2 = (base64.b64decode(config['Email']['senderPassword'])).decode()
p = base64.b64decode(password)


print('password: ' + password)
print('Decoded password: ' + p.decode())
print('p2: ' + p2)
input('...')
    