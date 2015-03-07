from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework import status


class HaProxyConfigBuildTest(APITestCase):

    def test_unamed_section_create_ok(self):
        data = {
            'section': 'global',
            'section_name': None,
            'configuration': '{"user": "haproxy", "group": "haproxy", "daemon": ""}'
        }
        response = self.client.post('/v1/haproxy/section/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unamed_section_create_fail(self):
        data = {
            'section': 'global',
            'section_name': None,
            'configuration': ''
        }
        response = self.client.post('/v1/haproxy/section/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)