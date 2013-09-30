
from abc import abstractmethod

from quantum.api.v2 import attributes as attr
from quantum.api.v2 import base
from quantum.common import exceptions as qexception
from quantum.api import extensions
from quantum import manager
from quantum.openstack.common import cfg
from quantum import quota



#===============================================================================
# Those are saw by user.
#===============================================================================


# Attribute Map
RESOURCE_ATTRIBUTE_MAP = {
    'users': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:regex': attr.UUID_PATTERN},
               'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'is_visible': True, 'default': ''},
        'passwd':{'allow_post': True, 'allow_put': True,
                 'is_visible':True, 'default':[]},
        'tenant_id':{'allow_post': True, 'allow_put': False,
                 'is_visible':False, 'default':''},
        'company':{'allow_post': True, 'allow_put': True,
                  'is_visible':True, 'default':[]},
        'siteid': {'allow_post': False, 'allow_put': True,
               'validate': {'type:string': None},
               'is_visible': True},
        'usersites':{'allow_post': True, 'allow_put': True,
                 'is_visible':True, 'default':[]},
    },

    'vns': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:regex': attr.UUID_PATTERN},
               'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
               'validate': {'type:string': None},
               'is_visible': False},
        'name': {'allow_post': True, 'allow_put': True,
                 'is_visible': True, 'default': ''},
        'vnsites':{'allow_post': True, 'allow_put': False,
                 'is_visible':True, 'default':[]},
        'vnlinks':{'allow_post': True, 'allow_put': True,
                  'is_visible':True, 'default':[]},
        'linkoption':{'allow_post': True, 'allow_put': False,
                  'is_visible':True, 'default':''},
        'layer':{'allow_post': True, 'allow_put': False,
                  'is_visible':True, 'default':'2'},
    },

    'vcs': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:regex': attr.UUID_PATTERN},
               'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
               'validate': {'type:string': None},
               'is_visible': False},
        'name': {'allow_post': True, 'allow_put': True,
                 'is_visible': True, 'default': ''},
        'site1':{'allow_post': True, 'allow_put': False,
                 'is_visible':True, 'default':{}},
        'site2':{'allow_post': True, 'allow_put': False,
                 'is_visible':True, 'default':{}},
        'qos':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':{}},
        'availability-level':{'allow_post': True, 'allow_put': False,
                              'is_visible':True, 'default':''},
    },

    'sites' : {
        'id':{'allow_post': False, 'allow_put': False,
              'validate': {'type:regex': attr.UUID_PATTERN},
              'is_visible':True}, 
        'tenant_id':{'allow_post': True, 'allow_put': False,
              'validate': {'type:string': None},
              'is_visible':False}, 
        'name':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'ceasnum':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'peasnum':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'peaddr':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'peloaddr':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'interface':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'vlanid':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'location':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''}, 
        'description':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''}, 
        'attachment':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':{}},
        'type':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'state':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':0},
        'sitebusy':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':0},
        'vnname':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'vcname':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
    },

    'vnsites' : {
        'id':{'allow_post': False, 'allow_put': False,
              'validate': {'type:regex': attr.UUID_PATTERN},
              'is_visible':True}, 
        'tenant_id':{'allow_post': True, 'allow_put': False,
              'validate': {'type:string': None},
              'is_visible':False}, 
        'ceasnum':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'peasnum':{'allow_post': True, 'allow_put': False,
               'is_visible':True, 'default':''},
        'location':{'allow_post': True, 'allow_put': False,
               'is_visible':True, 'default':''}, 
        'description':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''}, 
        'attachment':{'allow_post': True, 'allow_put': False,
               'is_visible':True, 'default':{}},
        'type':{'allow_post': True, 'allow_put': False,
               'is_visible':True, 'default':''},
    },

    'vnlinks' : {
        'pre_id':{'allow_post': False, 'allow_put': False,
              'is_visible':True}, 
        'tenant_id':{'allow_post': True, 'allow_put': False,
              'validate': {'type:string': None},
              'is_visible':False},
        'site1':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':{}},
        'site2':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':{}},
        'qos':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':{}}
                
    },
    'attachment' : {
        'ceasnum':{'allow_post': True, 'allow_put': False,
               'is_visible':True, 'default':''},
        'routeprotocol':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':{}},
        'transportippool':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':{}}
    },
    'routeprotocol': {
        'name':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'type':{'allow_post': True, 'allow_put': True,
               'is_visible':False, 'default':''},
    },
    'transportippool':{
        'peip':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'ceip':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
        'mask':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''}
    },            
     'qos':{
            'direction':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
            'bandwidth':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''}},
            're_bandwidth':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
            'id':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
            'delay':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''},
            'jitter':{'allow_post': True, 'allow_put': True,
               'is_visible':True, 'default':''}
}
class Huawei(extensions.ExtensionDescriptor):

    def get_name(self):
        return "Hua Wei"
    def get_alias(self):
        return "huawei"
    def get_description(self):
        return "The extension is provided by HuaWei."
    def get_namespace(self):
        return "http://www.huawei.com/xx"
    def get_updated(self):
        return "2012-x-x"
    def get_resources(self):
        """ Returns Ext Resources """
        resources = []
        plugin = manager.QuantumManager.get_plugin()
        for resource_name in ['vn', 'vc', 'site', 'vnsite', 'vnlink', 'user']:
            collection_name = resource_name + "s"
            params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())
            parent_resource=None
            member_actions = {}
            if resource_name == 'site':
                member_actions = {'show_site_attachment':'GET',
                                  'unplug_attach_from_site': 'PUT',
                                  'plug_attach_for_site': 'PUT'}
            if resource_name == 'vnsite':
                parent_resource={}
                parent_resource['member_name']='vn'
                parent_resource['collection_name']='vns'
                member_actions={'add_site_to_vn':'PUT',
                                'delete_site_from_vn':'PUT'}
            if resource_name == 'vnlink':
                parent_resource={}
                parent_resource['member_name']='vn'
                parent_resource['collection_name']='vns'
            if resource_name == 'user':
                member_actions={'add_site_to_user':'PUT',
                                'delete_site_from_user':'PUT',
                                'authorize_user':'PUT'}
            quota.QUOTAS.register_resource_by_name(resource_name)

            controller = base.create_resource(collection_name,
                                              resource_name,
                                              plugin, params,
                                              member_actions=member_actions,
                                              parent=parent_resource)

            resource = extensions.ResourceExtension(collection_name,
                                              controller,
                                              member_actions=member_actions,
                                              parent=parent_resource)
            resources.append(resource)

        return resources
