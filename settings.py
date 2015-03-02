from django.conf import settings

# HaProxy configuration file location
HAPROXY_CONFIG_PATH = settings.BASE_DIR + 'haproxy.cfg'

# Sections in configuration file, which must be named
HAPROXY_CONFIG_NAMED_SECTIONS = ['frontend', 'backend', 'listen']