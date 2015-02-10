from django.db import models
from hashlib import md5
import json
import base64


class Base64JsonField(models.TextField):
    """
    Base64JsonField is custom field purposed to store json data in base64 format to text column
    in relational databases.
    """
    __metaclass__ = models.SubfieldBase

    def get_prep_value(self, value):
        """
        Encodes json data into base64 when preparing data for write to a database.
        :param value: data to be serialized first to json, then to base64
        :return: base64 encoded data
        """
        if value is not None:
            return 'base64:' + base64.encodestring(json.dumps(value))

    def to_python(self, value):
        """
        Decodes base64 json serialized data.
        Method is called when data are gathered from the database as well as when the class is instantiated
        thus there is need to prepend a string with a prefix and check it to prevent decoding common string.
        :param value: serialized data from database
        :return: json data
        """
        if value is not None and isinstance(value, basestring):
            value = str(value)
            if value.startswith('base64:'):
                value = value.split(':')[1]
                return json.loads(base64.decodestring(value))
        elif value is not None and isinstance(value, dict):
            value = json.dumps(value)
            return value

        return value


class HaProxyConfigModel(models.Model):
    checksum = models.CharField(max_length=32)
    section = models.CharField(max_length=100)
    meta = Base64JsonField()
    configuration = Base64JsonField()

    def save(self, *args, **kwargs):
        """
        Enhances default models.Model.save method to store a configuration checksum for later processing
        like writes or check of integrity during saves.
        """
        checksum = md5()
        checksum.update(self.configuration)
        self.checksum = checksum.hexdigest()
        super(HaProxyConfigModel, self).save(*args, **kwargs)
