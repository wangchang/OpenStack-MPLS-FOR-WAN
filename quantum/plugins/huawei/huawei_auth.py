from quantum import context
from quantum.openstack.common import cfg
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
import datetime
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4
import webob
import webob.dec
import webob.exc
from quantum.api.v2 import attributes
from quantum.db.model_base import QuantumBaseV2
from quantum.openstack.common import jsonutils as json

hw_auth_base = declarative_base(cls=QuantumBaseV2)

class User(hw_auth_base):
    '''tenant informaation'''
    __tablename__ = 'user'
    
    name = Column(String(64), nullable=True, default=None)
    passwd = Column(String(64), nullable=True, default=None)
    company = Column(String(64), nullable=True, default=None)
    id = Column(String(36), primary_key=True)
    token_id = Column(String(36), nullable=True, default=None)
    expires = Column(DateTime(), default=None)

#===============================================================================
# class VnSitesPolicy(hw_auth_base):
#    '''tenant informaation'''
#    __tablename__ = 'vnsitespolicy'
#    id = Column(String(36), primary_key=True)
#    userid = Column(String(36))
#    get_vnsite = Column(Boolean(), default=False)
#    create_vnsite = Column(Boolean(), default=False)
#    update_vnsite = Column(Boolean(), default=False)
#    delete_vnsite = Column(Boolean(), default=False)
# 
# class VnLinksPolicy(hw_auth_base):
#    '''tenant informaation'''
#    __tablename__ = 'vnlinkspolicy'
#    
#    id = Column(String(36), primary_key=True)
#    userid = Column(String(36))
#    get_vnlink = Column(Boolean(), default=False)
#    create_vnlink = Column(Boolean(), default=False)
#    update_vnlink = Column(Boolean(), default=False)
#    delete_vnlink = Column(Boolean(), default=False)
# 
# class SitesPolicy(hw_auth_base):
#    '''tenant informaation'''
#    __tablename__ = 'sitespolicy'
#    
#    id = Column(String(36), primary_key=True)
#    userid = Column(String(36))
#    get_site = Column(Boolean(), default=False)
#    create_site = Column(Boolean(), default=False)
#    update_site = Column(Boolean(), default=False)
#    delete_site = Column(Boolean(), default=False)
#===============================================================================

    
class VnsPolicy(hw_auth_base):
    '''tenant informaation'''
    __tablename__ = 'vnspolicy'
    
    id = Column(String(36), primary_key=True)
    userid = Column(String(36))
    #get_vn = Column(Boolean(), default=False)
    create_vn = Column(Boolean(), default=False)
    #update_vn = Column(Boolean(), default=False)
    #delete_vn = Column(Boolean(), default=False)
    
class VcsPolicy(hw_auth_base):
    '''tenant informaation'''
    __tablename__ = 'vcspolicy'
    
    id = Column(String(36), primary_key=True)
    userid = Column(String(36))
    #get_vc = Column(Boolean(), default=False)
    create_vc = Column(Boolean(), default=False)
    #update_vc = Column(Boolean(), default=False)
    #delete_vc = Column(Boolean(), default=False)
    

_HW_AUTH_ENGINE = create_engine("mysql://hw_quantum_auth:openstack@localhost:3306/hw_quantum_auth")
_HW_ADMIN_NAME = 'admin'
_HW_ADMIN_PASSWD = 'admin'
Session=sessionmaker(bind=_HW_AUTH_ENGINE)

class Token(object):
    def check_token(self,token_id):
        '''check token_id is correct. Return tenant_id , if passed.'''
        session=Session()
        query = session.query(User)
        try:
            user = query.filter_by(token_id = token_id.lower()).one()
        except:
            raise webob.exc.HTTPUnauthorized(detail="Token value is out of date.")
        if user.name == _HW_ADMIN_NAME and user.passwd == _HW_ADMIN_PASSWD:
            return user.id,'admin',True
        now = datetime.datetime.utcnow()
        if not user.expires or now < user.expires:
            return user.id,user.name,False
        else:
            raise webob.exc.HTTPUnauthorized(detail="Token value is out of date.")
        
    def create_token(self, name, passwd):
        ''''Check user name and passwd , if passed, create a token_id and expires.'''
        session=Session()
        query = session.query(User)
        try:
            user = query.filter_by(name = name, passwd = passwd).one()
        except:
            raise webob.exc.HTTPUnauthorized(detail="Username or password error.")
        print "[auth]token_id in user table = ",user['token_id']

        now = datetime.datetime.utcnow()
        expire_delta = datetime.timedelta(seconds=86400)
        if user['token_id'] != None:
            user['expires']=now+expire_delta
            token_id=user['token_id']
            session.commit()
            return token_id
        
        token_id=(uuid4().get_hex()).lower()
        user['token_id']=token_id
        user['expires']=now+expire_delta
        session.commit()
        return token_id


class HuaweiAuthProtocol(object):
    def __init__(self, application, conf):
        self.application = application
        self.conf = conf
        global hw_auth_base
        global _HW_AUTH_ENGINE
        global _HW_ADMIN_NAME
        global _HW_ADMIN_PASSWD
        hw_auth_base.metadata.create_all(_HW_AUTH_ENGINE)
        session=Session()
        query = session.query(User)
        query = query.filter_by(name = _HW_ADMIN_NAME)
        if not query.count():
            session.add(User(name=_HW_ADMIN_NAME,passwd=_HW_ADMIN_PASSWD,id=uuid4().get_hex()))
            session.commit()
       
    def __call__(self, environ, start_response):
        print "[auth]get through Huawei auth."
        #self._check_token(environ, start_response)
        try:
            return self._parse_request(environ,start_response)
        except webob.exc.HTTPException,resp:
            resp.body = json.dumps({'QuantumError': str(resp)})
            resp.content_type = 'application/json'
            return resp(environ,start_response)
        except Exception,resp:
            body = json.dumps({'QuantumError': str(resp)})
            kwargs = {'body': body, 'content_type': 'application/json'}
            raise webob.exc.HTTPInternalServerError(**kwargs)
    
    def _parse_method_and_path(self, environ, info):
        '''Parse request method , path.'''
        method=environ['REQUEST_METHOD']
        path=environ['PATH_INFO']
        info['method']=method
        if path.startswith('/policies'):
            pre,back=path.split('/policies',1)
            info['resource']='policies'
            if back.startswith('/'):
                a,userid=back.split('/',1)
                info['userid']=userid
            else:
                info['userid']=None
        elif path.startswith('/users'):
            info['resource']='users'
            pre,back=path.split('/users',1)
            if back.startswith('/'):
                a,userid=back.split('/',1)
                if userid.find('/') != -1:
                    userid,action=userid.split('/',1)
                    info['userid']=userid
                    info['action']=action
                else:
                    info['userid']=userid
            else:
                info['userid']=None
            
            
    def _check_is_get_user_policy(self, info):
        '''Check requst is or not:
        GET  /policies
        GET  /policies/userid
        if is , return a dict , else ,return False.
        '''
        if 'resource' in info and info['resource']=='policies' \
        and 'method' in info and info['method']=='GET':
            if 'userid' in info and info['userid']:
                session=Session()
                query = session.query(User)
                try:
                    user = query.filter_by(id = info['userid']).one() #raise exception
                except:
                    raise webob.exc.HTTPNotFound()
                userid = user.id
                username = user.name
                re = dict()
                session=Session()
                query = session.query(VnsPolicy)
                query = query.filter_by(userid=userid)
                if query.count(): #don't raise exception
                    re['vnspolicy']={"create_vn":(query.first()).create_vn}
                session=Session()
                query = session.query(VcsPolicy)
                query = query.filter_by(userid=userid)
                if query.count():#don't raise exception
                    re['vcspolicy']={"create_vc":(query.first()).create_vc}
                re['username']=username
                return re
            else:
                session=Session()
                query = session.query(User)
                userall = query.all()
                re = []
                for user in userall:
                    session_t = Session()
                    query_t = session_t.query(VnsPolicy)
                    query_t = query_t.filter_by(userid=user.id)
                    re_t = dict()
                    if query_t.count():
                        re_t['vnspolicy']={"create_vn":(query_t.first()).create_vn}
                    session_t = Session()
                    query_t = session_t.query(VcsPolicy)
                    query_t = query_t.filter_by(userid=user.id)
                    if query_t.count():
                        re_t['vcspolicy']={"create_vc":(query_t.first()).create_vc}
                    re_t['username'] = user.name
                    re.append(re_t)
                return re
        return False
                    
    def _check_is_create_user(self,request,re,info):
        '''Withdraw tenant_id from re ,read body from write in database'''
        if 'resource' in info and info['resource']=='users' \
        and 'method' in info and info['method']=='POST':
            print '[auth] create user'
            re_json=json.loads(re[0])
            print '[auth] re_json = ',re_json
            userid=re_json['user']['id']
            body=json.loads(request.body)
            username=body['user']['name']
            userpasswd=body['user']['passwd']
            usercompany=body['user']['company']
            session=Session()
            session.add(User(name=username,passwd=userpasswd,id=userid,company=usercompany))
            session.commit()
            return True
        return False
    def _check_is_update_user(self,request,info):
        '''Use following method to get body.Body must be json format.'''
        if 'resource' in info and info['resource']=='users' \
        and 'method' in info and info['method']=='PUT' and 'action' not in info  \
        and 'userid' in info and info['userid']:
            print '[auth] update user'
            session = Session()
            query = session.query(User)
            try:
                user = query.filter_by(id = info['userid']).one()
            except:
                raise webob.exc.HTTPBadRequest(detail="User doesn't exist.")
            body=json.loads(request.body)
            new_passwd=body['user']['passwd']
            user.update({'passwd':new_passwd})
            session.commit()
            return True
        return False
    
    def _check_is_delete_user(self,info):
        if 'resource' in info and info['resource']=='users' and 'method' in info  \
        and info['method']=='DELETE' and 'userid' in info and info['userid']:
            print '[auth] delete user'
            userid = info['userid']
            session = Session()
            query = session.query(User)
            try:
                user = query.filter_by(id = userid).one()
            except:
                raise webob.exc.HTTPBadRequest(detail="User doesn't exist.")
            session.delete(user)
            session.commit()
            session=Session()
            try:
                vnspolicy=session.query(VnsPolicy).filter_by(userid=userid).one()
                session.delete(vnspolicy)
                session.commit()
            except:
                pass
            session=Session()
            try:
                vcspolicy=session.query(VcsPolicy).filter_by(userid=userid).one()
                session.delete(vcspolicy)
                session.commit()
            except:
                pass
            return True
        return False
    def _check_is_authorize_user(self,request,info):
        if 'resource' in info and info['resource']=='users' and 'method' in info  \
        and info['method']=='PUT' and 'userid' in info and info['userid'] \
        and 'action' in info and info['action']=='authorize_user':
            print '[auth] authorize user'
            userid=info['userid']
            body=json.loads(request.body)
            session=Session()
            try:
                session.query(User).filter_by(id=userid).one()
            except:
                raise webob.exc.HTTPBadRequest(detail="User doesn't exist.")
            #body : 'vnspolciy' , 'vcspolicy' , 'vnsitespolicy' , 'vnlinkspolicy' , 'sitespolicy'
            if 'vnspolicy' in body['user']:
                vnspolicy=body['user']['vnspolicy']
                for vnpolicy_key,vnpolicy_value in vnspolicy.iteritems():
                    if vnpolicy_key in ['create_vn',]:
                        session=Session()
                        query=session.query(VnsPolicy).filter_by(userid=userid)
                        if query.count():
                            userpolicy=query.one()
                            userpolicy.update({vnpolicy_key:attributes.convert_to_boolean(vnpolicy_value)})
                            session.commit()
                        else:
                            vnkwargs={vnpolicy_key:attributes.convert_to_boolean(vnpolicy_value)}
                            session.add(VnsPolicy(id=uuid4().get_hex(),userid=userid,**vnkwargs))
                            session.commit()
            if 'vcspolicy' in body['user']:
                vcspolicy=body['user']['vcspolicy']
                for vcpolicy_key,vcpolicy_value in vcspolicy.iteritems():
                    if vcpolicy_key in ['create_vc',]:
                        session=Session()
                        query=session.query(VcsPolicy).filter_by(userid=userid)
                        if query.count():
                            userpolicy=query.one()
                            userpolicy.update({vcpolicy_key:attributes.convert_to_boolean(vcpolicy_value)})
                            session.commit()
                        else:
                            vckwargs={vcpolicy_key:attributes.convert_to_boolean(vcpolicy_value)}
                            session.add(VcsPolicy(id=uuid4().get_hex(),userid=userid,**vckwargs))
                            session.commit()
            if 'vnsitespolicy' in body['user']:
                pass
            if 'vnlinkspolicy' in body['user']:
                pass
            if 'sitespolicy' in body['user']:
                pass
            return True
        return False

    def _parse_request(self, environ, start_response):
        token=Token()
        req = webob.Request(environ)
        req.response = req.ResponseClass()
        req.response.request = req
        try:
            print '[auth] request body = %s' % json.loads(req.body)
        except:
            print '[auth] no request body or request body exception.'
            pass
        body = {}
        @webob.dec.wsgify
        def re_control(request):
            s=json.dumps(body)
            return webob.Response(request=request, status=200,content_type='application/json',body=s,charset='utf8')
        
        print "[auth] check token..."
        if 'HTTP_X_AUTH_TOKEN' in environ:
            token_id=environ['HTTP_X_AUTH_TOKEN']
            print '[auth] receive token_id = ',token_id
            userid,username,is_admin=token.check_token(token_id=token_id)
            print '[auth] chech_token result = ',userid,username,is_admin
            if is_admin==True:
                info={}
                self._parse_method_and_path(environ,info)
                print '[auth] parse method and path result = ',info 
                body = self._check_is_get_user_policy(info)
                if body:
                    return re_control(environ,start_response)
                admin_context=context.Context(user_id=None,tenant_id=userid.lower(),is_admin=True,read_deleted="no")
                environ['quantum.context'] = admin_context
                re=self.application(environ ,start_response)
                print '[auth] controller app return = ',re
                try:
                    first=json.loads(re[0])
                except:
                    #if controller app return ['']
                    #if self._check_is_create_user(req,re,info):
                    #    pass
                    if self._check_is_update_user(req,info):
                        pass
                    elif self._check_is_delete_user(info):
                        pass
                    elif self._check_is_authorize_user(req,info):
                        pass
                    print '[auth] auth return location1 = ',re
                    return re
                if isinstance(first,dict):
                    print '[auth] check uesr or users in plugin return... '
                    if 'user' not in first :#and 'users' not in first:
                        return re
                #===============================================================
                # If plugin 'authorize_user' method success , return None , then do following check.
                # If plugin 'create_user' method success , return ['{"user":{"tenant_id":"xxxx"}} , then do following check.
                # If plugin 'update_user' method success , return None , then do following check.
                # If plugin 'delete_user' method success , return None , then do following check.
                # If admin use other API return None , then do following check.
                #===============================================================
                if self._check_is_create_user(req,re,info):
                    pass
                #elif self._check_is_update_user(req,info):
                #    pass
                #elif self._check_is_delete_user(info):
                #    pass
                #elif self._check_is_authorize_user(req,info):
                #    pass
                print '[auth] auth return location2 = ',re
                return re
            else:
                cont = context.Context(user_id=None, tenant_id=userid.lower(), roles=[username])
                environ['quantum.context'] = cont
                re=self.application(environ ,start_response)
                print '[auth] controller app return = ',re
                print '[auth] auth return location3 = ',re
                return re
        else:
            print "[auth] check user's name and passwd..."
            if 'HTTP_X_USERNAME' in environ and 'HTTP_X_USERPASSWD' in environ:
                name=environ['HTTP_X_USERNAME']
                passwd=environ['HTTP_X_USERPASSWD']
                token_id=token.create_token(name, passwd)
                #return {'token_id':token_id}
                print "[auth] token_id = ",token_id
                body={"token_id":str(token_id)}
                return re_control(environ,start_response)
            else:
                raise webob.exc.HTTPBadRequest

def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def auth_filter(app):
        return HuaweiAuthProtocol(app, conf)
    return auth_filter
#===============================================================================
# #
# class Token(object):
#    def get_token(self):
#        Session=sessionmaker(bind=_HW_AUTH_ENGINE,autocommit=True)
#        session=Session()
#        query = session.query(TokenModel)
#        query = query.filter_by(id=self.token_to_key(token_id), valid=True)
#        token_ref = query.first()
#        now = datetime.datetime.utcnow()
#        if token_ref and (not token_ref.expires or now < token_ref.expires):
#            return token_ref.to_dict()
#        else:
#            raise exception.TokenNotFound(token_id=token_id)
# 
# _HW_POLICY_CACHE = {}
# _HW_POLICY_PATH = None
# _hw_policy_columns = {}
# _HW_AUTH_ENGINE =None 
# 
# class HuaweiAuthProtocol(object):
#    def __init__(self, application, conf):
#        self.application = application
#        self.conf = conf
#        self._load_config_file()
#        self._db_create_table()
#        
#    def __call__(self, environ, start_response):
#        print "[auth]get through Huawei auth."
#        te_id=None
#        if environ.get('HTTP_X_TENANT_ID'):
#            te_id = environ['HTTP_X_TENANT_ID']
#        cont = context.Context(user_id=None, tenant_id=te_id)
#        if environ.get('HTTP_X_VN_ID'):
#            cont.vn_id=environ['HTTP_X_VN_ID']
#        if environ.get('HTTP_X_SITE1_ID'):
#            cont.site1_id=environ['HTTP_X_SITE1_ID']
#        if environ.get('HTTP_X_SITE2_ID'):
#            cont.site2_id=environ['HTTP_X_SITE2_ID']
#        environ['quantum.context'] = cont
#        return self.application(environ ,start_response)
#    
#    def _set_policies(self, data):
#        '''an example in hw_auth_file:
#        {'vnspolicy':{
#        'attributes':['vnsites','vnlinks'],
#        'actions':['get_vn','create_vn','update_vn','delete_vn']},}
#    
#        The 'actions' columns are 'Column(Boolean(), default=False))' type.
#        The 'attributes' columns are 'Column(String(64), nullable=True, default=None)' type.
#        
#        then , the 'vnspolicy' table in auth_database may like this:
#        columns:   get_vn| create_vn | delete_vn | update_vn | vnsites | vnlinks         
#        values:       1  |     0     |      0    |     1     | get_vn  | get_vn,update_vn
#        '''
#        
#        global _hw_policy_columns
#        _hw_policy_columns= dict(jsonutils.loads(data))
#        
#    def _load_config_file(self):
#        global _HW_POLICY_CACHE
#        global _HW_POLICY_PATH
#        _HW_POLICY_PATH = utils.find_config_file({}, cfg.CONF.hw_auth_file)
#        utils.read_cached_file(_HW_POLICY_PATH, _HW_POLICY_CACHE,reload_func=self._set_policies)
#        
#    def _db_create_tale(self):
#        global _hw_policy_columns
#        if  _hw_policy_columns:
#            global _HW_AUTH_ENGINE
#            _HW_AUTH_ENGINE=create_engine("mysql://huawei_quantum_auth:openstack@localhost:3306/huawei_quantum_auth",echo=True)
#            metadata=MetaData()
#            for k,v in _hw_policy_columns.items():
#                columns=[]
#                for item in v('attributes'):
#                    columns.append(Column(item, String(64), nullable=True, default=None))
#                for item in v('actions'):
#                    columns.append(Column(item, Boolean(), default=False))
#                tuple_columns=tuple(columns)
#                table=Table(k,metadata,tuple_columns)
#                table.create(_HW_AUTH_ENGINE)
#            user_table=Table('user',metadata,
#                             Column('name',String(64), nullable=True, default=None),
#                             Column('passwd',String(64), nullable=True, default=None),
#                             Column('company',String(64), nullable=True, default=None),
#                             Column('id',String(36), nullable=True, default=None),)
# 
# 
#            
# 
# 
# def filter_factory(global_conf, **local_conf):
#    conf = global_conf.copy()
#    conf.update(local_conf)
# 
#    def auth_filter(app):
#        return HuaweiAuthProtocol(app, conf)
#    return auth_filter
#===============================================================================
