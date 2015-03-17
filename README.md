api\_haproxy
========

Introduction
------

This Django application covers build, generation, validation and deployment processes of a HAProxy configuration file
lifecycle with common API calls. Project is developed as part of a Bachelor's thesis about NFV. Application uses
exceptions from the [api\_core](https://github.com/erigones/api_core ) submodule. Authentication introduced in api\_core 
may be used as well. See section [<b>Deploying with authentication</b>](https://github.com/erigones/api_haproxy#deploying) 
below for more details.

You may want to use whole Django project implementing this application instead. You can find it at 
[eszone\_haproxy](https://github.com/erigones/eszone_haproxy) repository.  

A typical use case may include this module in a Django project placed within a HAProxy virtual machine template 
labeling it a 'loadbalancer'. With the created template you can spawn virtual machines for your customers and then 
provide them with ways to configure it as they demand later on without need to access virtual machine using ssh. 

Installation
------

1. Submodule this application and api\_core into your Django project

   `git submodule add *repository-link*`

2. Append 'api\_haproxy' and 'api\_core' to INSTALLED_APPS in your Django project settings

3. Route submodules in urls.py in your Django project settings

```python
    url(r'^my-url-auth/', include('api_core.urls')),
    url(r'^my-url/', include('api_haproxy.urls')),
```

Running API
------

For testing and development purposes, running API with web server shipped in Django is fine enough. For production 
though, you may want to consider some production ready web server like uwsgi or gunicorn. Deploying Django application 
within one of these web servers is a matter of pointing to a wsgi.py file, which should be contained in your project's 
directory. In order how to configure these servers you can start reading following Django documentation pages:

[Deploying Django application using uwsgi](https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/uwsgi/)

[Deploying Django application using gunicorn](https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/gunicorn/)

Interacting with API
------

API is intended to be used by custom API client or tool incorporated into your dashboard. For testing and development 
purposes python-httpie package can help a bit. Install it with:

`pip install httpie`

Then you can interact with API:

`http POST http://${IP}:${PORT}/v1/haproxy/section/ section='global' configuration='{"daemon": "", "user": "www-data", "group": "www-data"}'`
`http GET http://${IP}:${PORT}/v1/haproxy/section/`
`http GET http://${IP}:${PORT}/v1/haproxy/configuration/generate/`
`http POST http://${IP}:${PORT}/v1/haproxy/configuration/generate/`
`http GET http://${IP}:${PORT}/v1/haproxy/configuration/validate/`
`http POST http://${IP}:${PORT}/v1/haproxy/configuration/deploy/`

Deploying with authentication
------

Currently, authentication from api\_core application is not integrated into api\_haproxy application. If you plan to
use api\_haproxy in a private network behind NAT and firewalls, there is probably no need to have authentication 
enabled at all. On the other hand, if you plan to do so, here are steps to make it work:

- submodule api\_core into your Django project

`git submodule add *repository-link*`

- import permissions and authentication modules by adding following lines to the top of views.py file

```python
    from rest_framework.permissions import IsAuthenticated
    from api_core.authentication import SimpleTokenAuthentication
```

- add permissions and authentication classes as attributes to each APIView you want to authenticate. For example:

```python
    class TestAuthView(APIView):
        authentication_classes = (SimpleTokenAuthentication, )
        permission_classes = (IsAuthenticated, )
```

From now on you can make HTTP requests with an authentication.token field in them, assuming you have created first token 
by hand.

- generation of master token is accessible after running `python manage.py migrate` and submoduling an api\_core app.

`python manage.py shell`

```python
    from api_core.models import SimpleTokenAuthModel
    token = SimpleTokenAuthModel()
    token.save()
    print token.token_uuid
```

Todo
------

- Finish this README
- Rework and use comments with Python sphinx module to make documentation
- Refactor views.py and settings.py to implement option 'enable authentication' from api\_core submodule
- Always refactor to make code better