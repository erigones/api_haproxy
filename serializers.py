from rest_framework.serializers import ModelSerializer
from models import HaProxyConfigModel


class HaProxyConfigModelSerializer(ModelSerializer):
    """
    ModelSerializer preparing output for responses sent to a client. Objects retrieved from a database using
    HaProxyConfigModel are formatted by this serializer and passed to a Response constructor.
    """

    class Meta:
        model = HaProxyConfigModel
        fields = ('checksum', 'section', 'section_name', 'meta', 'configuration')