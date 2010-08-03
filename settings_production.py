from settings_shared import *

TEMPLATE_DIRS = (
    "/var/www/riaki/riaki/templates",
)

MEDIA_ROOT = '/var/www/riaki/uploads/'
# put any static media here to override app served static media
STATICMEDIA_MOUNTS = (
    ('/sitemedia', '/var/www/riaki/riaki/sitemedia'),	
)


DEBUG = False
TEMPLATE_DEBUG = DEBUG
