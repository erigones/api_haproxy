from django.db import models
import json
import base64


class Base64JsonField(models.TextField):
    """
    Base64JsonField is a custom field intended to store a JSON data in a Base64 format to a text column in relational
    databases. Stored data are first serialized into a JSON string representation and then encoded into a Base64 format.
    When retrieving this data, same logic is applied in a reverse order.
    """
    __metaclass__ = models.SubfieldBase

    def get_prep_value(self, value):
        """
        Encodes JSON data into a Base64 format, when preparing them to be written to a database.
        :param value: data to be serialized and stored
        :return: Base64 string
        """
        if value is not None:
            return 'base64:' + base64.encodestring(json.dumps(value))

    def to_python(self, value):
        """
        Decodes Base64 serialized JSON data. This method is called when data are gathered from a database as well as
        when this class is instantiated, introducing need to differ a passed in value due to later processing.
        Distinction is accomplished by appending of a 'base64:' prefix before encoded data.
        :param value: serialized data from database
        :return: JSON data
        """
        if value is not None and isinstance(value, basestring):
            value = str(value)
            if value.startswith('base64:'):
                value = value.split(':')[1]
                prepared_data = json.loads(base64.decodestring(value))
                return json.loads(prepared_data)
        elif value is not None and isinstance(value, dict):
            value = json.dumps(value)
            return value

        return value