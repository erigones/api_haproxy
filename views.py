from rest_framework.views import APIView
from models import HaProxyConfigModel
from serializers import HaProxyConfigModelSerializer
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR
from api_core import exceptions as core_exceptions
from django.db import IntegrityError
from operator import methodcaller
import subprocess
import settings
import json


class HaProxyConfigBuildView(APIView):
    """
    API view handling build process of sections in HaProxy configuration.
    """

    def get(self, request, checksum=None):
        """
        Method responding to GET request lists specific configuration section stored in a database whenever
        unique checksum string is provided. Otherwise list of all configuration sections is returned in response.
        :param request: request data
        :param checksum: unique identifier of configuration sections
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
        Method responding to POST request creates new configuration section, validates input and
        stores it in a database.
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


class HaProxyConfigGenerateView(APIView):
    """
    API view handling generation process of HaProxy configuration file.
    """

    def post(self, request):
        """
        Method responding to POST request creates new configuration, which is stored in file specified by
        HAPROXY_CONFIG_PATH defined in settings file specific to api_haproxy.
        :param request: request data
        :return: rest_framework.response.Response containing serialized data
        """
        result = HaProxyConfigModel.objects.all()
        result.query.group_by = ['section', 'section_name']

        if result:
            result = sorted(result, key=methodcaller('get_section_weight'))
            config = ""
            with open(settings.HAPROXY_CONFIG_DEV_PATH, 'w') as f:
                for res in result:
                    config += "{0} {1}\n".format(str(res.section), (res.section_name or ""))
                    for key, value in json.loads(res.configuration).iteritems():
                        config += "    {0} {1}\n".format(str(key), (value or ""))
                    config += "\n"
                f.write(config)

        return Response({'created': True}, status=HTTP_201_CREATED)


class HaProxyConfigValidationView(APIView):
    """
    API view interacting with haproxy cli command to validate generated haproxy configuration file.
    """

    def get(self, request):
        """
        Method calling haproxy command to validate a generated configuration in a location provided by a
        HAPROXY_CONFIG_PATH variable. Validation is performed using command specified in a HAPROXY_VALIDATION_CMD
        variable. All these variables could be specified in settings.py file local to api_haproxy project.
        :param request: request data
        :return: rest_framework.response.Response containing serialized data
        """
        haproxy_executable = getattr(settings, 'HAPROXY_EXECUTABLE', None) or 'haproxy'
        haproxy_validation_cmd = getattr(settings, 'HAPROXY_VALIDATION_CMD', None)

        if not haproxy_validation_cmd:
            haproxy_validation_cmd = '{0} -f {1} -c'.format(haproxy_executable, settings.HAPROXY_CONFIG_DEV_PATH)

        # Exceptions raised in following command are handled in self.handle_exception method
        validate = subprocess.check_output(haproxy_validation_cmd.split(), stderr=subprocess.STDOUT)

        return Response()

    def handle_exception(self, exc):
        """
        Overridden an APIView.handle_exception method to create custom error responses based on exceptions generated by
        execution of commands using a subprocess module.
        :param exc: handled exception
        :return: rest_framework.response.Response containing exception information
        """
        if isinstance(exc, subprocess.CalledProcessError):
            data = {'return code': exc.returncode, 'detail': exc.output}
            return Response(data, status=HTTP_500_INTERNAL_SERVER_ERROR)
        if isinstance(exc, OSError):
            data = {
                'return code': exc.errno,
                'detail': str(exc.strerror) + '. Make sure HAProxy is installed and a path to its binary is correct.'
            }
            return Response(data, status=HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            super(self.__class__, self).handle_exception(exc)
