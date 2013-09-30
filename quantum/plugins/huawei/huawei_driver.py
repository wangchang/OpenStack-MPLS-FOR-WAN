import eventlet
from quantum import wsgi
import webob.exc

_huawei_controller_addr = ("192.168.1.211", 9797)
default_xml_serializer = wsgi.XMLDictSerializer()
default_xml_deserializer = wsgi.XMLDeserializer()

def remove_gang(basestr):
    return basestr.replace('-','')

def add_gang(basestr):
    str1=basestr[0:8]
    str2=basestr[8:12]
    str3=basestr[12:16]
    str4=basestr[16:20]
    str5=basestr[20:32]
    return '-'.join([str1,str2,str3,str4,str5])

def _recv_xml_from_controller(xmldata):
    data = default_xml_deserializer(xmldata)['body']
    return data

def _send_xml_to_controller(xml_serializer, data, is_create=False):
    #===========================================================================
    #  2012-12-04 add code
    #===========================================================================
    if not data:
        raise webob.exc.HTTPNotFound()
    cmd=data['document']['cmd']
    xmldata = xml_serializer(data)
    print '[driver] send xmldata = ',xmldata
    xmldata1,xmldata2=xmldata.split('<cmd>',1)
    xmldata3,xmldata4=xmldata2.split('</cmd>',1)
    xmldata5,xmldata6=xmldata1.split('<document>',1)
    cmd='<document><cmd>%s</cmd>' % cmd
    xmldata="%s%s%s" % (cmd,xmldata6,xmldata4)
    print '[driver] send xmldata =',xmldata
    #xmldata1,xmldata2=xmldata.split('>',1)
    #cmd='><cmd>%s</cmd>' % cmd
    #xmldata='%s%s%s' % (xmldata1,cmd,xmldata2)
    _socket_plugin = eventlet.connect(_huawei_controller_addr)
    _socket_plugin.send(xmldata+'\n')
    xmldata = _socket_plugin.recv(10240)
    print '[driver] recv xmldata = ',xmldata
    data=_recv_xml_from_controller(xmldata)
    print '[driver]controller return =',data
    result=data['document'].get('result', '-1')
    if result =='-1':
        return False
    if is_create:
        id = data['document'].get('vnid','')
        if id:
            print "(vnid) = ",id
            return remove_gang(id)
        else:
            id = data['document'].get('vcid','')
            if id:
                print "(vcid) = ",id
                return remove_gang(id)
        return False
    return True


#for huawei controlller , return info only when create
def xml_create_vc(body):
    '''
    <document>
        <cmd>1</cmd>
        <site_1_id>xxx</site_1_id>
        <site_2_id>yyy</site_2_id>
        <bandwidth_f>10000</bandwidth_f>
        <bandwidth_b>5000</bandwidth_b>
    </document>'''
    #Create VC
    site1_id=body['vc'].get('site1',{}).get('id','')
    site2_id=body['vc'].get('site2',{}).get('id','')
    bandwidth_f=body['vc'].get('qos',{}).get('bandwidth','')
    bandwidth_b=body['vc'].get('qos',{}).get('re_bandwidth','')
    if site1_id and site2_id and bandwidth_f and bandwidth_b:
        data = {"document":{"cmd":1,
                          "site_1_id":add_gang(site1_id),
                          "site_2_id":add_gang(site2_id),
                          "bandwidth_f":bandwidth_f,
                          "bandwidth_b":bandwidth_b}}
        return _send_xml_to_controller(default_xml_serializer, data, True)
    return False
    
#===============================================================================
# xml_update_vc_bandwidth 
#===============================================================================
def xml_update_vc_bandwidth(vc_id, body):
    #Update VC bandwidth
    '''
    <document>
        <cmd>2</cmd>
        <vc_id>xxx</vc_id>
        <bandwidth_f>100</bandwidth_f>
        <bandwidth_b>10</bandwidth_b>
    </document>'''
    bandwidth_f=body['vc'].get('qos',{}).get('bandwidth','')
    bandwidth_b=body['vc'].get('qos',{}).get('re_bandwidth','')
    if bandwidth_f and bandwidth_b:
        data = {"document":{"cmd":2,
                          "vc_id":add_gang(vc_id),
                          "bandwidth_f":bandwidth_f,
                          "bandwidth_b":bandwidth_b}}
        return _send_xml_to_controller(default_xml_serializer, data)
    return False
def xml_delete_vc(vc_id):
    #Delete VC
    '''
    <document>
        <cmd>4</cmd>
        <vc_id>xxx</vc_id>
    </document>
    '''
    data = {"document":{"cmd":4,
                      "vc_id":add_gang(vc_id)}}
    return _send_xml_to_controller(default_xml_serializer, data)
def xml_create_vn(body):
    #create L2VN

    '''<document>
        <cmd>5</cmd>
        <vn_name>xxx</vn_name>
        <site_num>xx</site_num>
        <site_list>
            <site uuid='xxxx'></site>
            <site uuid='xxxx'></site>
        </site_list>
        <link_list>
            <link>
                <site1 uuid='xxxx'/>
                <site2 uuid='xxxx'/>
                <bandwidth_f>100</bandwidth_f>
                <bandwidth_b>10</bandwidth_b>
            </link>
        </link_list>
    </document>'''
    data = {}
    print '[driver] xml_create_vn body = ',body
    sitenum = 0
    if body['vn']['layer'] == '2':
        sitelist = []
        for site in body['vn']['vnsites']:
            sitenum = sitenum + 1
            sitelist.append({'uuid':add_gang(site['id'])})
        vlinklist = []
        for vlink in body['vn']['vnlinks']:
            vlinklist.append({'site1':{'uuid':add_gang(vlink['site1']['id'])},
                              'site2':{'uuid':add_gang(vlink['site2']['id'])},
                              'bandwidth_f':vlink['qos']['bandwidth'],
                              'bandwidth_b':vlink['qos']['re_bandwidth']})
        data = {"document":{"cmd":5,
                          "vn_name":body['vn']['name'],
                          "site_num":sitenum,
                          "site_list":sitelist,
                          "link_list":vlinklist}}
    #create L3VN
    '''
    <document>
        <cmd>8</cmd>
        <vn_name>xxx</vn_name>
        <site_list>
            <site uuid='xxxx'>
                <routing_type>1</ routing_type >
                <ceasnum>6500</ceasnum>
                <pe_ip>xxx.xxx.xxx.xxx</pe_ip>
                <ce_ip>xxx.xxx.xxx.xxx</ce_ip>
            </site>
            <site uuid='xxxx'>
                <routing_type>1</ routing_type >
                <ceasnum>6500</ceasnum>
                <pe_ip>xxx.xxx.xxx.xxx</pe_ip>
                <ce_ip>xxx.xxx.xxx.xxx</ce_ip>
            </site>
        </site_list>
        <link_list>
            <link>
                <site1 uuid='xxxx'/>
                <site2 uuid='xxxx'/>
                <bandwidth_f>100</bandwidth_f>
                <bandwidth_b>10</bandwidth_b>
            </link>
        </link_list>
    </document>'''
    if  body['vn']['layer'] == '3':
        sitelist = []
        for site in body['vn']['vnsites']:
            sitenum = sitenum + 1
            sitelist.append({'uuid':add_gang(site['id']),
                             'routing_type':site['attachment']['routeprotocol']['type'],
                             'ceasnum':site['attachment']['routeprotocol']['ceasnum'],
                             "pe_ip":site['attachment']['routeprotocol']['transportippool']['peip'],
                             "ce_ip":site['attachment']['routeprotocol']['transportippool']['ceip']})
        vlinklist = []
        for vlink in body['vn']['vnlinks']:
            vlinklist.append({'site1':{'uuid':add_gang(vlink['site1']['id'])},
                              'site2':{'uuid':add_gang(vlink['site2']['id'])},
                              'bandwidth_f':vlink['qos']['bandwidth'],
                              'bandwidth_b':vlink['qos']['re_bandwidth']})
        data = {"document":{"cmd":8,
                            "vn_name":body['vn']['name'],
                            #"site_num":sitenum,
                            "site_list":sitelist,
                            "link_list":vlinklist}}
        
    metadata = {"plurals":{"site_list":"site",
                           "link_list":"link"},
                "attributes":{"site":{"uuid", },
                              "site1":{"uuid", },
                              "site2":{"uuid", }}}
    xml_serializer = wsgi.XMLDictSerializer(metadata=metadata)
    return _send_xml_to_controller(xml_serializer, data, True)
                                   
#===============================================================================
# xml_update_vlink_of_vn belons to update_vn
#===============================================================================
def xml_update_vlinkbandwidth_of_vn(vn_id,body,site1_id,site2_id):
    #maybe add vlink to vn or update vlink bandwidth of vn
    #update L2VN
    #update vlinks of L2VN
    '''
    <document>
        <cmd>11</cmd>
        <vn_id>xxx</vn_id>
        <link>
            <site1 uuid='xxxx'/>
            <site2 uuid='xxxx'/>
            <bandwidth_f>100</bandwidth_f>
            <bandwidth_b>10</bandwidth_b>
        </link>
    </document>'''
        #update vlink bandwidth from L2VN
    '''
    <document>
        <cmd>13</cmd>
        <vn_id>xxx</vn_id>
        <link>
            <site1 uuid='xxxx'/>
            <site2 uuid='xxxx'/>
            <bandwidth_f>100</bandwidth_f>
            <bandwidth_b>10</bandwidth_b>
        </link>
    <document>'''
    
    #update vlinks of L3VN
    '''
    <document>
        <cmd>11</cmd>
        <vn_id>xxx</vn_id>
        <link>
            <site1 uuid='xxxx'/>
            <site2 uuid='xxxx'/>
            <bandwidth_f>100</bandwidth_f>
            <bandwidth_b>10</bandwidth_b>
        </link>
    </document>'''
    
        #update vlink bandwidth from L3VN
    '''
    <document>
        <cmd>13</cmd>
        <vn_id>xxx</vn_id>
        <link>
            <site1 uuid='xxxx'/>
            <site2 uuid='xxxx'/>
            <bandwidth_f>100</bandwidth_f>
            <bandwidth_b>10</bandwidth_b>
        </link>
    <document>'''
    cmd = 13
    #if vlink_exist:
    #    cmd = 13
    #else:
    #    cmd = 11
    print '[driver] update_vlink_bandwidth body = ',body
    metadata = {"attributes":{"site1":{"uuid", }, "site2":{"uuid", }}}
    xml_serializer = wsgi.XMLDictSerializer(metadata=metadata)
    data = {"document":{"cmd":cmd,
                        "vn_id":add_gang(vn_id),
                        "link":{"site1":{"uuid":add_gang(site1_id)},
                                "site2":{"uuid":add_gang(site2_id)},
                                "bandwidth_f":body['vnlink']['qos']['bandwidth'],
                                "bandwidth_b":body['vnlink']['qos']['re_bandwidth']}}}
        #if cmd == 11:
        #    id = _send_xml_to_controller(xml_serializer, data, True)
        #    if id !=False:
        #        uuidlist.append(id)
        #    continue
        #=======================================================================
        # controller must add vlink item in vlink table if use cmd code 11
        #=======================================================================
    print data
    result =_send_xml_to_controller(xml_serializer, data, False)
    if result==False:
        return False
    return True

def xml_add_vlink_to_vn(vn_id ,body):
    cmd = 11
    metadata = {"attributes":{"site1":{"uuid", }, "site2":{"uuid", }}}
    xml_serializer = wsgi.XMLDictSerializer(metadata=metadata)
    data = {"document":{"cmd":cmd,
                        "vn_id":add_gang(vn_id),
                        "link":{"site1":{"uuid":add_gang(body['vnlink']['site1']['id'])},
                                "site2":{"uuid":add_gang(body['vnlink']['site2']['id'])},
                                "bandwidth_f":body['vnlink']['qos']['bandwidth'],
                                "bandwidth_b":body['vnlink']['qos']['re_bandwidth']}}}
    result =_send_xml_to_controller(xml_serializer, data, False)
    if result==False:
        return False
    return True

def xml_delete_vn(vn_id):
    #delete L2VN
    '''
    <document>
        <cmd>15</cmd>
        <vn_id>xxx</vn_id>
    </document>'''
    #delete vlink from L2VN
    '''
    <document>
        <cmd>12</cmd>
        <vn_id>xxx</vn_id>
        <link>
            <site1 uuid='xxxx'/>
            <site2 uuid='xxxx'/>
        </link>
    </document>'''
    #delete L3VN
    '''
    <document>
        <cmd>15</cmd>
        <vn_id>xxx</vn_id>
    </document>'''
    #delete vlink from L3VN
    '''
    <document>
        <cmd>12</cmd>
        <vn_id>xxx</vn_id>
        <link>
            <site1 uuid='xxxx'/>
            <site2 uuid='xxxx'/>
        </link>
    </document>'''

    metadata = {"attributes":{"site1":{"uuid", }, "site2":{"uuid", }}}
    xml_serializer = wsgi.XMLDictSerializer(metadata=metadata)
    data = {"document":{"cmd":15, "vn_id":add_gang(vn_id)}}
        
    return _send_xml_to_controller(xml_serializer, data, False)

def xml_delete_vlink_from_vn(vn_id,site1_id,site2_id):
    metadata = {"attributes":{"site1":{"uuid", }, "site2":{"uuid", }}}
    xml_serializer = wsgi.XMLDictSerializer(metadata=metadata)
    data = {"document":{"cmd":12,
                        'vn_id':add_gang(vn_id),
                        "link":{"site1":{"uuid":add_gang(site1_id)},
                                "site2":{"uuid":add_gang(site2_id)}}}}
    return _send_xml_to_controller(xml_serializer, data, False)
#===============================================================================
# xml_add_site_to_vn belongs to update_site
#===============================================================================
#===============================================================================
# def xml_add_site_to_vn(context, id, body, vpntype):
#    #update site
#    #add site to L2VN
#    '''
#    <document>
#        <cmd>6</cmd>
#        <vn_id>xxx</vn_id>
#        <site uuid='xxxx'></site>
#    </document>'''
#    #add site to L3VN
#    '''
#    <document>
#        <cmd>9</cmd>
#        <vn_id>xxx</vn_id>
#        <site uuid='xxxx'></site>
#    </document>'''
#    if getattr(context, 'vn_id'):
#        cmd = 0
#        if vpntype == 2:
#            cmd = 6
#        elif vpntype == 3:
#            cmd = 9
#        data = {"document":{"cmd":cmd, "vn_id":context.vn_id, "site":{"uuid":id}}}
#        metadata = {"attributes":{"site":{"uuid", }}}
#        xml_serializer = wsgi.XMLDictSerializer(metadata=metadata)
#        return _send_xml_to_controller(xml_serializer, data, False)
#    return False
#===============================================================================

#===============================================================================
# xml_delete_site_from_vn belongs to delete_site
#===============================================================================
#===============================================================================
# def xml_delete_site_from_vn(context, id, vpntype):
#    #delete site from L2VN
#    '''
#    <document>
#        <cmd>7</cmd>
#        <vn_id>xxx</vn_id>
#        <site uuid='xxxx'></site>
#    </document>'''
#    #delete site from L3VN
#    '''
#    <document>
#        <cmd>10</cmd>
#        <vn_id>xxx</vn_id>
#        <site uuid='xxxx'></site>
#    </document>'''
#    if getattr(context, 'vn_id'):
#        cmd = 0
#        if vpntype == 2:
#            cmd = 7
#        elif vpntype == 3:
#            cmd = 10
#        data = {"document":{"cmd":cmd, "vn_id":context.vn_id, "site":{"uuid":id}}}
#        metadata = {"attributes":{"site":{"uuid", }}}
#        xml_serializer = wsgi.XMLDictSerializer(metadata=metadata)
#        return _send_xml_to_controller(xml_serializer, data, False)
#    return False
#===============================================================================

#===============================================================================
# ceasnum should be from user.
#===============================================================================
def xml_plug_attach_for_site(site_id, body):
    '''
    <document>
        <cmd>16</cmd>
        <site uuid='xxxx'>
            <attachment>
                <routeprotocol>
                    <ceasnum>6500</ceasnum>
                    <name>xxx</name>
                    <type>x</type>
                    <transportippool>
                        <peip>xxx.xxx.xxx.xxx</peip>
                        <ceip>xxx.xxx.xxx.xxx</ceip>
                        <mask>xxx.xxx.xxx.xxx</mask>
                    </transportippool>
                </routeprotocol>
            </attachment>
        </site>
    </document>

    '''
    data = {"document":{"cmd":16,
                        "site":{"uuid":add_gang(site_id),
                                "ceasnum":body['site']['attachment']['routeprotocol']['ceasnum'],
                                'transportippool':{"peip":body['site']['attachment']['routeprotocol']['transportippool']['peip'],
                                                   "ceip":body['site']['attachment']['routeprotocol']['transportippool']['ceip'],
                                                   'mask':body['site']['attachment']['routeprotocol']['transportippool']['mask']},}}}
    metadata = {"attributes":{"site":{"uuid", }}}
    xml_serializer = wsgi.XMLDictSerializer(metadata=metadata)
    return _send_xml_to_controller(xml_serializer, data, False)

def xml_unplug_attach_for_site(site_id, body):
    '''
    <document>
        <cmd>17</cmd>
        <site uuid='xxxx'>
            <attachment>
                <routeprotocol>
                    <ceasnum>6500</ceasnum>
                    <name>xxx</name>
                    <type>x</type>
                    <transportippool>
                        <peip>xxx.xxx.xxx.xxx</peip>
                        <ceip>xxx.xxx.xxx.xxx</ceip>
                        <mask>xxx.xxx.xxx.xxx</mask>
                    </transportippool>
                </routeprotocol>
            </attachment>
        </site>
    </document>
    '''
    data = {"document":{"cmd":17,
                        "site":{"uuid":add_gang(site_id),
                                "ceasnum":body['site']['attachment']['routeprotocol']['ceasnum'],
                                'transportippool':{"peip":body['site']['attachment']['routeprotocol']['transportippool']['peip'],
                                                   "ceip":body['site']['attachment']['routeprotocol']['transportippool']['ceip'],
                                                   'mask':body['site']['attachment']['routeprotocol']['transportippool']['mask']},}}}
    metadata = {"attributes":{"site":{"uuid", }}}
    xml_serializer = wsgi.XMLDictSerializer(metadata=metadata)
    return _send_xml_to_controller(xml_serializer, data, False)




#===============================================================================
# XML exchange for Dict
#===============================================================================
def attach_xml_to_dict(xmldata):
    xml_deserializer=wsgi.XMLDeserializer()
    data=xml_deserializer(xmldata)['body']
    return data
def attach_dict_to_xml(data):
    xml_serializer=wsgi.XMLDictSerializer()
    print "[test 2012-12-05]",data
    data2={"transportippool":data}
    xmldata=xml_serializer(data2)
    print "[test 2012-12-05]",xmldata
    return xmldata
def controller_xml_to_dict(xmldata):
    metadata={'plurals':{'site_list':'site','link_list':'link'}}
    xml_deserializer=wsgi.XMLDeserializer(metadata)
    data=xml_deserializer(xmldata)['body']
    return data
def controller_dict_to_xml(data):
    '''first pattern, {"document":{"result":0|-1}}
    second pattern,   {"document":{"result":0,"vcid|vnid":'xxxx'}}'''
    xml_serializer=wsgi.XMLDictSerializer()
    xmldata=xml_serializer(data)
    return xmldata
