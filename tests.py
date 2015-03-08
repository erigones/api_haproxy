from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework import status


class HaProxyConfigBuildTest(APITestCase):
    base_url = '/{}/haproxy/section/'.format(settings.API_VERSION_PREFIX)
    data = {
        'section': 'global',
        'section_name': None,
        'configuration': '{"user": "haproxy", "group": "haproxy", "daemon": ""}'
    }
    non_existing_id = '1ab2cd3ef4gh/'

    def test_unnamed_section_create_ok(self):
        local_data = self.data.copy()
        response = self.client.post(self.base_url, local_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unnamed_section_create_fail(self):
        local_data = self.data.copy()
        local_data['configuration'] = ''
        response = self.client.post(self.base_url, local_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_named_section_create_ok(self):
        local_data = self.data.copy()
        local_data['section'] = 'frontend'
        local_data['section_name'] = 'nodes'
        response = self.client.post(self.base_url, local_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_named_section_create_fail(self):
        local_data = self.data.copy()
        local_data['section'] = 'frontend'
        response = self.client.post(self.base_url, local_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_section_create_fail(self):
        local_data = self.data.copy()
        response = self.client.post(self.base_url, local_data)
        response = self.client.post(self.base_url, local_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_existing_section_update_ok(self):
        local_data = self.data.copy()
        response = self.client.post(self.base_url, local_data)
        response = self.client.put(self.base_url + response.data.get('checksum') + '/', local_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_existing_section_update_fail(self):
        local_data = self.data.copy()
        response = self.client.post(self.base_url, local_data)
        response = self.client.put(self.base_url + self.non_existing_id, local_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_specific_section_ok(self):
        response = self.client.post(self.base_url, self.data)
        section_id = response.data.get('checksum') + '/'
        response = self.client.get(self.base_url + section_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_specific_section_not_found(self):
        response = self.client.get(self.base_url + self.non_existing_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_all_sections_ok(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)