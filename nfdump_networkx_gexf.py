#!/usr/bin/env python
import networkx as nx, commands, csv

G = nx.Graph()

nf_file = "nfcapd.201303182355"
outfile = "test.gexf"

netflow = commands.getoutput('nfdump -r ' + nf_file + ' "inet" -q -N -A srcip,dstip -o fmt:%sa,%da,%byt')
netflow = netflow.replace(' ', '').split("\n")

pairs = {}

maxsize = 0
minsize = 0

for (src,dst,bts) in csv.reader(netflow, delimiter=','):
        if (dst in pairs):
                thebts = pairs[dst][2]
                pairs[dst][2] = pairs[dst][2] + int(thebts)
                if (pairs[dst][2] > maxsize):
                        maxsize = pairs[dst][2]

        pairs[src] = [src, dst, int(bts)]

for node in pairs:
        (src, dst, bts) = pairs[node]
        G.add_edge(src, dst)

nx.write_gexf(G, outfile)
