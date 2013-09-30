import socket
from quantum import wsgi
from quantum.plugins.huawei import huawei_driver
from quantum.plugins.huawei.db import huawei_models_v2 as hw
from sqlalchemy import *
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import binascii
from uuid import uuid4
from random import randint as rd
from sqlalchemy.orm import exc as sql_exc

Base = declarative_base()
engine = create_engine('mysql://huawei_quantum:openstack@localhost:3306/huawei_quantum',echo=True)
Session = sessionmaker(bind=engine)

#session = Session()


def a2b(string):
    return binascii.a2b_hex(string)
  
def b2a(binary):
    return binascii.b2a_hex(binary)

def get_max_id(table):
    if table == 'vlink':
        session = Session()
        vlinkids = session.query(hw.VlinkInformation.vlinkid).all()
        max_id = 0
        for vlinkid in vlinkids:
            if vlinkid[0] > max_id:
                max_id = vlinkid[0]
        return max_id
    if table == 'vcinfo':
        pass

def create_vlink(s1id,s2id,band):
    current_max_vlink_id = get_max_id('vlink')
    tunnelid_r = rd(10,20)
    vlink = hw.VlinkInformation(vlinkid = current_max_vlink_id+1,site1id=s1id,site2id=s2id,\
        tunnelid = tunnelid_r,bandwidth=band)
    session = Session()
    session.add(vlink)
    session.commit()
    return current_max_vlink_id+1
    
def create_vc(vc):
    '''vc id a dict refered to huawei_driver.py
       {'document':{'cmd':1,'site_1_id':xx,
                    'site_2_id':xxx,'bandwidth_f':xxx,
                    'bandwidth_b':xxx}}
    '''
    #site must in table siteinfo
    site_1_id = vc['document']['site_1_id']
    site_2_id = vc['document']['site_2_id']
    pwid_r = rd(50,100) #for test
    #first deal with create vlink
    vlinkid_f = create_vlink(a2b(site_1_id),a2b(site_2_id),vc['document']['bandwidth_f'])
    vlinkid_b = create_vlink(a2b(site_2_id),a2b(site_1_id),vc['document']['bandwidth_b'])

    #then deal with vcinfo
    vcid = uuid4().get_hex() #this is ascii
    try:
        vc = hw.VcInformation(vcid = a2b(vcid),site1id=a2b(site_1_id),site2id=a2b(site_2_id),vlinkid=vlinkid_f,\
           back_vlinkid=vlinkid_b,pwid=pwid_r)
        session = Session()
        session.add(vc)
        #session.flush()
        session.commit()
    except:
        pass
    return {"document":{"result":0,"vcid":vcid}}

def update_vc(data):
    '''actually,i just deal update bandwidth
       return True or False
       {'vc':{'vcid':,'bandwidth_f':,'bandwidth_b':}}
       vcid->siteid->vlink->bandwidth
    '''
    vcid_b = a2b(data['document']['vc_id'])
    session = Session()
    vc = session.query(hw.VcInformation).filter(hw.VcInformation.vcid==vcid_b).one()
    site1id_b = vc['site1id']
    site2id_b = vc['site2id']

    #find front vlink and back vlink and update_vc
    #defaule site1->site2:front vlink 
    if data['document']['bandwidth_f']:#TODO
        vlink_f = session.query(hw.VlinkInformation).filter(hw.VlinkInformation.site1id==site1id_b).filter(hw.VlinkInformation.site2id==site2id_b).one()
        vlink_f.update({'bandwidth':data['document']['bandwidth_f']})
    if data['document']['bandwidth_b']:
        vlink_b = session.query(hw.VlinkInformation).filter(hw.VlinkInformation.site1id==site2id_b).filter(hw.VlinkInformation.site2id==site1id_b).one()
        vlink_b.update({'bandwidth':data['document']['bandwidth_f']})
    session.commit()

    return {"document":{'result':0}}


def delete_vc(data):
    '''just do vcinfo 
       {'document':{'vcid':xxx}}
    '''
    session = Session()
    vcid_b = a2b(data['document']['vc_id'])
    vc = session.query(hw.VcInformation).filter(hw.VcInformation.vcid==vcid_b).one()
    session.delete(vc)
    session.commit() 
    return {"document":{'result':0}}

def create_vn(data,layer):
    session = Session()
    vn_id = uuid4().get_hex()
    vnid_b = a2b(vn_id)
    #add item to vninfo table
    vn = hw.VnInformation(vnid=vnid_b,sitecnt=data['document']['site_num'],vpntype=layer)
    session.add(vn)
    session.commit()
    # add sites to vn
    
    for site in data['document']['site_list']:
        add_site_to_vn(site,vnid_b)
        
    # add vlinks to vn
    session = Session()
    for vlink in data['document']['link_list']:
        v1id=create_vlink(s1id=a2b(vlink['site1']['uuid']) , s2id=a2b(vlink['site2']['uuid']) , band=vlink['bandwidth_f'])
        v2id=create_vlink(s1id=a2b(vlink['site2']['uuid']) , s2id=a2b(vlink['site1']['uuid']) , band=vlink['bandwidth_b'])
        session.add(hw.VnLink(vnid=vnid_b,vlinkid=v1id))
        session.add(hw.VnLink(vnid=vnid_b,vlinkid=v2id))
    session.flush()
    session.commit()
    return {"document":{"result":0,"vnid":vn_id}}

def delete_vn(data):
    session=Session()
    vnid_b=a2b(data['document']['vn_id'])
    #===========================================================================
    # # delete vlinks from Vn
    vlinks=session.query(hw.VnLink).filter(hw.VnLink.vnid == vnid_b).all()
    for vlink in vlinks:
        vlink_id=vlink['vlinkid']
        vl = session.query(hw.VlinkInformation).filter(hw.VlinkInformation.vlinkid==vlink_id).one()
        session.delete(vl)
        session.commit()
    # #delete site from Vn
    session=Session()
    vnsites=session.query(hw.VnSite).filter(hw.VnSite.vnid==vnid_b).all()
    for site in vnsites:
        session.delete(site)
        session.commit()
    #===========================================================================
    #delete vn 
    session=Session()
    vn=session.query(hw.VnInformation).filter(hw.VnInformation.vnid==vnid_b).one()
    session.delete(vn)
    #session.flush()
    session.commit()
    return {"document":{'result':0}}

def update_vlink_of_vn(data):
    try:#add new vlink or update existed vlink
        session = Session()
        site1id_b=a2b(data['document']['link']['site1']['uuid'])
        site2id_b=a2b(data['document']['link']['site2']['uuid'])
        if data['document']['cmd']=='13':
            vlink1 = session.query(hw.VlinkInformation).filter(hw.VlinkInformation.site1id==site1id_b).filter(hw.VlinkInformation.site2id==site2id_b).one()
            vlink2 = session.query(hw.VlinkInformation).filter(hw.VlinkInformation.site2id==site1id_b).filter(hw.VlinkInformation.site1id==site2id_b).one()
            vlink1.update({'bandwidth':data['document']['link']['bandwidth_f']})
            vlink2.update({'bandwidth':data['document']['link']['bandwidth_b']})
        elif data['document']['cmd']=='11':
            v1id = create_vlink(site1id_b,site2id_b,data['document']['link']['bandwidth_f'])
            v2id = create_vlink(site2id_b,site1id_b,data['document']['link']['bandwidth_b'])
            session.add(hw.VnLink(vnid=a2b(data['document']['vn_id']),vlinkid=v1id))
            session.add(hw.VnLink(vnid=a2b(data['document']['vn_id']),vlinkid=v2id))
        session.flush()
        session.commit()
        return {"document":{'result':0}}
    except:
        return {"document":{'result':-1}}

def delete_vlink_from_vn(data):
    try:
        session = Session()
        site1id_b=a2b(data['document']['link']['site1']['uuid'])
        site2id_b=a2b(data['document']['link']['site2']['uuid'])
        vlink1 = session.query(hw.VlinkInformation).filter(hw.VlinkInformation.site1id==site1id_b).filter(hw.VlinkInformation.site2id==site2id_b).one()
        vlink2 = session.query(hw.VlinkInformation).filter(hw.VlinkInformation.site2id==site1id_b).filter(hw.VlinkInformation.site1id==site2id_b).one()
        vnlink1=session.query(hw.VnLink).filter(hw.VnLink.vlinkid==vlink1['vlinkid']).one()
        vnlink2=session.query(hw.VnLink).filter(hw.VnLink.vlinkid==vlink2['vlinkid']).one()
        session.delete(vlink1)
        session.delete(vlink2)
        #session.delete(vnlink1)
        #session.delete(vnlink2)
        session.commit()
        return {"document":{'result':0}}
    except sql_exc.NoResultFound:
        return {"document":{"result":"-1"}}

def add_site_to_vn(site,vnid_b):
    session=Session()
    siteid_b=a2b(site['uuid'])
    vnsite = hw.VnSite(siteid=siteid_b,vnid=vnid_b)
    if site.get('routing_type'):
        cepe={'ceip':site['ce_ip'], 'peip':site['pe_ip']}
        xmlip = wsgi.XMLDictSerializer()(cepe)
        attach = hw.SiteAttachment(siteid=siteid_b,routetype=site['routing_type'],xmlcontent=xmlip)
        session.add(attach)
    session.add(vnsite)
    session.flush()
    session.commit()
    return True

def plug_attach_for_site(id):
    return {"document":{"result":"0"}}

def unplug_attach_for_site(id):
    return {"document":{"result":"0"}}

def main():
    print "server run."
    host = "localhost"
    port = 9123
    addr=(host,port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(addr)
    sock.listen(128)
    while True:
        connection,address = sock.accept()
        xmldata = connection.recv(10240)
        print xmldata
        data=huawei_driver.controller_xml_to_dict(xmldata)
        print data
        re=''
        #=======================================================================
        # Use controller_dict_to_xml to convert dict to xml.
        #=======================================================================
        #try:
        if data['document']['cmd']=='1':
            re=create_vc(data)
        elif data['document']['cmd']=='2':
            re=update_vc(data)
        elif data['document']['cmd']=='4':
            re=delete_vc(data)
        elif data['document']['cmd']=='5':
            re=create_vn(data,2)
        elif data['document']['cmd']=='8':
            re=create_vn(data,3)
        elif data['document']['cmd']=='11' or data['document']['cmd']=='13':
            print 'cmd = ',data['document']['cmd']
            re=update_vlink_of_vn(data)
        elif data['document']['cmd']=='15':
            re=delete_vn(data)
        elif data['document']['cmd']=='12':
            re=delete_vlink_from_vn(data)
        elif data['document']['cmd']=='16':
            re=plug_attach_for_site(data)
        elif data['document']['cmd']=='17':
            re=unplug_attach_for_site(data)
        print '[return]xmldata = ',re
        xmldata=huawei_driver.controller_dict_to_xml(re)
        print '[return]xmldata = ',xmldata
        connection.send(xmldata)
        connection.close()
        #except:
        #    re={"document":{"result":'-1'}}
        #    xmldata=huawei_driver.controller_dict_to_xml(re)
        #    connection.send(xmldata)
        #    connection.close()
        
if __name__ == "__main__":
    main()
