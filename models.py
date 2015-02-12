from django.db import models
from hashlib import md5
from fields import Base64JsonField


class HaProxyConfigModel(models.Model):
    checksum = models.CharField(max_length=32)
    section = models.CharField(max_length=100)
    section_name = models.CharField(max_length=100)
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
