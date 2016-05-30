#!/usr/bin/env python


import sys
import httplib
import json
import time
import traceback

host = '10.4.0.4'
port = 8091
flow_name = ""

def _forward2Controller(host, port, method, url, body = None):
    print "%s, %s, %s, %s" %(host, port, method, url)
    
    res = None
    try:
        _conn=httplib.HTTPConnection(host,port)
        if body:
           header = {"Content-Type": "application/json"}
           _conn.request(method, url, body=body, headers=header)
        else:
           _conn.request(method, url)
        res = _conn.getresponse()
        ret = res.read()
    except:    
        traceback.print_exc()
        pass
    if res.status in (httplib.OK,
                      httplib.CREATED,
                      httplib.ACCEPTED,
                      httplib.NO_CONTENT):
        return ret

    raise httplib.HTTPException(
        res, 'code %d reason %s' % (res.status, res.reason),
        res.getheaders(), res.read())


def _chain(in_ip, ip_a, ip_b): 
    ret = _forward2Controller(host, port, 'POST', '/v1.0/network/networks/path/%s_%s' %(in_ip, ip_a))
    print ret
    resp = json.loads(ret)
    if resp.get('complete', False) is False:
       if resp.get('request_submitted', False) is False:
          return
    time.sleep(2)
    ret = _forward2Controller(host, port, 'POST', '/v1.0/network/networks/path/%s_%s' %(in_ip, ip_b))
    print ret
    resp = json.loads(ret)
    if resp.get('complete', False) is False:
       if resp.get('request_submitted', False) is False:
          return
    time.sleep(2)
    ret = _forward2Controller(host, port, 'POST', '/v1.0/network/networks/path/%s_%s' %(ip_b, ip_a))
    print ret
    resp = json.loads(ret)
    if resp.get('complete', False) is False:
       if resp.get('request_submitted', False) is False:
          return
    time.sleep(2)
    ret = _forward2Controller(host, port, 'GET', '/v1.0/network/networks/path/%s_%s' %(in_ip, ip_b))
    resp1 = json.loads(ret)
    ret = _forward2Controller(host, port, 'GET', '/v1.0/network/networks/path/%s_%s' %(ip_a, ip_b))
    resp2 = json.loads(ret)

    mac_a = resp2['src_mac'] 
    mac_b = resp2['dst_mac'] 
    mac_in = resp1['src_mac'] 
    
    path = resp1['path']

    l = len(path)
    for idx,p in enumerate(path):
       (dpid, in_port, out_port) = p
       print "%s, %s, %s" %(dpid, in_port, out_port)
       if idx == (l - 1):
           out_port = 2
       flow1 = {}
       flow1 = {'user_id': flow_name, 'hard_timeout': 0, 'actions': [{'type': 'OUTPUT', 'port': out_port}], 'priority': 60000, 'idle_timeout': 0, 'cookie': 0}
       flow1.update({'dpid': int(dpid, 16), 'match': {'dl_type': 2048, 'nw_proto': 1, 'dl_src': mac_in, 'dl_dst': mac_a,  
                                                  'in_port': in_port}})
       flow1['match'].pop('nw_proto')
       print flow1
       ret = _forward2Controller(host, port, 'POST', '/v1.0/network/networks/user_flow_add/%s' % flow1.get('dpid'), json.dumps(flow1))
       print (dpid, ret)
       if idx == (l - 1):
           out_port=in_port
           in_port = 3
           flow1 = {}
           flow1 = {'user_id': flow_name, 'hard_timeout': 0, 'actions': [{'type': 'OUTPUT', 'port': out_port}], 'priority': 60000, 'idle_timeout': 0, 'cookie': 0}
           flow1.update({'dpid': int(dpid, 16), 'match': {'dl_type': 2048, 'nw_proto': 1, 'dl_dst': mac_in,
                                                  'in_port': in_port}})
           flow1['match'].pop('nw_proto')
           print flow1
           ret = _forward2Controller(host, port, 'POST', '/v1.0/network/networks/user_flow_add/%s' % flow1.get('dpid'), json.dumps(flow1))


    path = resp2['path']

    l = len(path)
    for idx,p in enumerate(path):
       (dpid, in_port, out_port) = p
       print "%s, %s, %s" %(dpid, in_port, out_port)
       if idx == (l - 1):
           out_port = 2
       flow1 = {}
       flow1 = {'user_id': flow_name, 'hard_timeout': 0, 'actions': [{'type': 'OUTPUT', 'port': out_port}], 'priority': 60000, 'idle_timeout': 0, 'cookie': 0}
       flow1.update({'dpid': int(dpid, 16), 'match': {'dl_type': 2048, 'nw_proto': 1, 'dl_src': mac_a, 'dl_dst': mac_in,
                                                  'in_port': in_port}})
       flow1['match'].pop('nw_proto')
       print flow1
       ret = _forward2Controller(host, port, 'POST', '/v1.0/network/networks/user_flow_add/%s' % flow1.get('dpid'), json.dumps(flow1))
       print (dpid, ret)
       if idx == (l - 1):
           out_port=in_port
           in_port = 3
           flow1 = {}
           flow1 = {'user_id': flow_name, 'hard_timeout': 0, 'actions': [{'type': 'OUTPUT', 'port': out_port}], 'priority': 60000, 'idle_timeout': 0, 'cookie': 0}
           flow1.update({'dpid': int(dpid, 16), 'match': {'dl_type': 2048, 'nw_proto': 1, 'dl_dst': mac_a,
                                                  'in_port': in_port}})
           flow1['match'].pop('nw_proto')
           print flow1
           ret = _forward2Controller(host, port, 'POST', '/v1.0/network/networks/user_flow_add/%s' % flow1.get('dpid'), json.dumps(flow1))
           print (dpid, ret)

    """
    dst_mac = resp['dst_mac']
    src_gw_mac = resp['src_gw_mac']
    dst_gw_mac = resp['dst_gw_mac']
    path = resp['path']
    print path
    if len(path) > 1:
        (src_dpid, src_in_port, src_out_port)  = path[0]
        (dst_dpid, dst_out_port, dst_in_port)  = path[len(path) - 1]
    elif len(path) == 1:
        (src_dpid, src_in_port, src_out_port)  = path[0]
        (dst_dpid, dst_out_port, dst_in_port)  = path[0]

    print (src_dpid, src_in_port, src_out_port)
    print (dst_dpid, dst_out_port, dst_in_port)
    
    flow1 = {}
    flow1 = {'user_id': 'hadi', 'hard_timeout': 0, 'actions': [{'type': 'OUTPUT', 'port': src_out_port}], 'priority': 60000, 'idle_timeout': 0, 'cookie': 0}
    flow1.update({'dpid': int(src_dpid, 16), 'match': {'dl_type': 2048, 'nw_dst': '%s/32' % dst_ip, 'tp_proto': 6, 'dl_src': src_mac, 'dl_dst': src_gw_mac, 'nw_src': '%s/32' % src_ip, 
                                                  'in_port': src_in_port}})
    flow1['actions'] = []    
    flow1['actions'].append({'type': 'SET_DL_DST', 'dl_dst': dst_mac})
    flow1['actions'].append({'type': 'OUTPUT', 'port': src_out_port})
    
    flow2 = {}
    flow2 = {'user_id': 'hadi', 'hard_timeout': 0, 'actions': [{'type': 'OUTPUT', 'port': dst_out_port}], 'priority': 60000, 'idle_timeout': 0, 'cookie': 0}
    flow2.update({'dpid': int(dst_dpid, 16), 'match': {'dl_type': 2048, 'nw_dst': '%s/32' % src_ip, 'tp_proto': 6, 'dl_src': dst_mac, 'dl_dst': dst_gw_mac, 'nw_src': '%s/32' % dst_ip, 
                                                  'in_port': dst_in_port}})
    flow2['actions'] = []    
    flow2['actions'].append({'type': 'SET_DL_DST', 'dl_dst': src_mac})
    flow2['actions'].append({'type': 'OUTPUT', 'port': dst_out_port})
        
    #ret = _forward2Controller(host, port, 'POST', '/stats/flowentry/add', json.dumps(flow1))
    ret = _forward2Controller(host, port, 'POST', '/v1.0/network/networks/user_flow_add/%s' % flow1.get('dpid'), json.dumps(flow1))
    print (src_dpid, ret)
    
    #ret = _forward2Controller(host, port, 'POST', '/stats/flowentry/add', json.dumps(flow2))
    ret = _forward2Controller(host, port, 'POST', '/v1.0/network/networks/user_flow_add/%s' % flow2.get('dpid'), json.dumps(flow2))
    print (dst_dpid, ret)
    """

def main(argv):
    if len(argv) < 6:
        print "Usage: ./chaining.py <endpoing 1> <endpoing 2> <middlebox> <janus ip> <flow name>"
        sys.exit()

    global host
    global flow_name

    in_ip = argv[1]
    ip_a = argv[2]
    ip_b = argv[3]
    host = argv[4]
    flow_name = argv[5]
    print "chain connection of %s to %s via %s" %(in_ip, ip_a, ip_b)
    print "SDI manager IP %s and port %s" % (host, port)
    print "Rules to be installed with name %s" % (flow_name)

    _chain(in_ip, ip_a, ip_b)

def create_chain(ep1="", ep2="", middlebox="", janus_ip="", flowname=""):
    global host
    global flow_name

    in_ip = ep1 
    ip_a = ep2 
    ip_b = middlebox 
    host = janus_ip
    flow_name = flowname
    
    print "chain connection of %s to %s via %s" %(in_ip, ip_a, ip_b)
    print "SDI manager IP %s and port %s" % (host, port)
    print "Rules to be installed with name %s" % (flow_name)

    _chain(in_ip, ip_a, ip_b)
    

if __name__ == '__main__':
     #main(sys.argv)
     create_chain(ep1="192.168.194.5", ep2="192.168.183.176", middlebox="192.168.208.204", janus_ip="142.150.208.237", flowname="span")
     #create_chain(ep1="54.174.135.135", ep2="54.175.202.161", middlebox="142.150.208.204", janus_ip="10.12.1.23", flowname="span")

