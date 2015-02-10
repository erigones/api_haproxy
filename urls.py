from django.conf.urls import url
import views

urlpatterns = [
    url(r'^test/$', views.TestView.as_view()),
    url(r'^haproxy/$', views.HaProxyTestView.as_view())
]
