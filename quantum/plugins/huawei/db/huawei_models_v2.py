from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Binary, DateTime, orm
from datetime import datetime
import binascii
from uuid import uuid4
from quantum.plugins.huawei.db import huawei_db_base

#class ResponseCommand(huawei_db_base.HW_BASE):
#	'''Represents the command which has been executed'''
#	__tablename__ = 'responselog'
	
#	siteid = Column(Binary(16),nullable=False)
#	type = Column(String(36),nullable=False)
#	targetid = Column(Binary(16),nullable=False)
#	xml = Column(String(256),nullable=False)
#	date = Column(DateTime,nullable=False,default=datetime.now)
	
#	def __init__(self,siteid,type,targetid,xml):
#		self.siteid = siteid
#		self.type = type
#		self.targetid = targetid
#		
#	def __repr__(self):
#		return ""
class TenantInformation(huawei_db_base.HW_BASE):
    '''tenant informaation'''
    __tablename__ = 'tenantinfo'
    
    tenantid = Column(Binary(16),nullable=False, primary_key=True)
    username = Column(String(64), nullable=True, default=None)
    pwd = Column(String(64), nullable=True, default=None)
    company = Column(String(64),nullable=True,default=None)


class SiteAttachment(huawei_db_base.HW_BASE):
	'''the Attachment info of site'''
	__tablename__ = 'siteattach'
	
	siteid = Column(Binary(16), ForeignKey("siteinfo.siteid", ondelete="CASCADE"), nullable=False, primary_key=True)
	routetype = Column(String(32), nullable=True, default=None)
	xmlcontent = Column(String(256), nullable=False)
	
#	def __init__(self,siteid,routetype,xmlcontent):
#		self.siteid = siteid
#		self.routetype = routetype
#		self.xmlcontent = xmlcontent
#	
#	def __repr__(self):
#		return "<SiteAttachment(%s,%s,%s)>" %(format(self.siteid,'b'),self.routetype,self.xmlcontent)

class SiteInformation(huawei_db_base.HW_BASE):
	'''the detail information of a site'''
	__tablename__ = 'siteinfo'
	
	siteid = Column(Binary(16), nullable=False, primary_key=True)
	sitename = Column(String(64), default=None)
	geoinfo = Column(String(128), default=None)
	peasnum = Column(Integer(10), default=None)
	ceasnum = Column(Integer(10), default=None)
	peaddr = Column(String(15), default=None)
	peloaddr = Column(String(15), default=None)
	vlanid = Column(Integer(10), default=None)
	stat = Column(Integer(10), default=0)
	interface = Column(String(32), default=None)
	
#	def __init__(self,siteid,sitename,geoinfo):
#		self.siteid = siteid
#		self.sitename = sitename
#		self.geoinfo = geoinfo
		
#	def __repr__(self):
#		return "<SiteInformation(%s,%s,%s)>" % (format(self.siteid,'b'),self.sitename,self.geoinfo)

class SiteUpdate(huawei_db_base.HW_BASE):
	'''Represents the command sended to a specific site'''
	__tablename__ = 'siteupdate'
	
	siteid = Column(Binary(16), nullable=False)
	type = Column(String(36), nullable=False, primary_key=True)
	targetid = Column(Binary(16), nullable=False, primary_key=True)
	xml = Column(String(256), nullable=False)
		
class TenantSites(huawei_db_base.HW_BASE):
	'''represent the available sites for a tenant'''
	__tablename__ = 'tenantsite'
	
	siteid = Column(Binary(16), nullable=False, primary_key=True)
	tenantid = Column(Binary(16), nullable=False)
	desc = Column(String(128), default=None)
	sitebusy = Column(Integer(10),default=0)
	
#	def __init__(self,tenantid,siteid,desc):
#		self.siteid = siteid
#		self.tenantid = tenantid
#		self.desc =desc
	
#	def __repr__(self):
#		return "<TenantSites(%s,%s,%s)>" % (format(self.tenantid,'b'),format(self.siteid,'b'),desc)

class  TenantVc(huawei_db_base.HW_BASE):
	'''represent VCs belong to a tenant'''
	__tablename__ = 'tenantvc'
	
	vcid = Column(Binary(16), ForeignKey("vcinfo.vcid", ondelete="CASCADE"), nullable=False, primary_key=True, default=binascii.a2b_hex(uuid4().hex)) 
	tenantid = Column(Binary(16), nullable=False, primary_key=True)
	vcname = Column(String(64), default=None)
	
#	def __init__(self,tenantid,vcname):
#		self.tenantid = tenantid
#		self.vcname = vcname
#		self.vcid = uuid4()
	
#	def __repr__(self):
#		return "<TenantVc(%s,%s,%s)>" % (format(self.tenantid,'b'),format(self.vcid,'b'),vcname)

class TenantVn(huawei_db_base.HW_BASE):
	'''represent VNs belong to a tenant'''

	__tablename__ = 'tenantvn'
	
	tenantid = Column(Binary(16), nullable=False, primary_key=True)
	vnid = Column(Binary(16), ForeignKey("vninfo.vnid", ondelete=True), nullable=False, primary_key=True)
	vnname = Column(String(64), default=None)
	
#	def __init__(self,tenantid,vnname):
#		self.tenantid = tenantid
#		self.vnname = vnname
#		self.vnid = uuid4()
	
#	def __repr__(self):
#		return "<TenantVn(%s,%s,%s)>" % (format(self.tenantid,'b'),format(self.vnid,'b'),self.vnname)
		
class VcInformation(huawei_db_base.HW_BASE):
	'''represent the detail infomation of a specific VC'''
	__tablename__ = 'vcinfo'
	
	vcid = Column(Binary(16), nullable=False, primary_key=True, default=binascii.a2b_hex(uuid4().hex))
	site1id = Column(Binary(16), nullable=False)
	site2id = Column(Binary(16), nullable=False)
	vlinkid = Column(Integer(10), nullable=False)
	back_vlinkid = Column(Integer(10), nullable=False)
	pwid = Column(Integer(10), nullable=False)
	
#	def __init__(self,site1id,site2id,vlinkid,back_vlinkid):
#		self.vcid = uuid4()
#		self.site1id = site1id
#		self.site2id = site2id
#		self.vlinkid = vlinkid
#		self.back_vlinkid = back_vlinkid
	
#	def __repr__(self):
#		return "<VcInformation(%s,%s,%s,%d,%d)>" % (format(self.vcid,'b'),format(self.site1id,'b'),format(self.site2id,'b'),vlinkdid,back_vlinkid)
		
class VlinkInformation(huawei_db_base.HW_BASE):
	'''represent the detail information of a specific vlink'''
	__tablename__ = 'vlink'

	vlinkid = Column(Integer(10), nullable=False, primary_key=True)
	site1id = Column(Binary(16), nullable=False)
	site2id = Column(Binary(16), nullable=False)
	bandwidth = Column(Integer(10), default=None)
	tunnelid = Column(Integer(10), nullable=False)
	
#	def __init__(self,vlinkid,site1id,site2id,bandwidth):
#		self.vlinkid = vlinkid
#		self.site1id = site1id
#		self.site2id = site2id
#		self.bandwidth = bandwidth
	
#	def __repr__(self):
#		return "<VlinkInformation(%d,%s,%s,%d)>" % (vlinkid,format(self.site1id,'b'),format(self.site2id,'b'),bandwidth)
		
class VnLink(huawei_db_base.HW_BASE):
	'''represent the vlinks belong to a specific VN'''
	__tablename__ = 'vnlink'
	
	vnid = Column(Binary(16), ForeignKey("vninfo.vnid", ondelete="CASCADE"), nullable=False)
	vlinkid = Column(Integer(10), nullable=False, primary_key=True)

class VnSite(huawei_db_base.HW_BASE):
	'''represent the sites belong to a specific VN'''
	__tablename__ = 'vnsite'
	
	vnid = Column(Binary(16), ForeignKey("vninfo.vnid", ondelete="CASCADE"), nullable=False, primary_key=True)
	siteid = Column(Binary(10), nullable=False, primary_key=True)
	vnrt = Column(Integer(10), default=None)

class VnInformation(huawei_db_base.HW_BASE):
	'''represent the detail information of a specific VN'''
	__tablename__ = 'vninfo'
	
	vnid = Column(Binary(16), nullable=False, primary_key=True, default=binascii.a2b_hex(uuid4().hex))
	sitecnt = Column(Integer(10), nullable=False)
	vpntype = Column(Integer(10), nullable=False)
	sites = orm.relationship(VnSite, backref='vninfo')
	vlinks = orm.relationship(VnLink, backref='vninfo')
	
	

	
	
	
	
	
	
	
	
	
	
	
	
