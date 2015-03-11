from django.conf import settings

## General settings
# HaProxy configuration file location
HAPROXY_CONFIG_PATH = '/etc/haproxy/haproxy.cfg'

# Path to developed configuration. This file replaces one specified in HAPROXY_CONFIG_PATH when changes are deployed
HAPROXY_CONFIG_DEV_PATH = settings.BASE_DIR + '/haproxy.cfg'

# Sections in configuration file, which must be named
HAPROXY_CONFIG_NAMED_SECTIONS = ['frontend', 'backend', 'listen']

# Strings to be ignored from haproxy command outputs
HAPROXY_BLACKLISTED_OUTPUT = [
    'Fatal errors found in configuration.',
    'Error(s) found in configuration file',
    'Configuration file is valid'
]

# Path to bash is needed for graceful reloading, when left blank, restart will be performed on haproxy instead.
BASH_PATH = '/bin/bash'

# Path to file, where pids of processes will be stored during reload
HAPROXY_PID_FILE_PATH = '/var/run/haproxy-procs.pid'

## Commands used to validate HaProxy configuration
# Specifying this commands introduces a SECURITY HAZARD. Commands will be executed as they are without further control
# and their output will be harvested for later processing. Use carefully or delete/comment these variables. In the
# latter case, api_haproxy will use hardcoded defaults, which are mentioned in comments above specific commands.

# Default: haproxy, this variable expects haproxy binary configured in your PATH environment variable
HAPROXY_EXECUTABLE = 'haproxy'

# Default: haproxy -f PATH_TO_CONFIG -c
HAPROXY_VALIDATION_CMD = '{0} -f {1} -c'.format((HAPROXY_EXECUTABLE or 'haproxy'), HAPROXY_CONFIG_DEV_PATH)

# Default: /bin/bash -c haproxy -f PATH_TO_CONFIG -f /var/run/haproxy.pid -sf $(</var/run/haproxy.pid)
# This command will be performed only if bash is present on a system
HAPROXY_RELOAD_CMD = '{0} -f {1} -p {2} -sf $(<{2})'.format(
    (HAPROXY_EXECUTABLE or 'haproxy'), HAPROXY_CONFIG_PATH, HAPROXY_PID_FILE_PATH
)

# Default: /etc/init.d/haproxy
HAPROXY_RESTART_CMD = '/etc/init.d/haproxy restart'