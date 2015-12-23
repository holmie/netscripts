#!/usr/bin/env python2.7
"""
Zabbix API CGI Wrapper by Espen Holm Nilsen

Hackish wrapper for the Zabbix API to return some values I needed

This script returns just the value as a plain string.
Running this as CGI.

I am assuming you can install pyzabbix by "pip install pyzabbix"

"""
from pyzabbix import ZabbixAPI
from datetime import datetime
import time, json, sys
import cgi

form = cgi.FieldStorage()


ZABBIX_SERVER = "https://my.zabbix/server/"

zapi = ZabbixAPI(ZABBIX_SERVER)
zapi.login('zabbix_api_user', 'password')

item_id = form.getvalue('itemid')
history = zapi.history.get(itemids=[item_id], history='0', sortfield='clock', sortorder='DESC', output='extend', limit='1')

lastvalue = 0.0

def humanAgo(seconds):
	if seconds > 86400:
		return """%d dager siden""" % (seconds/3600)
	if seconds > 3600:
		return """%d timer siden""" % (seconds/3600)
	if seconds > 60:
		return """%d minutter siden""" % (seconds/60)
	else:
		return """%d sekunder siden""" % seconds

if len(history) == 0:
	currvalue = ""
	statechange = int(time.time())
	print "Content-type: application/json\n"
	history = zapi.history.get(itemids=[int(item_id)], history='3', output='extend', limit='20000', sortfield='clock', sortorder='DESC')
	for p in reversed(history):
		if p['value'] != currvalue:
			currvalue = p['value']
			statechange = p['clock']

	print currvalue
	sys.exit(0)
last = history[0]


print "Content-type: application/json"
print
last['ago'] = humanAgo(int(time.time()) - int(last['clock']))

print last['value']
