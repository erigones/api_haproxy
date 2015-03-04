from django.conf import settings

## General settings
# HaProxy configuration file location
HAPROXY_CONFIG_PATH = settings.BASE_DIR + '/haproxy.cfg'

# Sections in configuration file, which must be named
HAPROXY_CONFIG_NAMED_SECTIONS = ['frontend', 'backend', 'listen']

## Commands used to validate HaProxy configuration
# Specifying this commands introduces a SECURITY HAZARD. Commands will be executed as they are without further control
# and their output will be harvested for later processing. Use carefully or delete/comment these variables. In the
# latter case, api_haproxy will use hardcoded defaults, which are mentioned in comments above specific commands.

# Default: haproxy, this variable expects haproxy binary configured in your PATH environment variable
HAPROXY_EXECUTABLE = 'haproxy'

# Default: haproxy -f PATH_TO_CONFIG -c
HAPROXY_VALIDATION_CMD = '{0} -f {1} -c'.format((HAPROXY_EXECUTABLE or 'haproxy'), HAPROXY_CONFIG_PATH)
