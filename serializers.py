from rest_framework.serializers import ModelSerializer, CharField
from models import HaProxyConfigModel


class HaProxyConfigModelSerializer(ModelSerializer):

    class Meta:
        model = HaProxyConfigModel
        fields = ('checksum', 'section', 'section_name', 'meta', 'configuration')