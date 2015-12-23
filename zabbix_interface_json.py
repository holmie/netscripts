#!/usr/bin/env python2.7
"""
Hackish script to return some values I needed from Zabbix, returns beautiful json output
that can be used by other scripts/things/graphers/etc!

I am using this with openhab and highcharts to do whatever magic I need at home.

Requires: pyzabbix  (pip install pyzabbix)

Run as CGI, call with this_script.py?itemid=<itemid>

Demo:
$ curl "http://192.168.1.1/cgi/zinterf.py?itemid=25895"
{"itemid": "25895", "ago": "1 minutter siden", "ns": "565486588", "value": "29.0000", "clock": "1450859171"}
$

OpenHAB config:
$ cat /etc/openhab/configurations/transform/getvalue.js
JSON.parse(input).value;
$ grep getvalue /etc/openhab/configurations/items/*.items
Number Temperature_FF_Living    "Temperature [%.2f C]"      <temperature>   (Temperature, FF_Living) { http="<[http://192.168.1.1/zinterf.py?itemid=25882:10000:JS(getvalue.js)]" }


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

	print json.dumps({'value': currvalue, 'ago': humanAgo(int(time.time()) - int(statechange))})
	sys.exit(0)
last = history[0]


print "Content-type: application/json"
print
last['ago'] = humanAgo(int(time.time()) - int(last['clock']))
print json.dumps(last)
