from django.db import models
from hashlib import md5
from fields import Base64JsonField
from django.utils import timezone


class HaProxyConfigModel(models.Model):
    """
    Model storing serialized configuration of HaProxy divided per section in Base64 format. E.g. frontend, backend.
    """
    db_table = 'haproxy_config'
    checksum = models.CharField(max_length=32, unique=True)
    section = models.CharField(max_length=100)
    section_name = models.CharField(max_length=100, null=True)
    meta = Base64JsonField()
    configuration = Base64JsonField()
    create_time = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Enhances default models.Model.save method to store a configuration checksum for later processing
        like writes or check of integrity during saves.
        """
        checksum = md5()
        checksum.update(self.section + (self.section_name or '') + self.configuration)
        self.checksum = checksum.hexdigest()
        self.meta = self.generate_meta()
        super(HaProxyConfigModel, self).save(*args, **kwargs)

    def generate_meta(self):
        """
        Method generates metadata for every submitted entry to database.
        :return: list of metadata for entry
        """
        meta = {
            'create_time': str(timezone.now()),
        }
        return meta