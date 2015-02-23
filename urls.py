from django.conf.urls import url
import views

urlpatterns = [
    url(r'^section/$', views.HaProxyConfigBuildView.as_view()),
    url(r'^section/(?P<checksum>\w+)/$', views.HaProxyConfigBuildView.as_view()),
    url(r'^configuration/$', views.HaProxyConfigGenerateView.as_view())
]
