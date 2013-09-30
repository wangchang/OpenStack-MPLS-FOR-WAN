#===============================================================================
# read quantum.plugins.openvswitch.common.config
#===============================================================================
from quantum.openstack.common import cfg

database_opts = [
    cfg.StrOpt('sql_connection', default='sqlite://'),
    cfg.IntOpt('sql_max_retries', default= -1),
    cfg.IntOpt('reconnect_interval', default=2),
    cfg.IntOpt('sql_min_pool_size',
               default=1,
               help="Minimum number of SQL connections to keep open in a "
                    "pool"),
    cfg.IntOpt('sql_max_pool_size',
               default=5,
               help="Maximum number of SQL connections to keep open in a "
                    "pool"),
    cfg.IntOpt('sql_idle_timeout',
               default=3600,
               help="Timeout in seconds before idle sql connections are "
                    "reaped"),
    cfg.BoolOpt('sql_dbpool_enable',
                default=False,
                help="Enable the use of eventlet's db_pool for MySQL"),
]

huawei_opts = [

]

driver_opts = [

]


cfg.CONF.register_opts(database_opts, "DATABASE")
cfg.CONF.register_opts(huawei_opts, "HUAWEI")
cfg.CONF.register_opts(driver_opts, "DRIVER")
