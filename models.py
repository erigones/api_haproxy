from django.db import models
import json
import base64


class Base64JsonField(models.TextField):
    """
    Base64JsonField is custom field purposed to store json data in base64 format to text column.
    """
    __metaclass__ = models.SubfieldBase

    def get_prep_value(self, value):
        if value is not None:
            return 'base64:' + base64.encodestring(json.dumps(value))

    def to_python(self, value):
        # This method is called when data are gathered from the database as well as when the class is instantiated
        # thus there is need to prepend a string with a prefix and check it to prevent decoding common string
        if value is not None and isinstance(value, basestring):
            value = str(value)
            if value.startswith('base64:'):
                value = value.split(':')[1]
                return json.loads(base64.decodestring(value))
            else:
                return value


class HaProxyConfigModel(models.Model):
    checksum = models.CharField(max_length=32)
    section = models.CharField(max_length=100)
    meta = Base64JsonField()
    configuration = Base64JsonField()