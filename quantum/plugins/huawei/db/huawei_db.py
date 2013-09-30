#========================================================================
#
#Core Functions Of HuaWei Quantum Plugin
#
#@author:Chang Wang
#@author:Xuejiao Lai
#=========================================================================
import datetime
import logging 
import random


from quantum.db import db_base_plugin_v2
from sqlalchemy.orm import exc as sql_exc
#from quantum.plugins.huawei.common import huawei_exceptions as hw_exc
#TODO fix this
from quantum.plugins.huawei.db import huawei_models_v2
from quantum.common import utils
from quantum.common import exceptions as q_exc
import binascii
import uuid
from quantum.wsgi import XMLDeserializer  ##xml --> json
from quantum.wsgi import XMLDictSerializer ## json --> xml
from quantum.plugins.huawei import huawei_driver
import webob.exc as w_exc

LOG = logging.getLogger(__name__)

class HuaWeiPluginDb(db_base_plugin_v2.QuantumDbPluginV2):
    """DB support for HuaWeiPlugin"""
    def __init__(self):
        pass

    #def _make_bin_for_dict(self, dict, fields):
    #    """for update and create,Change value from acsii to binary"""
    #    """fields means which key need to trans,fields is a list"""
    #    ret = {}
    #    for k, v in dict.iteritems():
    #        if k in fields:
    #            ret[k] = binascii.a2b_hex(v)
    #        else:
    #            ret[k] = v
    #    return ret
  
    def _b2a(self,id):
        return binascii.b2a_hex(id)

    def _a2b(self,id):
        return binascii.a2b_hex(id)

    def _fields(self,dic,fields):
        return dict([(k,v) for k,v in dic.iteritems() if k in fields])

    def _check_tenentid_is_right(self,context):
        session = context.session
        tenant_id_b = self._a2b(context.tenant_id)
        try:
            ret = session.query(huawei_models_v2.TenantInformation).filter(huawei_models_v2.TenantInformation.tenantid==tenant_id_b)
        except sql_exc.NoResultFound:
            raise w_exc.HTTPBadRequest(detail="The Tenantid doesn't existed in DB")
        return True

    def _check_str_id_format(self,obj): # check if the bit num and string format are right
        if isinstance(obj,basestring) and len(obj) is 32:
            return True
        else:
            return False

    def _check_int_format(self,obj): # check if the number is int
        try:
            if isinstance(obj,basestring):
                obj=int(obj)
        except:
            raise w_exc.HTTPBadRequest(detail="vlink id is wrong")
        return isinstance(obj,int) or isinstance(obj,long)

    def _check_tenantid_format(self,tenantid):
        if not self._check_str_id_format(tenantid):
            raise w_exc.HTTPBadRequest(detail='tenant id has format error')

    def _check_siteid_format(self,siteid):
        if not self._check_str_id_format(siteid):
            raise w_exc.HTTPBadRequest(detail='site id has format error')

    def _check_vnid_format(self,vnid):
        if not self._check_str_id_format(vnid):
            raise w_exc.HTTPBadRequest(detail='vn id has format error')
    
    def _check_vcid_format(self,vcid):
        if not self._check_str_id_format(vcid):
            raise w_exc.HTTPBadRequest(detail='vc id has format error')

    def _check_vlinkid_format(self,vlinkid):
        if not self._check_int_format(vlinkid):
            raise w_exc.HTTPBadRequest(detail='vlink id has format error')
           


##################################  Site Operation ################################################
	
    def get_site(self, context, site_id, fields=None,**kwargs): # show site
        #this check args is right
        #vn_id=None
        #if hasattr(context,'vn_id'):
        #    vn_id = context.vn_id
        #if vn_id:
        #    self._check_site_in_vn(context, self._a2b(site_id),self._a2b(vn_id))
        self._check_siteid_format(site_id)
        ret = self._get_site(context, self._a2b(site_id)) # get the basic information of a site
        if fields:
            ret = self._fields(ret,fields)
            #if 'attachment' in fields:
            #    attach = self._get_attachment(context, self._a2b(site_id))
            #    if attach:
            #        ret.update({'attachment':attach})
        ret.update({'tenant_id':context.tenant_id})
        return ret

    def get_sites(self,context,filters=None,fields=None,**kwargs): # list sites
        #if filters:#get sites belong to a VN         
        #    vn_id = self._a2b(filters['vn_id'][0])
        #    sitelist = self._get_vn_sites_collection(context,self._make_site_dict,vn_id)
        #    if fields:
        #        sitelist = [self._fields(s,fields) for s in sitelist]
        #    if 'attachment' in fields:
        #        for s in sitelist:
        #            attach = self._get_attachment(context, self._a2b(s['id']))
        #            if attach:
        #                s.update({'attachment':attach})
        #            print 'test***',s
        #else:#get sites belong to a tenant
        if fields==None:
            fields=[]
        fields.append('tenant_id')
        
        if fields:
            sitelist = [self._fields(s,fields) for s in self._get_sites_collection(context,self._make_site_dict)]
        else:# defualtly return all the information of sites
            sitelist = self._get_sites_collection(context,self._make_site_dict)
        #print sitelist
        return sitelist

    def _get_sites_collection(self,context,dict_fun):#get all sites' basic info as a dict list
        session = context.session
        if 'admin' not in context.roles:
            self._check_tenantid_format(context.tenant_id)
            tenant_id_b = binascii.a2b_hex(context.tenant_id)
            #collection = session.query(huawei_models_v2.TenantSites,huawei_models_v2.SiteInformation).join(huawei_models_v2.SiteInformation).filer(huawei_models_v2.TenantSites.tenantid==tenant_id_b).all()
            collection = session.query(huawei_models_v2.TenantSites,huawei_models_v2.SiteInformation).filter(huawei_models_v2.SiteInformation.siteid==huawei_models_v2.TenantSites.siteid).filter(huawei_models_v2.TenantSites.tenantid==tenant_id_b).all()
            return [dict_fun(c) for c in collection]
        else:
            collection = session.query(huawei_models_v2.SiteInformation).all()
            return [self._make_site_dict_for_admin(s,context) for s in collection]

    def _get_vn_sites_collection(self,context,dict_fun,vn_id):
        session = context.session
        sites = session.query(huawei_models_v2.TenantSites,huawei_models_v2.SiteInformation,huawei_models_v2.VnSite).filter(huawei_models_v2.TenantSites.siteid == huawei_models_v2.SiteInformation.siteid).filter(huawei_models_v2.VnSite.siteid == huawei_models_v2.SiteInformation.siteid).filter(huawei_models_v2.VnSite.vnid == vn_id).all()
        return [self._make_site_dict(s) for s in sites]

    def _make_site_dict(self,tst):
        """every tst is a (TenantSites,SiteInformation)"""
        tenantsite = tst[0]
        site = tst[1]
        ret = {'id':binascii.b2a_hex(tenantsite['siteid']),
               'description':tenantsite['desc'],
               'location':site['geoinfo'],
               'state':site['stat'],
               'sitebusy':tenantsite['sitebusy'],
               'tenant_id':self._b2a(tenantsite['tenantid'])}
        #print '[plugin 1]',ret
        return ret
    
    def _make_site_dict_for_admin(self,site,context):
        """every tst is a (TenantSites,SiteInformation)"""
        ret = {'id':binascii.b2a_hex(site['siteid']),
               'name':site['sitename'],
               'location':site['geoinfo'],
               'state':site['stat'],
               'peasnum':site['peasnum'],
               'ceasnum':site['ceasnum'],
               'peaddr':site['peaddr'],
               'peloaddr':site['peloaddr'],
               'vlanid':site['vlanid'],
               'interface':site['interface'],
               'tenant_id':context.tenant_id}
        #=======================================================================
        # use siteid to query tenantsite , if query success , then add key/value to ret. 
        #=======================================================================
        try:
            tenantsite = context.session.query(huawei_models_v2.TenantSites).filter_by(siteid=site['siteid']).one()
            ret.update({"sitebusy":tenantsite.sitebusy})
        except:
            pass
        vnname=[]
        try:
            #===================================================================
            # In VnSite , a site only exist once.
            #===================================================================
            vnsite = context.session.query(huawei_models_v2.VnSite).filter_by(siteid=site['siteid']).one()
            tenantvn = context.session.query(huawei_models_v2.TenantVn).filter_by(vnid=vnsite.vnid).one()
            vnname(tenantvn.vnname)
        except:
            pass
        ret.update({'vnname':vnname})
        vcname=[]
        try:
            vcinfo = context.session.query(huawei_models_v2.VcInformation).filter_by(site1id=site['siteid']).all()
            for vc in vcinfo:
                tenantvc = context.session.query(huawei_models_v2.TenantVc).filter_by(vcid=vc.vcid).one()
                vcname.append(tenantvc.vcname)
        except:
            pass
        try:
            vcinfo = context.session.query(huawei_models_v2.VcInformation).filter_by(site2id=site['siteid']).all()
            for vc in vcinfo:
                tenantvc = context.session.query(huawei_models_v2.TenantVc).filter_by(vcid=vc.vcid).one()
                vcname.append(tenantvc.vcname)
        except:
            pass
        ret.update({'vcname':vcname})
        print '[plugin] sites = ',ret
        return ret

    def _get_site(self, context, site_id):
        try:
            session = context.session
            if 'admin' not in context.roles:
                self._check_tenantid_format(context.tenant_id)
                site = session.query(huawei_models_v2.TenantSites,huawei_models_v2.SiteInformation).filter(huawei_models_v2.SiteInformation.siteid==huawei_models_v2.TenantSites.siteid).\
                filter(huawei_models_v2.SiteInformation.siteid==site_id).one()
                ret = self._make_site_dict(site)
            else:
                site = session.query(huawei_models_v2.SiteInformation).filter_by(siteid=site_id).one()
                ret = self._make_site_dict_for_admin(site,context)
        except sql_exc.NoResultFound:
            #raise hw_exc.SiteNotFound(site_id=self._b2a(site_id))
            raise w_exc.HTTPNotFound(detail="DEBUG-01-site id is wrong!")
        return ret		

    def _check_site_in_vn(self, context, site_id, vn_id):
        vnsite = context.session.query(huawei_models_v2.VnSite).filter_by(vnid=vn_id, siteid=site_id).all()
        if not vnsite:
            raise w_exc.HTTPNotFound(detail="DEBUG 2 check site in vn") 
    
    def create_site(self,context,body,**kwargs): #create site
        if 'admin' in context.roles:
            site=body['site']
            session=context.session
            site_id=self._a2b(str(uuid.uuid4()).replace('-',''))
            with session.begin(subtransactions=True):
                site_new=huawei_models_v2.SiteInformation(siteid=site_id,sitename=site['name'],geoinfo=site['location'],peasnum=site['peasnum'],ceasnum=site['ceasnum'],peaddr=site['peaddr'],peloaddr=site['peloaddr'],vlanid=site['vlanid'],stat=site['state'],interface=site['interface'])
                #print site_new
                session.add(site_new)
        else:
            raise w_exc.HTTPForbidden(detail='no authorization to create site')
        return {'id':self._b2a(site_id)}
        

    def update_site(self,context,site_id,body,**kwargs):

        self._check_siteid_format(site_id)
        
        if 'admin' not in context.roles:
            self._check_tenantid_format(context.tenant_id) 
            if self._check_tenentid_is_right(context):
                with context.session.begin(subtransactions=True):# modify the basic attributes of site
                    site_q=context.session.query(huawei_models_v2.TenantSites).filter_by(siteid=self._a2b(site_id)).one()
                    site_q['desc'] = body['site']['description']
        else:
            with context.session.begin(subtransactions=True):
                site_q=context.session.query(huawei_models_v2.SiteInformation).filter_by(siteid=self._a2b(site_id)).one()
                if 'name' in body['site'].keys():
                    site_q['sitename']=body['site']['name']
                if 'location' in body['site'].keys():
                    site_q['geoinfo']=body['site']['location']
            
        return None

    def delete_site(self,context,site_id,**kwargs):  # delete site from user's resource
        self._check_siteid_format(site_id)
        session = context.session
        if 'admin' not in context.roles:
            try:
                if not self._check_str_id_format(context.tenant_id):
                    raise w_exc.HTTPBadRequest(detail='tenant id has format error')

                with session.begin(subtransactions=True):
                    site = session.query(huawei_models_v2.SiteInformation).filter_by(siteid=self._a2b(site_id)).one()
                    tenantsite=session.query(huawei_models_v2.TenantSites).filter_by(siteid=self._a2b(site_id)).filter_by(tenantid=self._a2b(context.tenant_id)).one()
                    if tenantsite['sitebusy']:
                        #raise Exception('error for deleting a used site') #error for deleting a used site
                        raise w_exc.HTTPForbidden(detai="cannot delete,site is busy")
                    else:
                        session.delete(tenantsite)
                        site['stat']=0
            except:
                raise w_exc.HTTPUnauthorized(detail="cannot delete site,no auth") #error for deleting an unauthorized site
        else:
            try:
                with session.begin(subtransactions=True):
                    site = session.query(huawei_models_v2.SiteInformation).filter_by(siteid=self._a2b(site_id)).one()
                    if not site['stat']:
                        session.delete(site)
                    else:
                        raise w_exc.HTTPForbidden('this site is being used,cannot delete the resource')
            except:
                raise w_exc.HTTPNotFound('site is busy or cannot find this site')
        return None     

    def _make_tenantsite_dict(self,tenant_id,site_id,dic):
        ret = {'tenantid':self._a2b(tenant_id),
            'siteid':self._a2b(site_id),
            'desc':dic['description']}
        return ret 



########################## vnsite operation ####################
    def get_vnsite(self,context,site_id,fields=None,**kwargs): # show site # get the info of a site in a specific vn 
        vn_id=None
        if 'vn_id' in kwargs.keys():
            vn_id = kwargs['vn_id']
        else:
            raise w_exc.HTTPBadRequest(detail='no vnid no vn site')
        # check if all parameters are legal in format
        self._check_tenantid_format(context.tenand_id)
        self._check_vnid_format(vn_id)
        self._check_siteid_format(site_id)
        if vn_id:
            self._check_site_in_vn(context, self._a2b(site_id),self._a2b(vn_id))

        ret = self._get_site(context, self._a2b(site_id)) # get the basic information of a site
        if fields:
            ret = self._fields(ret,fields)
            if 'attachment' in fields:
                attach = self._get_attachment(context, self._a2b(site_id))
                if attach:
                    ret.update({'attachment':attach})
        ret.update({'tenant_id':context.tenant_id})
        return ret

    def get_vnsites(self,context,filters=None,fields=None,**kwargs): # list sites # get info of all the sites belong to a vn
        if fields==None:
            fields=[]
        fields.append('tenant_id')
        self._check_tenantid_format(context.tenant_id)
        if 'vn_id' in kwargs.keys():
            #vn_id_a = kwargs['vn_id']
            self._check_vnid_format(kwargs['vn_id'])
        else:
            raise w_exc.HTTPBadRequest(detail='no vn no site')

        #self._check_vnid_format(kwargs['vn_id_a'])
        #if filters:#get sites belong to a VN         
        vn_id = self._a2b(kwargs['vn_id'])
        sitelist = self._get_vn_sites_collection(context,self._make_site_dict,vn_id)
        if fields:
            sitelist = [self._fields(s,fields) for s in sitelist]
        if 'attachment' in fields:
            for s in sitelist:
                attach = self._get_attachment(context, self._a2b(s['id']))
                if attach:
                    s.update({'attachment':attach})
        return sitelist

    def add_site_to_vn(self,context,site_id,**kwargs): #add site to vn
        self._check_tenantid_format(context.tenant_id)
        self._check_siteid_format(site_id)
        if self._check_tenentid_is_right(context):
            if 'vn_id' in kwargs.keys():
                self._check_str_id_format(kwargs['vn_id'])
                try:
                    with context.session.begin(subtransactions=True):
                        vn = context.session.query(huawei_models_v2.VnInformation).filter_by(vnid=self._a2b(kwargs['vn_id'])).one()
                        tenantsite = context.session.query(huawei_models_v2.TenantSites).filter_by(siteid=self._a2b(site_id)).one()
                        if not tenantsite['sitebusy']: # if the site is not allocated to a vn
                            site = context.session.query(huawei_models_v2.SiteInformation).filter_by(siteid=self._a2b(site_id)).one()
                            vnsite=huawei_models_v2.VnSite(vnid=vn['vnid'],siteid=site['siteid'])
                            context.session.add(vnsite)
                            tenantsite['sitebusy']=1
                        else: # if the site is allocated to a vn, this operation is illegal
                            raise w_exc.HTTPForbidden(detail="DEBUG 3 try to add a busy site to vn") 
                    return None
                except sql_exc.NoResultFound:
                    raise w_exc.HTTPNotFound(detail="cannot add site to vn")
             

    def delete_site_from_vn(self,context,site_id,**kwargs): # delete site from vn
        self._check_tenantid_format(context.tenant_id)
        self._check_siteid_format(site_id)
        if self._check_tenentid_is_right(context):
            if 'vn_id' in kwargs.keys():
                self._check_vnid_format(kwargs['vn_id'])
                try:
                    try:
                        vlink=context.session.query(huawei_models_v2.VlinkInformation).filter_by(site1id=self._a2b(site_id)).one()
                        print "[plugin]find site in pre_vlink, count = ",vlink.count()
                        raise w_exc.HTTPForbidden(detail="The site is busy.")
                    except sql_exc.NoResultFound:
                        try:
                            vlink=context.session.query(huawei_models_v2.VlinkInformation).filter_by(site2id=self._a2b(site_id)).one()
                            print "[plugin]find site in back_vlink."
                            raise w_exc.HTTPForbidden(detail="The site is busy.")
                        except sql_exc.NoResultFound:
                            pass
                    with context.session.begin(subtransactions=True):
                        vn = context.session.query(huawei_models_v2.VnInformation).filter_by(vnid=self._a2b(kwargs['vn_id'])).one()
                        tenantsite = context.session.query(huawei_models_v2.TenantSites).filter_by(siteid=self._a2b(site_id)).one()
                        # huawei_controller.xml_delete_site_from_vn(context,site_id,vn['vpbtype'])
                        vnsite = context.session.query(huawei_models_v2.VnSite).filter_by(siteid=self._a2b(site_id)).one()
                        vn['sitecnt']=vn['sitecnt']-1
                        tenantsite['sitebusy']=0
                        context.session.delete(vnsite)
                        #vninfo = context.session.query(huawei_models_v2.VnInformation).filter_by
                        #context.session.flush()
                        #context.session.commit()
                    #raise Exception #TODO
                #except sql_exc.NoResultFound:#TODO i do not know what except in sql
                except:
                    raise w_exc.HTTPNotFound(detail="cannot del site from vn")
                return None
            else:
                raise w_exc.HTTPBadRequest(detail='DEBUG 5 no vn id') 


##########################Vlink Operation ######################
    def get_vlinks(self,context,**kwargs): # get vlinks
        if 'vn_id' in kwargs.keys():
            self._check_vnid_format(kwargs['vn_id'])
            vnid_b=self._a2b(kwargs['vn_id'])
            return self._get_vlinks(context,vnid_b)
        else:
            raise w_exc.HTTPBadRequest(detail='DEBUG 4 u must define vnid')
        
    def get_vlink(self,context,id,**kwargs): # get vlinks
        if 'vn_id' in kwargs.keys():
            self._check_vnid_format(kwargs['vn_id'])
            self._check_vlinkid_format(id)
            vnid_b=self._a2b(kwargs['vn_id'])
            session=context.session
            try:
                with session.begin(subtransactions=True):
                    vnlink=session.query(huawei_models_v2.VnLink).filter_by(vnid=vnid_b).filter_by(vlinkid=id).one()
                    vlink=session.query(huawei_models_v2.VlinkInformation).filter_by(vlinkid=id).one()
                    re_vlink=session.query(huawei_models_v2.VlinkInformation).filter_by(site1id=vlink['site2id']).filter_by(site2id=vlink['site1id']).one()
                    ret = self._make_vlink_dict(vlink, re_vlink['bandwidth'])
                    ret.update({"tenant_id":context.tenant_id})
                    return ret
            except:
                raise w_exc.HTTPNotFound(detail='cannot find vlink')
        else:
            raise w_exc.HTTPBadRequest(detail='DEBUG 4 u must define vnid')

    def update_vlink(self,context,vlink_id,body,**kwargs): # update vlink of vn
        if self._check_tenentid_is_right(context):
            self._check_tenantid_format(context.tenant_id)
            self._check_vlinkid_format(vlink_id)
            self._check_vnid_format(kwargs['vn_id'])
            #print '[plugin] update_vlink int(vlink_id) = ',int(vlink_id)
            try:
                session=context.session
                with session.begin(subtransactions=True):
                    vlink = session.query(huawei_models_v2.VlinkInformation).filter_by(vlinkid=int(vlink_id)).one()
                    huawei_driver.xml_update_vlinkbandwidth_of_vn(kwargs['vn_id'],body,self._b2a(vlink['site1id']),self._b2a(vlink['site2id']))
            except:
                raise w_exc.HTTPNotFound(detail='cannot find vlink') 
            return None

    #TODO wangchang: i do not think this is right
    def add_vlink_to_vn(self,context,body,**kwargs): # add vlink to vn
        self._check_tenantid_format(context.tenant_id)
        self._check_vnid_format(kwargs['vn_id'])
        if self._check_tenentid_is_right(context):
            huawei_driver.xml_add_vlink_to_vn(kwargs['vn_id'],body)
        return None

    def delete_vlink(self,context,vlink_id,**kwargs): # delete vlinks from vn_id
        self._check_tenantid_format(context.tenant_id)
        self._check_vlinkid_format(vlink_id)
        self._check_vnid_format(kwargs['vn_id'])

        session = context.session
        vn_id = kwargs['vn_id']
        try:
            vlink = session.query(huawei_models_v2.VlinkInformation).filter_by(vlinkid=int(vlink_id)).one()
            vnlink = session.query(huawei_models_v2.VnLink).filter_by(vlinkid=int(vlink_id)).filter_by(vnid=self._a2b(vn_id)).one()
            if huawei_driver.xml_delete_vlink_from_vn(vn_id,self._b2a(vlink['site1id']),self._b2a(vlink['site2id'])):
                #tenantsite1 = session.query(huawei_models_v2.TenantSites).filter_by(siteid=vlink['site1id']).one()
                #tenantsite2 = session.query(huawei_models_v2.TenantSites).filter_by(siteid=vlink['site2id']).one()
                #tenantsite1['sitebusy']=0
                #tenantsite2['sitebusy']=0
                pass
            else:
                raise w_exc.HTTPError()
                #session.delete(vlink)
                #session.delete(vnlink)
            return None
        except:
            raise w_exc.HTTPNotFound(detail='cannot find vlink')


    def _get_vlink(self, context, vlink_id):
        try:
            session = context.session
            vlink = session.query(huawei_models_v2.VlinkInformation).filter_by(vlinkid=int(vlink_id)).one()
        except sql_exc.NoResultFound:
            raise w_exc.HTTPNotFound(detail='cannot get vlink id is wrong')
        return self._make_vlink_dict(vlink)

    def _get_vlinks(self, context, vn_id):
        try:
            flag=[]
            session = context.session 
            vlinks = session.query(huawei_models_v2.VlinkInformation,huawei_models_v2.VnLink).filter(huawei_models_v2.VnLink.vlinkid == huawei_models_v2.VlinkInformation.vlinkid).\
                filter(huawei_models_v2.VnLink.vnid==vn_id).all()
            idlist=[l[0]['vlinkid'] for l in vlinks]
        except sql_exc.NoResultFound:
            #raise hw_exc.VlinkNotFound()
            raise w_exc.HTTPNotFound(detail="cannot find vlinks")
        vlinklist=[]
        for l in vlinks:
            if not flag.count(l[0]['vlinkid']):
                re_links=session.query(huawei_models_v2.VlinkInformation).filter(huawei_models_v2.VlinkInformation.site2id==l[0]['site1id']).filter(huawei_models_v2.VlinkInformation.site1id==l[0]['site2id']).all()
                re_vlink=[re_l for re_l in re_links if idlist.count(re_l['vlinkid'])]
                flag.append(l[0]['vlinkid'])
                flag.append(re_vlink[0]['vlinkid'])
                vlinkdict=self._make_vlink_dict(l[0],re_vlink[0]['bandwidth'])
                vlinkdict.update({"tenant_id":context.tenant_id})
                vlinklist.append(vlinkdict)

        return vlinklist

    def _make_vlink_dict(self, vlink,rebandwidth):
        ret = { 'pre_id':vlink['vlinkid'],
                'site1':{'id':binascii.b2a_hex(vlink['site1id']),'type':'source'},
                'site2':{'id':binascii.b2a_hex(vlink['site2id']),'type':'destination'},
                'qos':{'bandwidth':vlink['bandwidth'],
                       're_bandwidth':rebandwidth}}
        return ret

########################attachment operation###################

    def show_attachment_for_site(self,context,site_id,**kwargs): # show attachment for site
        self._check_siteid_format(site_id)
        site_id_b=self._a2b(site_id)
        return self._get_attachment(context,site_id_b)

    def plug_attach_for_site(self,context,site_id,body,**kwargs): # plug attachment for site
        self._check_siteid_format(site_id)
        self._check_tenantid_format(context.tenant_id)
        if self._check_tenentid_is_right(context):
            if body['site'].get('attachment') and huawei_driver.xml_plug_attach_for_site(site_id,body):
                # huawei_controller.xml_plug_attach_for_site(context,site_id,body)
                with context.session.begin(subtransactions=True):
                    attach = huawei_models_v2.SiteAttachment(siteid=self._a2b(site_id),routetype=body['site']['attachment']['routeprotocol']['type'],xmlcontent=huawei_driver.attach_dict_to_xml(body['site']['attachment']['routeprotocol']['transportippool']))
                    context.session.add(attach)
                    #context.session.flush()
                    #context.session.commit()
        return None

    def unplug_attach_for_site(self,context,site_id,body,**kwargs): # unplug attachment from site
        self._check_siteid_format(site_id)
        self._check_tenantid_format(context.tenant_id)
        if self._check_tenentid_is_right(context):
            try:
                attach = context.session.query(huawei_models_v2.SiteAttachment).filter_by(siteid=self._a2b(site_id)).one()
                if huawei_driver.xml_unplug_attach_for_site(site_id,body):
                    with context.session.begin(subtransactions=True):
                        context.session.delete(attach)
                #context.session.flush()
                #context.session.commit()
            except sql_exc.NoResultFound:
                raise w_exc.HTTPNotFound(detail='find no attach of this site')
        return None

    def _get_attachment(self, context, site_id):
        session = context.session
        try:
            attach = session.query(huawei_models_v2.SiteAttachment).filter_by(siteid=site_id).one()
            #print 'test**** attach[xmlcontent]',attach['xmlcontent']
            ret = {'routeprotocol':attach['routetype'],
                   'transportippool':huawei_driver.attach_xml_to_dict(attach['xmlcontent'])}
            return ret
        except sql_exc.NoResultFound:
            return None
########################VN operation#############################

    def get_vn(self, context, vn_id, fields=None,**kwargs): # show vn
        self._check_vnid_format(vn_id)
        self._check_tenantid_format(context.tenant_id)

        vn_id_b = binascii.a2b_hex(vn_id)
        ret = self._get_vn(context,vn_id_b,fields)
        ret.update({'tenant_id':context.tenant_id})
        return ret

    def _get_vn(self, context, vn_id, fields=None):
        try:
            session = context.session
            vn = session.query(huawei_models_v2.VnInformation,huawei_models_v2.TenantVn).filter(huawei_models_v2.TenantVn.vnid == huawei_models_v2.VnInformation.vnid).filter(huawei_models_v2.TenantVn.vnid==vn_id).one()
            ret = self._make_vn_dict(vn)
            #print fields
        except sql_exc.NoResultFound:
            raise w_exc.HTTPNotFound(detail='NO VN')
        if fields:
            #print '[plugin] get_vn fields = ',fields
            ret = self._fields(ret,fields)  #filte vn info by fields 
            if 'vnsites' in fields:  # add sites list to vn info 
                ret.update({'vnsites':self.get_vnsites(context,None,['id','location','description','attachment'],vn_id=self._b2a(vn_id))})
            if 'vnlinks' in fields:  #add vlinks list to vn info
                ret.update({'vnlinks':self._get_vlinks(context, vn_id)})
        #print ret
        return ret

    def get_vns(self, context, fields=None, filters=None,**kwargs): # list vn
        if fields==None:
            fields=[]
        fields.append('tenant_id')
        self._check_tenantid_format(context.tenant_id)
        vnlist = self._get_vns_collection(context,self._make_vn_dict)
        if fields:
            vnlist = [self._fields(v,fields) for v in vnlist]
        return vnlist

    def update_vn(self,context,vn_id,body,**kwargs): # update vn
        self._check_vnid_format(vn_id)
        self._check_tenantid_format(context.tenant_id)

        if self._check_tenentid_is_right(context):
            if body['vn'].get('name'):
                with context.session.begin(subtransactions=True):
                    vn = context.session.query(huawei_models_v2.TenantVn).filter_by(vnid=self._a2b(vn_id)).one()
                    vn['vnname']=body['vn']['name']
                    #context.session.flush()
                    #context.session.commit()
        return None

    def _check_l3_vn_body(self,context,body):
        for vnsite in body['vn']['vnsites']:
            self._check_sitebusy(context,vnsite['id'])

    def _check_sitebusy(self,context,site_id):
        self._check_siteid_format(site_id)
        try:
            with context.session.begin(subtransactions=True):
                vnsite_q=context.session.query(huawei_models_v2.TenantSites).filter_by(siteid=self._a2b(site_id)).one()
                if vnsite_q['sitebusy']:
                    raise w_exc.HTTPBadRequest('site has been used in a vn or vc, create error')
        except:
            raise w_exc.HTTPBadRequest('cannot find site')
        
    def create_vn(self,context,body,**kwargs): # create vn
        self._check_tenantid_format(context.tenant_id)
        self._check_l3_vn_body(context,body)
        if self._check_tenentid_is_right(context):
            # add ceasnum
            vn_id = huawei_driver.xml_create_vn(body)
            if vn_id:
                #try:
                vn_id_n = vn_id.replace("-","")
                with context.session.begin(subtransactions=True):
                    vn = huawei_models_v2.TenantVn(tenantid=self._a2b(context.tenant_id),vnid=self._a2b(vn_id_n),vnname=body['vn']['name'])       
                    context.session.add(vn)
                    sites=context.session.query(huawei_models_v2.VnSite).filter_by(vnid=self._a2b(vn_id_n)).all()
                    for site in sites:
                        tenantsite=context.session.query(huawei_models_v2.TenantSites).filter_by(siteid=site['siteid']).one()
                        tenantsite['sitebusy']=1
                    if body['vn']['layer']=='3':
                        for site in body['vn']['vnsites']:
                            siteid=site['id']
                            sitebody={"site":{"attachment":site['attachment']}}
                            self.plug_attach_for_site(context,siteid,sitebody)
                #except:
                    #raise w_exc.HTTPError(detail='create vn failed')
                #session.flush()
                    #context.session.commit()
            #return {'vn':{'id':vn_id}}
                #print '******This is db create_vn',vn_id_n
                return {'id':vn_id_n}
            else:
                raise w_exc.HTTPError(detail='create vn failed')
        else:
            raise w_exc.HTTPError(detail="Tenant id is wrong")

    def delete_vn(self,context,vn_id,**kwargs): #delete vn
        self._check_vnid_format(vn_id)
        self._check_tenantid_format(context.tenant_id)
        allsites=[]
        if self._check_tenentid_is_right(context):
            try:
                #context.session.begin(subtransactions=True)
                #vn = context.session.query(huawei_models_v2.TenantVn).filter_by(vnid=self._a2b(vn_id)).one()
                vnsites=context.session.query(huawei_models_v2.VnSite).filter_by(vnid=self._a2b(vn_id)).all()
                for vnsite in vnsites:
                    allsites.append(vnsite['siteid'])
                try:
                    vnlinks=context.session.query(huawei_models_v2.VnLink).filter_by(vnid=self._a2b(vn_id)).all()
                except:
                    pass
                vnlinkid = []
                for vnlink in vnlinks:
                    vnlinkid.append(vnlink['vlinkid'])
                for linkid in vnlinkid:
                    #print '[plugin] vlinkid = ',vnlink['vlinkid']
                    try:
                        self.delete_vlink(context,linkid,vn_id=vn_id)
                    except:
                        pass
                #context.session.rollback()
                    #for vnsite in vnsites:
                    #    self.delete_site_from_vn(context,self._b2a(vnsite['siteid']),vn_id=vn_id)
                    #vn = context.session.query(huawei_models_v2.TenantVn).filter_by(vnid=self._a2b(vn_id)).one()
                    #else:
                        #raise w_exc.HTTPError(detail="Controller delete vn failed")
                        # with context.session.begin(subtransactions=True):
                        #if hasattr(context,'site1_id') and hasattr(context,'site2_id'):
                            #return None
                        #else:
                            #context.session.delete(vn)
                            #context.session.flush()
                            #context.session.commit()
                    #else:
                        #raise Exception
            except sql_exc.NoResultFound:
                raise w_exc.HTTPNotFound(detail="delete vn not found.")
            if huawei_driver.xml_delete_vn(vn_id):
                context.session.begin(subtransactions=True)
                try:
                    vn = context.session.query(huawei_models_v2.TenantVn).filter_by(vnid=self._a2b(vn_id)).one()
                    context.session.delete(vn)
                except:
                    pass
                context.session.rollback()
            else:
                raise w_exc.HTTPError(detail="Controller delete vn failed")
            try:
                for site in allsites:
                    if site:
                        with context.session.begin(subtransactions=True):
                            tenantsite = context.session.query(huawei_models_v2.TenantSites).filter_by(siteid=site).one()
                            tenantsite['sitebusy']=0
            except:
                raise w_exc.HTTPError(detail='change sitebusy failed.')
        return None

    def _make_tenantvn_dict(self,tenant_id,vn_id,dic):
        ret = {'tenantid':self._a2b(tenant_id),
              'vnid':self._a2b(vn_id),
              'vnname':dic['name']}
        return ret
            

    def _get_vns_collection(self,context,dict_fun):
        session = context.session
        tenant_id_b = self._a2b(context.tenant_id)
        vns = session.query(huawei_models_v2.VnInformation,huawei_models_v2.TenantVn).filter(huawei_models_v2.TenantVn.vnid ==huawei_models_v2.VnInformation.vnid).filter(huawei_models_v2.TenantVn.tenantid==tenant_id_b).all()
        return [dict_fun(v) for v in vns]

    def _make_vn_dict(self,tst):
        """every tst is a (VnInformation,TenantVn)"""
        vn = tst[0]
        tenantvn = tst[1]
        vn_dict = {'id':self._b2a(tenantvn['vnid']),
                   'name':tenantvn['vnname'],
                   'layer':vn['vpntype'],
                   'tenant_id':self._b2a(tenantvn['tenantid'])}
        return vn_dict				   
######################

    def _get_vc_bw(self,context,vlinkid):
        session = context.session
        try:
            vlink = session.query(huawei_models_v2.VlinkInformation).filter(huawei_models_v2.VlinkInformation.vlinkid==vlinkid).one()
        except sql_exc.NoResultFound:
            raise w_exc.HTTPNotFound(detail='no bw')
        ret = vlink['bandwidth']
        return ret

    def get_vc(self, context, vc_id, fields,**kwargs):
        self._check_tenantid_format(context.tenant_id)
        self._check_vcid_format(vc_id)
        [vcinfo, tenantvc] = self._get_vc(context, vc_id)
        vc = self._make_vc_base_dict(vcinfo, tenantvc)
        '''vc_base is a dict.need add site info'''
        if 'site1' in fields:
            site1_id_b = vcinfo['site1id']
            vc.update({'site1':self._get_vc_site(context,site1_id_b)})
        if 'site2' in fields:
            site2_id_b = vcinfo['site2id']
            vc.update({'site2':self._get_vc_site(context,site2_id_b)})
        if 'qos' in fields:
            vlinkid_b = vcinfo['vlinkid']
            back_vlinkid_b = vcinfo['back_vlinkid']
            vc.update({'qos':{'bandwidth':self._get_vc_bw(context,vlinkid_b),
              're_bandwidth':self._get_vc_bw(context,back_vlinkid_b)}})
        vc.update({'tenant_id':context.tenant_id})
        return vc

    def _get_vc_site(self,context,siteid):
        self.site_id = siteid
        session = context.session
        siteinfo = session.query(huawei_models_v2.SiteInformation).filter(huawei_models_v2.SiteInformation.siteid==self.site_id).one()
        tenant_site = session.query(huawei_models_v2.TenantSites).filter(huawei_models_v2.TenantSites.siteid==self.site_id).one()
        ret = {'id':self._b2a(siteinfo['siteid']),
              'location':siteinfo['geoinfo'],
              'description':tenant_site['desc']}
        return ret
        

                
      
    def get_vcs(self, context, filters=None, fields=None,**kwargs):
        if fields==None:
            fields=[]
        fields.append('tenant_id')
        self._check_tenantid_format(context.tenant_id)
        return self._get_vcs_collection(context, self._make_vcs_dict, filters=filters, fields=fields)

    def update_vc(self, context, vc_id, vc,**kwargs):
        ''''''
        self._check_tenantid_format(context.tenant_id)
        self._check_vcid_format(vc_id)

        n = self._check_tenentid_is_right(context)
        vc_id_b = self._a2b(vc_id)
        if n:
            #===================================================================
            # #vc_data = self._make_bin_for_dict(vc['vc'], ['vcid', 'site1id', 'site2id'])     
            # if vc['vc'].has_key('name') and vc['vc']['qos'].has_key('bandwidth'):
            #    ret = huawei_driver.xml_update_vc_bandwidth(context,vc_id,vc)
            #    if ret: 
            #        with context.session.begin(subtransactions=True): 
            #            session = context.session
            #            tenantvc = session.query(huawei_models_v2.TenantVc).filter(huawei_models_v2.TenantVc.vcid == vc_id_b).one()
            #            tenantvc['vcname'] = vc['vc']['name']
            #        #session.flush()
            #        #session.commit()
            #            return None
            #===================================================================
            if vc['vc'].has_key('name'):
                try:
                    with context.session.begin(subtransactions=True): 
                        session = context.session
                        tenantvc = session.query(huawei_models_v2.TenantVc).filter(huawei_models_v2.TenantVc.vcid==vc_id_b).one()
                        tenantvc['vcname'] = vc['vc']['name']
                #session.flush()
                except:
                    raise w_exc.HTTPError(detail='update vc name failed')
            if 'qos' in vc['vc'] and vc['vc']['qos'].has_key('bandwidth'):
                ret = huawei_driver.xml_update_vc_bandwidth(vc_id,vc)
                if ret:
                    return None
                else:
                    raise w_exc.HTTPError(detail='internal controller error')
                    #raise error
        #print 'update_vc:tenantid not right'
        raise w_exc.HTTPError(detail='tenantid  error')

    def create_vc(self, context, vc,**kwargs):
        self._check_tenantid_format(context.tenant_id)
        if self._check_tenentid_is_right(context,):
            site1_id=vc['vc']['site1']['id']
            site2_id=vc['vc']['site2']['id']
            self._check_sitebusy(context,site1_id)
            self._check_sitebusy(context,site2_id)
            name = vc['vc']['name']
            id=huawei_driver.xml_create_vc(vc)
            if not id:
                #print '==create vc failed'
                raise w_exc.HTTPError(detail='Create VC failed:error in controller')
            else: 
                id_pure = id.replace("-","")#wachang:in db,uuid has no -
                with context.session.begin(subtransactions=True):
                    #session = context.session
                    #id_pure = id.replace("-","")#wachang:in db,uuid has no -
                    tenantvc = huawei_models_v2.TenantVc(vcid = self._a2b(id_pure),tenantid=self._a2b(context.tenant_id),vcname=name)
                    context.session.add(tenantvc)
                    #context.session.commit()
                    tenantsite1=context.session.query(huawei_models_v2.TenantSites).filter_by(siteid=self._a2b(site1_id)).one()
                    tenantsite2=context.session.query(huawei_models_v2.TenantSites).filter_by(siteid=self._a2b(site2_id)).one()
                    tenantsite1['sitebusy']=1
                    tenantsite2['sitebusy']=1
                    #tenantvc = huawei_models_v2.TenantVc(vcid = self._a2b(id_pure),tenantid=self._a2b(context.tenant_id),vcname=name)
                    #context.session.add(tenantvc)
                    #context.session.commit()
                    #print 'create_vc success'
                return {'id':id_pure}   #wachang
        #print 'create_vc:tenantid not right'
        raise w_exc.HTTPBadRequest(detail="Tenant id is wrong")
        
    def delete_vc(self, context, vc_id,**kwargs):
        self._check_tenantid_format(context.tenant_id)
        self._check_vcid_format(vc_id)

        if self._check_tenentid_is_right(context):
            with context.session.begin(subtransactions=True):
                vcinfo = context.session.query(huawei_models_v2.VcInformation).filter_by(vcid=self._a2b(vc_id)).one()
                site1id=vcinfo.site1id
                site2id=vcinfo.site2id
                ret=huawei_driver.xml_delete_vc(vc_id)
                if ret:
                    with context.session.begin(subtransactions=True):
                        #vcinfo = context.session.query(huawei_models_v2.TenantVc).filter_by(vcid=self._a2b(vc_id)).one()
                        tenantsite1=context.session.query(huawei_models_v2.TenantSites).filter_by(siteid=site1id).one()
                        tenantsite2=context.session.query(huawei_models_v2.TenantSites).filter_by(siteid=site2id).one()
                        tenantsite1['sitebusy']=0
                        tenantsite2['sitebusy']=0
                    return None
                else:
                    raise w_exc.HTTPError(detail="delete vc failed.")

    def _get_vc(self, context, vc_id):
        try:
            session = context.session
            vc_id_b = binascii.a2b_hex(vc_id)
            with session.begin(subtransactions=True):
                vc = session.query(huawei_models_v2.VcInformation).filter_by(vcid=vc_id_b).one()
                tenantvc = session.query(huawei_models_v2.TenantVc).filter_by(vcid=vc_id_b).one()
                return [vc, tenantvc]
        except sql_exc.NoResultFound:
            raise w_exc.HTTPNotFound(detail='No vc found')
            

    def _get_vcs_collection(self, context, dict_fun, filters=None, fields=None):
        if context.tenant_id is not None:
            tenant_id_b = binascii.a2b_hex(context.tenant_id)
            session = context.session
            collection = session.query(huawei_models_v2.TenantVc, huawei_models_v2.VcInformation).join(huawei_models_v2.VcInformation).filter(huawei_models_v2.TenantVc.tenantid == tenant_id_b).all()
        return [dict_fun(c, fields) for c in collection]

    def _make_vcs_dict(self, tvc, fields):
        """every tvc is a tuple"""
        tenantvc = tvc[0]
        vcinfo = tvc[1]
        ret = {'id':binascii.b2a_hex(vcinfo['vcid']),
            'name':tenantvc['vcname'],
            'site1id':binascii.b2a_hex(vcinfo['site1id']),
            'site2id':binascii.b2a_hex(vcinfo['site2id']),
            'vlinkid':vcinfo['vlinkid'],
            'back_vlinkid':vcinfo['back_vlinkid'],
            'pwid':vcinfo['pwid'],
            'tenant_id':self._b2a(tenantvc['tenantid'])
            }
        return ret

    def _make_vc_base_dict(self, vc, tenantvc):
        if tenantvc is not None:
            ret = {'name':tenantvc['vcname'],
                'id':binascii.b2a_hex(vc['vcid'])}
        elif tenantvc is None:
            #this shoud never be used
            ret = {'id':binascii.b2a_hex(vc['vcid']),
                'site1id':binascii.b2a_hex(vc['site1id']),
                'site2id':binascii.b2a_hex(vc['site2id']),
                'vlinkid':vc['vlinkid'],
                'pwid':vc['pwid']}
        return ret


######################Tenant Operation###############################
    # def get_user(self,context,user_id,fields=None): # get a user's info via user_id

    def get_users(self,context,filters=None,fields=None,**kwargs): # list Users
        try:
            if fields==None:
                fields=[]
            fields.append('tenant_id')
            session = context.session
            users = session.query(huawei_models_v2.TenantInformation).all()
            userlist=[]
            for user in users:
                userlist.append(self._fields(self._make_user_dict(user),fields))
            return userlist
        except:
            raise w_exc.HTTPNotFound(detail='no user found')
        
    def get_user(self,context,user_id,fields=None,**kwargs): # list Users
        self._check_tenantid_format(user_id)
        try:
            if fields==None:
                fields=[]
            fields.append('tenant_id')
            session = context.session
            user = session.query(huawei_models_v2.TenantInformation).filter_by(tenantid=self._a2b(user_id)).one()
            ret=self._fields(self._make_user_dict(user),fields)
            try:
                collection = session.query(huawei_models_v2.TenantSites,huawei_models_v2.SiteInformation).filter(huawei_models_v2.SiteInformation.siteid==huawei_models_v2.TenantSites.siteid).filter(huawei_models_v2.TenantSites.tenantid==self._a2b(user_id)).all()
            except:
                return ret
            usersites=[self._make_site_dict(c) for c in collection]
            ret.update({'usersites':usersites})
            return ret
        except:
            raise w_exc.HTTPNotFound(detail='no usr found')
        
    def create_user(self,context,body,**kwargs): # create user
        session = context.session
        user = session.query(huawei_models_v2.TenantInformation).filter_by(username=body['user']['name'])
        if user.count():
            raise w_exc.HTTPForbidden(detail="User has been existed.")
        else:
            with session.begin(subtransactions=True):
                userid=self._a2b(str(uuid.uuid4()).replace('-',''))
                new_user=huawei_models_v2.TenantInformation(tenantid=userid,username=body['user']['name'],pwd=body['user']['passwd'],company=body['user']['company'])
                session.add(new_user)
                return {'id':self._b2a(userid)}

    def update_user(self,context,user_id,body,**kwargs): # wangchang update user's password / user use this function?
        self._check_tenantid_format(user_id)
        if self._check_tenentid_is_right(context):
            try:
                with context.session.begin(subtransactions=True):
                    session = context.session
                    tenant = session.query(huawei_models_v2.TenantInformation).filter_by(tenantid=self._a2b(user_id)).one()
                    tenant['pwd']=body['user']['passwd']
                #session.commit()
            except sql_exc.NoResultFound:
                raise w_exc.HTTPNotFound(detail='DEBUG 9 No user found!')
        else:
            raise w_exc.HTTPBadRequest(detail='tenant id is wrong!') #TODO this user cannot be found
        

    def delete_user(self,context,user_id,**kwargs): # delete a user
        self._check_tenantid_format(user_id)
        print '[delete_user]'
        try:
            with context.session.begin(subtransactions=True):
                usersites=context.session.query(huawei_models_v2.TenantSites).filter_by(tenantid=self._a2b(user_id)).all()
                raise w_exc.HTTPError(detail="cannot delete user for available sites.")
        except Exception,e:
            with context.session.begin(subtransactions=True):
                user=context.session.query(huawei_models_v2.TenantInformation).filter_by(tenantid=self._a2b(user_id)).one()
                context.session.delete(user)
                return None

    def _make_user_dict(self,user): # make a user's dict via database
        ret = {'tenant_id':self._b2a(user['tenantid']),
              'name':user['username'],
              'passwd':user['pwd'],
              'company':user['company'],
              'id':self._b2a(user['tenantid'])}
        return ret


##################### Admin Operation #################################
    def add_site_to_tenant(self,context,tenant_id,body,**kwargs): # add site to user
    #site: site['tenantid'],site['siteid'],site['desc']
        self._check_tenantid_format(tenant_id)
        self._check_siteid_format(body['user']['siteid'])
        session = context.session
        site_check = session.query(huawei_models_v2.SiteInformation).filter_by(siteid=self._a2b(body['user']['siteid'])).one()
        if not site_check['stat']:
            with session.begin(subtransactions=True):
                tenantsite = huawei_models_v2.TenantSites(siteid=self._a2b(body['user']['siteid']),tenantid=self._a2b(tenant_id),desc=None,sitebusy=0)
                session.add(tenantsite)
                site_check['stat']=1
        else:
            raise w_exc.HTTPForbidden(detail='this site has been allocated to some user') #TODO this site has been allocated to some user
        return None

    def release_site_from_tenant(self,context,tenant_id,body,**kwargs): # delete site from user
        self._check_tenantid_format(tenant_id)
        self._check_siteid_format(body['user']['siteid'])

        session = context.session
        try:
            with session.begin(subtransactions=True):
                site = session.query(huawei_models_v2.SiteInformation).filter_by(siteid=self._a2b(body['user']['siteid'])).one()
                tenantsite=session.query(huawei_models_v2.TenantSites).filter_by(siteid=self._a2b(body['user']['siteid'])).filter_by(tenantid=self._a2b(tenant_id)).one()
                if tenantsite['sitebusy'] ==1 :
                    raise w_exc.HTTPError(detail="site is busy")
                session.delete(tenantsite)
                site['stat']=0
        except:
            raise w_exc.HTTPNotFound(detail="can't find this site in tenant or site busy")
        return None
        #return True
            

