from rest_framework.views import APIView
from models import HaProxyConfigModel
from serializers import HaProxyConfigModelSerializer
from rest_framework.response import Response
from api_core.exceptions import InvalidRequestException, DoesNotExistException, DuplicateEntryException
from django.db import IntegrityError


class HaProxyTestView(APIView):

    def get(self, request, pk=None, format=None):
        if pk is not None:
            try:
                config = HaProxyConfigModel.objects.get(pk=pk)
                serializer = HaProxyConfigModelSerializer(config)
            except HaProxyConfigModel.DoesNotExist:
                raise DoesNotExistException()
        else:
            config = HaProxyConfigModel.objects.all()
            serializer = HaProxyConfigModelSerializer(config, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        section = request.DATA.get('section', None)
        section_name = request.DATA.get('section_name', None)
        configuration = request.DATA.get('configuration', None)

        named_sections = ['frontend', 'backend', 'listen']
        if section in named_sections and not all([x is not None for x in [section, section_name, configuration]]):
            raise InvalidRequestException()
        else:
            try:
                config = HaProxyConfigModel(section=section, section_name=section_name, configuration=configuration)
                config.save()
            except IntegrityError:
                raise DuplicateEntryException()

        return Response({'status': 'ok'})

