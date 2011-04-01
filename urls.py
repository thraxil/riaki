from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
import os.path
admin.autodiscover()
import staticmedia
from django.views.generic.simple import redirect_to

site_media_root = os.path.join(os.path.dirname(__file__),"media")

urlpatterns = patterns('',
                       (r'^$',redirect_to, {'url' : '/page/index/'}),
                       (r'^page/(?P<slug>[^/]*)/$','main.views.page'),
                       (r'^tag/$','main.views.tag_index'),
                       (r'^tag/(?P<tag>[^/]+)/$','main.views.tag'),
                       (r'^tag/(?P<tag>[^/]+)/delete/$','main.views.delete_tag'),
                       (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': site_media_root}),
                       (r'^uploads/(?P<path>.*)$','django.views.static.serve',{'document_root' : settings.MEDIA_ROOT}),
) + staticmedia.serve()

