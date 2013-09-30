#=========================================================================#
#
#
#
#
#@author:
#@author:
#========================================================================


import quantum.db.api as db
from quantum.db import models_v2
from sqlalchemy.orm import exc
from quantum.common import exceptions as q_exc
from quantum.openstack.common import cfg
from quantum.plugins.huawei.common import config
from sqlalchemy.ext import declarative

HW_BASE = declarative.declarative_base(cls=models_v2.model_base.QuantumBaseV2)

def initialize():
    options = {"sql_connection": "%s" % cfg.CONF.DATABASE.sql_connection}
    options.update({"sql_max_retries": cfg.CONF.DATABASE.sql_max_retries})
    options.update({"reconnect_interval":cfg.CONF.DATABASE.reconnect_interval})
    options.update({"base": HW_BASE})
    options.update({"sql_dbpool_enable":cfg.CONF.DATABASE.sql_dbpool_enable})
    db.configure_db(options)

