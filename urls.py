from django.conf.urls import url
import views

urlpatterns = [
    url(r'^section/$', views.HaProxyConfigBuildView.as_view()),
    url(r'^section/(?P<checksum>\w+)/$', views.HaProxyConfigBuildView.as_view()),
    url(r'^configuration/generate/$', views.HaProxyConfigGenerateView.as_view()),
    url(r'^configuration/validate/$', views.HaProxyConfigValidationView.as_view()),
    url(r'^configuration/deploy/$', views.HaProxyConfigDeployView.as_view())
]
