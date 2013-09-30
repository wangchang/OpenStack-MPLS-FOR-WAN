#
#            HuaWei Plugin Exceptions
#
#
#
#
#
#
#
#
#
#


#from quantum.openstack.common.exceptions import Error
#from quantum.openstack.common.exceptions import OpenstackException

from quantum.common.exceptions import QuantumException,BadRequest,NotFound,NotAuthorized,AdminRequired,InUse

class BadRequest(BadRequest):
	pass
	
class NotAuthorized(NotAuthorized):
	pass
	
class AdminRequired(AdminRequired):
	pass

class SiteNotFound(NotFound):
	message = _("Site %(site_id)s could not be found")
	
class VcNotFound(NotFound):
	message = _("VC %(vc_id)s could not be found")
	
class VnNotFound(NotFound):
	message = _("VN %(vn_id)s could not be found")
	
class AttachmentNotFound(NotFound):
	message = _("Attachment of site %(site_id)s could not be found")
	
class VlinkNotFound(NotFound):
	message = _("Vlink %(vlink_id)s could not be found")
	
class SiteInUse(InUse):
	message = _("the site %(site_id)s is in use")
	
class VcInUSe(InUse):
	message = _("cannot complete the operation, the VC %(vc_id)s is in use")
	
class VnInUse(InUse):
	message = _("cannot complete the operation, the VN %(vn_id)s is in use")
	
class MultiResults(QuantumException):
    message = _("Error for multi-results")
	
