from django.conf.urls import url
import views

urlpatterns = [
    url(r'^section/$', views.HaProxyTestView.as_view()),
    url(r'^section/(?P<pk>\d+)/$', views.HaProxyTestView.as_view())
]
