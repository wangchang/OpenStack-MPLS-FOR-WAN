import logging
import os
import sys
import json
import webob.exc
import fcntl

from quantum import policy
from quantum.api.v2 import attributes
from quantum.extensions import providernet as provider #TODO
from quantum.common import constants as q_const
from quantum.common import exceptions as q_exc
from quantum.common import topics
from quantum.openstack.common import context
from quantum.openstack.common import cfg
from quantum.openstack.common import rpc
from quantum.openstack.common.rpc import dispatcher
from quantum.openstack.common.rpc import proxy

from quantum.plugins.huawei.common import huawei_constants as hw_cons
from quantum.plugins.huawei.common import config
from quantum.plugins.huawei.db import huawei_db
from quantum.plugins.huawei.common import huawei_exceptions as hw_exc
from quantum.plugins.huawei.db import huawei_db_base
from quantum.plugins.huawei.db import huawei_models_v2

from quantum.api.v2.attributes import convert_to_boolean
from quantum import policy
from quantum.common import exceptions

class HuaWeiQuantumPlugin(huawei_db.HuaWeiPluginDb):
    _native_bulk_support = True
    supported_extension_aliases = ["provider", "router", "huawei"]
        
    def __init__(self):
        "create the db now no need"
        print "plugin create database tables."
        huawei_db_base.initialize()
        #self.tenant_network_type = cfg.CONF.huawei.tenant_network_type
        #if self.tenant_network_type not in [constants.TYPE_VPN]:
        #  LOG.error("error")
        
        #self.setup_rpc()

    #def setup_rpc():
        #self.topic = topics.PLUGIN
        #self.rpc_context = context.RequestContext('quantum','quantum',is_admin=False)
        #self.conn = rpc.create_connection(new=True)
        #self.notifier = DrivernotifierApi(topics.DRIVER) #TODO
        #self.callbacks = HuaWeiRpcCallbacks(self,rpc_context,self.notifier)#TODO
        #self.dispatcher = self.callbacks.create_rpc_dispatcher()
        #self.conn.create_consumer(self.topic,self.dispatcher,fanout=False)
        #self.conn.comsume_in_thread()


    def _fields(self, resource, fields):
        if fields:
            return dict(((key, item) for key, item in resource.iteritems() if key in fields))
        return resource
    def _check_huawei_update(self, context, dict):
        pass
########################Virtual Connection##################
    def get_vc(self, context, id, fields=None,**kwargs):
        #return {"name":"zuocheng"}
        if fields==None:
            fields=[]
        fields.append('tenant_id')
        vc = super(HuaWeiQuantumPlugin, self).get_vc(context, id, fields,**kwargs)
        return self._fields(vc, fields)

    def get_vcs(self, context, filters=None, fields=None,**kwargs):
        #return [{"name":"zuocheng"},{"name":"wentao"}]
        vcs = super(HuaWeiQuantumPlugin, self).get_vcs(context, filters, fields,**kwargs)
        return [self._fields(vc, fields) for vc in vcs]

    def update_vc(self, context, id, vc,**kwargs):
        #return None
        ret = super(HuaWeiQuantumPlugin, self).update_vc(context, id, vc,**kwargs)
        return ret

    def create_vc(self, context, vc,**kwargs):
        #return None
        ret = super(HuaWeiQuantumPlugin,self).create_vc(context,vc,**kwargs)
        return ret

    def delete_vc(self, context, id,**kwargs):
        #return None
        ret = super(HuaWeiQuantumPlugin, self).delete_vc(context, id,**kwargs)
        return ret


########################Site#################################
    def get_site(self, context, id, fields=None,**kwargs):
        #return {"name":"zuocheng"}
        return super(HuaWeiQuantumPlugin,self).get_site(context, id ,fields,**kwargs)

    def get_sites(self, context, filters=None, fields=None,**kwargs):
        #return [{"name":"zuocheng"},{"name":"wentao"}]
        return super(HuaWeiQuantumPlugin,self).get_sites(context,filters,fields,**kwargs)
    
    def update_site(self, context, id, site,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).update_site(context,id,site,**kwargs)

    def create_site(self, context, site,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).create_site(context,site,**kwargs)

    def delete_site(self, context, id,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).delete_site(context,id,**kwargs)
    
############################VnSite##############################
    def get_vn_vnsite(self,context,id,fields=None,**kwargs):
        #return {"name":"zuocheng"}
        return super(HuaWeiQuantumPlugin,self).get_vnsite(context,id,fields,**kwargs)

    def get_vn_vnsites(self,context,filters=None,fields=None,**kwargs):
        #return [{"name":"zuocheng"},{"name":"wentao"}]
        return super(HuaWeiQuantumPlugin,self).get_vnsites(context,filters,fields,**kwargs)
    
    def add_site_to_vn(self,context,id,body=None,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).add_site_to_vn(context,id,**kwargs)
    
    def delete_site_from_vn(self,context,id,body=None,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).delete_site_from_vn(context,id,**kwargs)
    
#######################Virtual Network##########################
    def get_vn(self, context, id, fields=None,**kwargs):
        #return {"name":"zuocheng"}
        return super(HuaWeiQuantumPlugin,self).get_vn(context,id,fields,**kwargs)

    def get_vns(self, context, fields=None,filters=None,**kwargs):
        #return [{"name":"zuocheng"},{"name":"wentao"}]
        return super(HuaWeiQuantumPlugin,self).get_vns(context,fields,**kwargs)

    def update_vn(self, context, id, vn,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).update_vn(context,id,vn,**kwargs)

    def create_vn(self, context, vn,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).create_vn(context,vn,**kwargs)

    def delete_vn(self, context, id,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).delete_vn(context,id,**kwargs)

########################Virtual Link############################
    def get_vn_vnlinks(self, context, filters=None, fields=None,**kwargs):
        #return [{"name":"zuocheng"},{"name":"wentao"}]
        return super(HuaWeiQuantumPlugin,self).get_vlinks(context,**kwargs)
    
    def get_vn_vnlink(self,context,id,fields=None,**kwargs):
        #return {"name":"zuocheng"}
        return super(HuaWeiQuantumPlugin,self).get_vlink(context,id,**kwargs)
    
    def update_vn_vnlink(self,context,id,vnlink,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).update_vlink(context,id,vnlink,**kwargs)
    
    def create_vn_vnlink(self,context,vnlink,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).add_vlink_to_vn(context,vnlink,**kwargs)
    
    def delete_vn_vnlink(self,context,id,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).delete_vlink(context,id,**kwargs)

#####################Attachment################################
    def show_site_attachment(self,context,id,**kwargs):
        #return {"name":"zuocheng"}
        return super(HuaWeiQuantumPlugin,self).show_attachment_for_site(context,id,**kwargs)
    
    def plug_attach_for_site(self,context,id,body,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).plug_attach_for_site(context,id,body,**kwargs)
    
    def unplug_attach_from_site(self,context,id,body,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).unplug_attach_for_site(context,id,body,**kwargs)
    
#######################User#####################################
    def get_users(self,context,filters=None,fields=None,**kwargs):
        #return [{"name":"zuocheng"},{"name":"wentao"}]
        return super(HuaWeiQuantumPlugin,self).get_users(context,filters,fields,**kwargs)
    
    def get_user(self,context,id,fields=None,**kwargs):
        #return {"name":"zuocheng"}
        return super(HuaWeiQuantumPlugin,self).get_user(context,id,fields,**kwargs)
    
    def delete_user(self,context,id,**kwargs):
        #return {"name":"zuocheng"}
        return super(HuaWeiQuantumPlugin,self).delete_user(context,id,**kwargs)
    
    def create_user(self,context, user ,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).create_user(context,user,**kwargs)
    
    def update_user(self,context,id,user,**kwargs):
        #return None
        return super(HuaWeiQuantumPlugin,self).update_user(context,id,user,**kwargs)
    
    def add_site_to_user(self,context,id,body,**kwargs):
        #return None
        action = "users:add_site_to_user"
        try:
            if policy.enforce(context, action, body['user']) == False:
                raise webob.exc.HTTPNotFound()
        except exceptions.PolicyNotAuthorized:
            raise webob.exc.HTTPNotFound()
        return super(HuaWeiQuantumPlugin,self).add_site_to_tenant(context,id,body,**kwargs)
    
    def delete_site_from_user(self,context,id,body,**kwargs):
        #return None
        action = "users:delete_site_from_user"
        try:
            if policy.enforce(context, action, body['user']) == False:
                raise webob.exc.HTTPNotFound()
        except exceptions.PolicyNotAuthorized:
            raise webob.exc.HTTPNotFound()
        return super(HuaWeiQuantumPlugin,self).release_site_from_tenant(context,id,body,**kwargs)
    
    def authorize_user(self,context,id,body,**kwargs):
        #return None
        print "[plugin] authorize_user"
        action = "users:authorize_user"
        try:
            if policy.enforce(context, action, body['user']) == False:
                raise webob.exc.HTTPNotFound()
        except exceptions.PolicyNotAuthorized:
            raise webob.exc.HTTPNotFound()
        if 'user' in body:
            try:
                tenantinfo=context.session.query(huawei_models_v2.TenantInformation).filter_by(tenantid=self._a2b(id)).one()
            except:
                raise webob.exc.HTTPNotFound()
            for policy_key,policy_value in body['user'].iteritems():
                if policy_key in ["vcspolicy","vnspolicy","vnsitespolicy",
                                  "vnlinkspolicy","sitespolicy"]:
                    if policy_key == "vcspolicy":
                        for vcpolicy_key,vcpolicy_value in policy_value.iteritems():
                            if vcpolicy_key in ["create_vc",]:
                                vcbool=convert_to_boolean(vcpolicy_value)
                                if vcbool == True:
                                    self.write_policy_true(vcpolicy_key,tenantinfo.username)
                            else:
                                raise webob.exc.HTTPNotFound()
                    elif policy_key == "vnspolicy":
                        for vnpolicy_key,vnpolicy_value in policy_value.iteritems():
                            if vnpolicy_key in ["create_vn",]:
                                vnbool=convert_to_boolean(vnpolicy_value)
                                if vnbool == True:
                                    self.write_policy_true(vnpolicy_key,tenantinfo.username)
                    elif policy_key == "vnsitespolicy":
                        pass
                    elif policy_key == "vnlinkspolicy":
                        pass
                    elif policy_key == "sitespolicy":
                        pass
                else:
                    raise webob.exc.HTTPNotFound()
        else:
            raise webob.exc.HTTPBadRequest()
    def write_policy_true(self,policy_key,username):
        #global _POLICY_PATH
        print '[plugin] _POLICY_PATH =',policy._POLICY_PATH
        fp = open(policy._POLICY_PATH,'r')
        jsondata = json.load(fp)
        fp.close()
        if policy_key in jsondata:
            policy_value=jsondata[policy_key]
            rolestr='role:'+username
            if policy_value.find(rolestr)!=-1:
                return
            new_policy_value=policy_value+' or role:'+username
            jsondata[policy_key]=new_policy_value
        else:
            raise webob.exc.HTTPNotFound()
        try:
            fp = open(policy._POLICY_PATH,'w')
            fcntl.flock(fp,fcntl.LOCK_EX)
            json.dump(jsondata,fp)
        finally:
            fcntl.flock(fp,fcntl.LOCK_UN)
            fp.close()
            
        
    def write_policy_false(self,policy_key,username):
        #global policy._POLICY_PATH
        print '[plugin] _POLICY_PATH =',policy._POLICY_PATH
        fp = open(policy._POLICY_PATH,'r')
        jsondata = json.load(fp)
        fp.close()
        if policy_key in jsondata:
            policy_value=jsondata[policy_key]
            rolestr1='or role:'+username
            rolestr2='role:'+username+' or'
            rolestr='role:'+username
            if policy_value.find(rolestr1)!=-1 or policy_value.find(rolestr2)!=-1 or policy_value.find(rolestr)!=-1:
                str1,str2=policy_value.split(rolestr,1)
                new_policy_value=str1+str2
                jsondata[policy_key]=new_policy_value
            else:
                return
        else:
            raise webob.exc.HTTPNotFound()
        try:
            fp = open(policy._POLICY_PATH,'w')
            fcntl.flock(fp,fcntl.LOCK_EX)
            json.dump(jsondata,fp)
        finally:
            fcntl.flock(fp,fcntl.LOCK_UN)
            fp.close()