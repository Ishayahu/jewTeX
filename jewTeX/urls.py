"""jewTeX URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
# from django.urls import path
from django.urls import path, re_path
import texts.views
import database.views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('avoda/', database.views.index, name='avoda_index'),
    path('avoda/tag/<int:pk>', database.views.list_by_tag, name='avoda_list_by_tag'),
    path('avoda/show/<int:pk>', database.views.show_by_pk, name='avoda_show_by_pk'),

    re_path(r'^$', texts.views.index, name='index'),
    path(r'utils/terms_to_define', texts.views.terms_to_define, name='terms_to_define'),
    path(r'utils/need_to_be_done', texts.views.need_to_be_done, name='need_to_be_done'),
    path(r'utils/not_translated', texts.views.need_to_translate, name='not_translated'),
    path(r'utils/search/', texts.views.search, name='search'),
    path('<slug:author_name>/', texts.views.author, name='author'),
    path('<slug:author_name>/<slug:book_name>/', texts.views.book, name='book'),
    # path('open/<slug:author>/<slug:book>/siman=<int:siman>&seif=<int:seif>/', texts.views.open_by_siman_and_seif, name = 'open_by_siman_seif'),
    # url(r'open/([^/]+)/([^/]+)/([^/]+)/([^/]+)/$', texts.views.open_text_old, name = 'open'),
    re_path(r'open/([^/]+)/([^/]+)/([^/]+)/$', texts.views.open_text, kwargs={'api': False}, name='open_from_xml'),
    re_path(r'api/text/([^/]+)/([^/]+)/([^/]+)/$', texts.views.open_text, kwargs={'api': True}, name='text_api_request'),
    # re_path(r'api/text/([^/]+)/([^/]+)/([^/]+)/$', texts.views.api_request, kwargs={'api': False}, name='text_api_request'),
    # path('api/text/talmud/<slug:name>/daf=<slug:daf>/', texts.views.api_request, name='text_api_request'),
    path('api/term/<str:term>/', texts.views.api_term, name='text_api_term'),


    # path('admin/', admin.site.urls),
]
from django.conf import settings
if not settings.DEBUG:
    handler404 = 'texts.views.error400'
    handler500 = 'texts.views.error500'