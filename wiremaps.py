#!/usr/bin/env python
import requests, json, re

# script that shows how to use the wiremaps API, generates a dotfile to generate a network map of the information in wiremaps by vincent bernat (https://github.com/vincentbernat/wiremaps)

# the api base url should go here (replace WIREMAPSHOST with the IP/Hostname of the wiremaps box and PORT with the port twistd is running at
api_url = """http://WIREMAPSHOST:PORT/api/1.1/"""

all_equipment = json.loads(requests.get(api_url + "equipment/").text)
connections = {}

print """digraph network {"""

for (node, ip) in all_equipment:
	ports = json.loads(requests.get(api_url + "equipment/" + ip).text)

	for (ifindex, ifname, ifdescr, ifstatus, ifspeed, unk1, unk2) in ports:
		portinfo = json.loads(requests.get(api_url + "equipment/" + ip + "/" + str(ifindex)).text)
		if (len(portinfo) > 2):
			for pstuff in portinfo:
				if pstuff[0].find('Host') != -1:
					node = re.sub(r'\([^)]*\)', '', node)
					node = re.sub(r' ', '_', node)
					node = re.sub(r'\.', '-', node)
					connected = re.sub(r'\([^)]*\)', '', pstuff[2])
					connected = re.sub(r' ', '_', connected)
					connected = re.sub(r'\.', '-', connected)
					connections[node + " -> " + connected] = 1

for connection in connections.keys():
	print connection + """;"""

print """}"""
