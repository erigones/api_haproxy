from rest_framework.views import APIView
from models import HaProxyConfigModel
from serializers import HaProxyConfigModelSerializer
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from api_core.exceptions import InvalidRequestException, DoesNotExistException, DuplicateEntryException
from django.db import IntegrityError
from operator import methodcaller
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
                raise DoesNotExistException()
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
            raise InvalidRequestException()
        else:
            try:
                json.loads(configuration)  # Should raise ValueError if configuration data are invalid
                config = HaProxyConfigModel(section=section, section_name=section_name, configuration=configuration)
                config.save()
            except IntegrityError:
                raise DuplicateEntryException()
            except ValueError:
                raise InvalidRequestException()

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
            with open(settings.HAPROXY_CONFIG_PATH, 'w') as f:
                for res in result:
                    config += str(res.section) + " " + (res.section_name or "") + "\n"
                    for key, value in json.loads(res.configuration).iteritems():
                        config += "    " + str(key) + " " + (value or "") + "\n"
                    config += "\n"
                f.write(config)

        return Response({'created': True}, status=HTTP_201_CREATED)