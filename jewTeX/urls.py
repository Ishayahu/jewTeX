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
from django.urls import path
from django.conf.urls import url, include
import texts.views

urlpatterns = [
    url(r'^$', texts.views.index, name = 'index'),
    url(r'utils/terms_to_define', texts.views.terms_to_define, name = 'terms_to_define'),
    url(r'utils/need_to_be_done', texts.views.need_to_be_done, name = 'need_to_be_done'),
    url(r'utils/not_translated', texts.views.not_translated, name = 'not_translated'),
    path('<slug:author>/', texts.views.author, name = 'author'),
    path('<slug:author>/<slug:book>/', texts.views.book, name = 'book'),
    # path('open/<slug:author>/<slug:book>/siman=<int:siman>&seif=<int:seif>/', texts.views.open_by_siman_and_seif, name = 'open_by_siman_seif'),
    url(r'open/([^/]+)/([^/]+)/([^/]+)/([^/]+)/$', texts.views.open_text_old, name = 'open'),
    url(r'open/([^/]+)/([^/]+)/([^/]+)/$', texts.views.open_text, name = 'open_from_xml'),
    url(r'api/text/([^/]+)/([^/]+)/([^/]+)/$', texts.views.api_request, name = 'text_api_request'),

    path('admin/', admin.site.urls),
]
