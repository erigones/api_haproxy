from rest_framework.views import APIView
from models import HaProxyConfigModel
from serializers import HaProxyConfigModelSerializer
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from api_core import exceptions as core_exceptions
from django.db import IntegrityError
from django.utils import timezone
from operator import methodcaller
from helpers import parse_haproxy_configtest_output, raise_500_error
from os.path import isfile
import shutil
import subprocess
import settings
import json


class HaProxyConfigBuildView(APIView):
    """
    An API view handling build process of a HAProxy configuration file. Specific configuration directives are posted in
    sections, which are then formatted and stored in a database. Posted sections are versioned with a md5 checksum and
    create time, thus most currently posted section is always used in a final configuration. In a need to use a specific
    older section, method implementing PUT provides similar functionality to an unix touch command, moving touched
    section to top of a selection process.
    """

    def get(self, request, checksum=None):
        """
        Method, responding to a GET request, lists a specific configuration section stored in a database whenever
        an unique checksum string is provided. Otherwise list of all configuration sections is returned in a response.
        :param request: request data
        :param checksum: an unique identifier of a configuration section
        :return: rest_framework.response.Response containing serialized data
        """
        if checksum is not None:
            try:
                config = HaProxyConfigModel.objects.get(checksum=checksum)
                serializer = HaProxyConfigModelSerializer(config)
            except HaProxyConfigModel.DoesNotExist:
                raise core_exceptions.DoesNotExistException()
        else:
            config = HaProxyConfigModel.objects.all()
            serializer = HaProxyConfigModelSerializer(config, many=True)

        return Response(serializer.data)

    def post(self, request):
        """
        Method is responding to a POST request, which in turn creates a new configuration section, after successful pass
        of a input validation. Processed section is stored in a database if it contains correct information.
        :param request: request data
        :return: rest_framework.response.Response containing serialized data
        """
        section = request.DATA.get('section', None)
        section_name = request.DATA.get('section_name', None)
        configuration = request.DATA.get('configuration', None)

        named_sections = settings.HAPROXY_CONFIG_NAMED_SECTIONS
        if section in named_sections and not all([x is not None for x in [section, section_name, configuration]]):
            raise core_exceptions.InvalidRequestException()
        else:
            try:
                json.loads(configuration)  # Should raise ValueError if configuration data are invalid
                config = HaProxyConfigModel(section=section, section_name=section_name, configuration=configuration)
                config.save()
            except IntegrityError:
                raise core_exceptions.DuplicateEntryException()
            except ValueError:
                raise core_exceptions.InvalidRequestException()

        return Response({'checksum': config.checksum}, status=HTTP_201_CREATED)

    def put(self, request, checksum=None):
        """
        Method, responding to a PUT request, modifies existing section, updates its create_time field and sets
        a modify_time key to meta field of a section. Updated section will be selected into configuration file
        generation.
        :param request: request data
        :return: rest_framework.response.Response containing serialized data
        """
        if not checksum:
            raise core_exceptions.InvalidRequestException()

        try:
            config = HaProxyConfigModel.objects.get(checksum=checksum)
            meta = config.meta
            meta[unicode('modify_time')] = unicode(str(timezone.now()))
            HaProxyConfigModel.objects.filter(checksum=checksum).update(meta=json.dumps(meta))
        except HaProxyConfigModel.DoesNotExist:
            raise core_exceptions.DoesNotExistException()

        return Response({'checksum': config.checksum})

    def delete(self, request, checksum=None):
        """
        Method, responding to a DELETE request, deletes existing section.
        :param request: request data
        :return: rest_framework.response.Response containing serialized data
        """
        if not checksum:
            raise core_exceptions.InvalidRequestException()

        try:
            HaProxyConfigModel.objects.filter(checksum=checksum).delete()
        except HaProxyConfigModel.DoesNotExist:
            raise core_exceptions.DoesNotExistException()

        return Response({'deleted': True})

class HaProxyConfigGenerateView(APIView):
    """
    An API view handling generation process of a HAProxy configuration file. The generation process walks through all
    configuration sections stored in a database. Only newest one of each unique section type is retrieved from a
    database and passed to a next step. Uniqueness of a section type is guaranteed by a combination of a section and
    section name. The next step constructs a sorted list containing these selected objects, which represent specific
    configuration blocks, and based on an used request method either sends them in response or write them to a file.
    Sections will be sorted as follows: global, defaults, defaults(named), frontend, backend, listen
    """

    def get(self, request):
        """
        Method, responding to a GET request, fetches most currently posted sections of every type. Fetched sections are
        send serialized in a response to a client, thus providing preview of a final configuration.
        :param request: request data
        :return: rest_framework.response.Response containing serialized data
        """
        result = HaProxyConfigModel.objects.all()
        result.query.group_by = ['section', 'section_name']

        if not result:
            raise core_exceptions.DoesNotExistException()

        result = sorted(result, key=methodcaller('get_section_weight'))
        serializer = HaProxyConfigModelSerializer(result, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Method, responding to a POST request, creates a new configuration, which is stored in a file specified by
        the HAPROXY_CONFIG_PATH variable defined in a settings file specific to a api_haproxy application. Objects from
        a database are retrieved with a same logic as in the HaProxyConfigGenerateView.get method and formatted into a
        representation valid for a HAProxy configuration.
        :param request: request data
        :return: rest_framework.response.Response containing serialized data
        """
        result = HaProxyConfigModel.objects.all()
        result.query.group_by = ['section', 'section_name']

        if not result:
            raise core_exceptions.DoesNotExistException()

        result = sorted(result, key=methodcaller('get_section_weight'))
        config = ""
        try:
            with open(settings.HAPROXY_CONFIG_DEV_PATH, 'w') as f:
                for res in result:
                    config += "{0} {1}\n".format(str(res.section), (res.section_name or ""))
                    for key, value in res.configuration.iteritems():
                        config += "    {0} {1}\n".format(str(key), (value or ""))
                    config += "\n"
                f.write(config)
        except IOError as e:
            raise_500_error(e.errno, e.strerror + settings.HAPROXY_CONFIG_DEV_PATH)

        return Response({'created': True}, status=HTTP_201_CREATED)


class HaProxyConfigValidationView(APIView):
    """
    An API view interacting with 'haproxy' command utility to validate a previously generated HAProxy configuration
    file. Validation process tries to load path to a file and command to be executed from a settings file. In the case,
    when there are no such settings available, the process uses hardcoded defaults. At the end of a process, an output
    from a validation is parsed and sent to a client.
    """

    def get(self, request):
        """
        Method is calling 'haproxy' command to validate newly generated configuration in a location provided by the
        HAPROXY_CONFIG_DEV_PATH variable. This method expects previous run of a generation method. Validation is
        performed by a command specified in the HAPROXY_VALIDATION_CMD variable, which output is then parsed and sent to
        a client requesting validation check.
        :param request: request data
        :return: rest_framework.response.Response containing serialized data
        """
        haproxy_executable = getattr(settings, 'HAPROXY_EXECUTABLE', None) or 'haproxy'
        haproxy_validation_cmd = getattr(settings, 'HAPROXY_VALIDATION_CMD', None)
        haproxy_dev_conf = settings.HAPROXY_CONFIG_DEV_PATH

        if not haproxy_validation_cmd:
            haproxy_validation_cmd = '{0} -f {1} -c'.format(haproxy_executable, haproxy_dev_conf)

        if not isfile(haproxy_dev_conf):
            raise core_exceptions.DoesNotExistException(detail='{} is not a file.'.format(haproxy_dev_conf))

        validate = 'There has been no output so far.'
        try:
            validate = subprocess.check_output(haproxy_validation_cmd.split(), stderr=subprocess.STDOUT)
        # Exception is caught when an executed command returns a non zero code
        except subprocess.CalledProcessError as e:
            raise_500_error(e.returncode, parse_haproxy_configtest_output(e.output))

        # Exception is caught when no executable is found
        except OSError as e:
            err_message = str(e.strerror) + '. Make sure HAProxy is installed and a path to its binary is correct.'
            raise_500_error(e.errno, err_message)

        validate_output = parse_haproxy_configtest_output(validate)
        return Response({'return code': 0, 'detail': validate_output})


class HaProxyConfigDeployView(APIView):
    """
    An API view interacting with 'haproxy' command to deploy new configuration and reload a HAProxy daemon. This
    process tries to load commands as well as paths to configuration files from a settings.py file. In the case, when
    there are no such settings available, the process uses hardcoded defaults. At the end, production configuration file
    is backed up and replaced with a development configuration file, followed by a restart or reload of a daemon.
    """

    def post(self, request):
        """
        Method is calling 'haproxy' command to deploy specified configuration file and reload a HAProxy daemon.
        Production file listed in the HAPROXY_CONFIG_PATH variable is replaced with a file listed in the
        HAPROXY_CONFIG_DEV_PATH variable, the one generated with a HaProxyConfigGenerateView. Replaced production file
        is renamed to same name, but ends with a .bak extension. After files are switched, method calls 'haproxy'
        command and attempts to reload configuration, expecting that bash is present, otherwise restart will be
        performed. It is not recommended to run this method before previous validation run.
        :param request: request data
        :return: rest_framework.response.Response containing serialized data
        """
        haproxy_executable = getattr(settings, 'HAPROXY_EXECUTABLE', None) or 'haproxy'
        haproxy_reload_cmd = getattr(settings, 'HAPROXY_RELOAD_CMD', None)
        haproxy_restart_cmd = getattr(settings, 'HAPROXY_RESTART_CMD', None)
        haproxy_dev_config = settings.HAPROXY_CONFIG_DEV_PATH
        haproxy_prod_config = settings.HAPROXY_CONFIG_PATH

        # Check if executables are specified in settings, otherwise provide defaults
        if getattr(settings, 'BASH_PATH', None):
            if not haproxy_reload_cmd:
                haproxy_reload_cmd = '{0} -f {1} -p {2} -sf $(<{2})'.format(
                    haproxy_executable, haproxy_prod_config, '/var/run/haproxy-pids.pid'
                )
            haproxy_reload = [settings.BASH_PATH, '-c', haproxy_reload_cmd]
        else:
            if not haproxy_restart_cmd:
                haproxy_restart_cmd = '/etc/init.d/haproxy restart'
            haproxy_reload = haproxy_restart_cmd.split()

        # Check if configs are in place
        if not isfile(haproxy_dev_config):
            raise core_exceptions.DoesNotExistException(
                detail='{} is not a file. Run call to generate it first.'.format(haproxy_dev_config)
            )
        if not isfile(haproxy_prod_config):
            raise core_exceptions.DoesNotExistException(detail='{} is not a file.'.format(haproxy_prod_config))

        deploy = 'There has been no output so far.'
        try:
            shutil.copy(haproxy_prod_config, haproxy_prod_config + '.bak')
            shutil.copy(haproxy_dev_config, haproxy_prod_config)
            deploy = subprocess.Popen(haproxy_reload, stdin=None, stdout=None, stderr=None)
        except subprocess.CalledProcessError as e:
            raise_500_error(e.returncode, parse_haproxy_configtest_output(e.output))

        except OSError as e:
            err_message = str(e.strerror) + '. Make sure HAProxy is installed and a path to its binary is correct.'
            raise_500_error(e.errno, err_message)

        return Response({'return code': 0})
