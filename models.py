from django.db import models
from hashlib import md5
from fields import Base64JsonField
from django.utils import timezone


class HaProxyConfigModel(models.Model):
    """
    Model is intended to store a serialized configuration of a HAProxy loadbalancer software. Stored data are divided
    per section, e.g. frontend, backend, defaults and so on. These data provide two types of information. First are
    columns with metadata like a checksum (used as id as well as unique identifier), create time and a meta column,
    which could be customized to store information like, who posted a specific configuration block or so.
    Second, there are columns containing configuration, these columns are section, section name and configuration.
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
        Method enhances a default models.Model.save method to store a configuration checksum for later processing
        like writes or check of an integrity during saves to a database.
        """
        checksum = md5()
        checksum.update(self.section + (self.section_name or '') + self.configuration)
        self.checksum = checksum.hexdigest()
        self.meta = self.generate_meta()
        super(HaProxyConfigModel, self).save(*args, **kwargs)

    def generate_meta(self):
        """
        Method generates metadata for every submitted entry to a database. This is place, where additional information
        should be defined if needed.
        :return: list of metadata for an entry
        """
        meta = {
            'create_time': str(timezone.now()),
        }
        return meta

    def get_section_weight(self):
        """
        Method returns weights of sections for later processing. This method is handy during generation or preview of a
        configuration file. Sections are numbered to appear in a following order:
        global, defaults, defaults(named), frontend, backend, listen
        :return: weight of a specific section
        """
        weights = {'global': 1, 'defaults': 3, 'frontend': 5, 'backend': 7, 'listen': 9}
        if self.section in weights:
            weight = weights.get(str(self.section), 0)
            if self.section_name:
                return weight + 1
            return weight