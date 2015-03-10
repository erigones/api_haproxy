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


class HaProxyConfigTest(APITestCase):
    base_url = '/{}/haproxy'.format(settings.API_VERSION_PREFIX)
    sections_url = '{}/section/'.format(base_url)
    generate_url = '{}/configuration/generate/'.format(base_url)
    validate_url = '{}/configuration/validate/'.format(base_url)
    posts = [
        {'section': 'global', 'section_name': None, 'configuration': '{"user": "haproxy", "group": "haproxy"}'},
        {'section': 'defaults', 'section_name': None, 'configuration': '{"log": "global", "mode": "http"}'},
        {'section': 'frontend', 'section_name': 'nodes', 'configuration': '{"bind": "*:80", "default_backend": "bak"}'},
        {'section': 'backend', 'section_name': 'bak', 'configuration': '{"balance": "roundrobin", "server": "1.1.1.1"}'}
    ]

    def test_config_generation_ok(self):
        for section in self.posts:
            self.client.post(self.sections_url, section)

        response = self.client.post(self.generate_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_config_generation_fail(self):
        response = self.client.post(self.generate_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_config_preview_ok(self):
        for section in self.posts:
            self.client.post(self.sections_url, section)
        response = self.client.get(self.generate_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_config_preview_fail(self):
        response = self.client.get(self.generate_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_config_generation_file_open_fail(self):
        with self.settings(HAPROXY_CONFIG_DEV_PATH='/root/no/permissions/to/access'):
            response = self.client.get(self.validate_url)
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_config_validation_executable_not_found(self):
        with self.settings(HAPROXY_EXECUTABLE='non-existing'):
            response = self.client.get(self.validate_url)
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)



