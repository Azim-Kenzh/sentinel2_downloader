import unittest
from unittest.mock import patch, Mock
from sentinel2_downloader import SentinelAPI


class TestSentinelAPI(unittest.TestCase):
    @patch('requests.post')
    def setUp(self, mock_post):
        # Создаем фиктивный ответ от сервера для токена
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_response
        self.api = SentinelAPI('username', 'password')

    @patch('requests.get')
    def test_query(self, mock_get):
        # Создаем фиктивный ответ от сервера для запроса
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'value': ['test_product']}
        mock_get.return_value = mock_response

        products = self.api.query('footprint', 'start_date', 'end_date', 'product_type', 'cloud_cover_percentage',
                                  'platform_name')
        self.assertEqual(products, ['test_product'])

    @patch('requests.get')
    @patch('requests.Session')
    def test_download(self, mock_session, mock_get):
        # Создаем фиктивные ответы от сервера для загрузки
        mock_response_query = Mock()
        mock_response_query.raise_for_status.return_value = None
        mock_response_query.json.return_value = {'value': [{'Id': 'product_id', 'Name': 'product_name'}]}
        mock_get.return_value = mock_response_query

        mock_response_download = Mock()
        mock_response_download.status_code = 200
        mock_response_download.content = b'test_content'
        mock_session_instance = mock_session.return_value
        mock_session_instance.get.return_value = mock_response_download

        self.api.query('footprint', 'start_date', 'end_date', 'product_type', 'cloud_cover_percentage', 'platform_name')
        self.api.download('product_id', 'directory_path')

        mock_session_instance.get.assert_called_with(
            'https://catalogue.dataspace.copernicus.eu/odata/v1/Products(product_id)/$value', allow_redirects=False)
        with open('directory_path/product_name.zip', 'rb') as f:
            self.assertEqual(f.read(), b'test_content')


if __name__ == '__main__':
    unittest.main()
