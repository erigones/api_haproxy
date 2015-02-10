from rest_framework.views import APIView
from models import HaProxyConfigModel
from serializers import HaProxyConfigModelSerializer
from rest_framework.response import Response
from api_core.exceptions import InvalidRequestException


class TestView(APIView):

    def get(self, request, format=None):
        return Response({'Result': 'Hello tester!'})


class HaProxyTestView(APIView):

    def get(self, request, format=None):
        configs = HaProxyConfigModel.objects.all()
        serializer = HaProxyConfigModelSerializer(configs, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        section = request.DATA.get('section', None)
        configuration = request.DATA.get('configuration', None)

        if not section or not configuration:
            raise InvalidRequestException()

        return Response({'status': 'ok'})

