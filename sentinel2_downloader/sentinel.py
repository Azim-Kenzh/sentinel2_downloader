import os
import time

import requests
from tqdm import tqdm


class SentinelAPI:
    def __init__(self, username, password, api_url='https://catalogue.dataspace.copernicus.eu/odata/v1/Products'):
        """Initializes the SentinelAPI instance.
        Args:
            username (str): The username for authentication.
            password (str): The password for authentication.
            api_url (str, optional): The API URL for accessing Sentinel data. Default is the Copernicus API URL.

        Raises:
            Exception: If token creation fails or the response from the server is not successful.
        """
        self.api_url = api_url
        if username and password:
            data = {
                "client_id": "cdse-public",
                "username": username,
                "password": password,
                "grant_type": "password",
            }
            try:
                response_token = requests.post(
                    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
                    data=data)
                response_token.raise_for_status()
                self.token = response_token.json()
            except Exception as e:
                raise Exception(
                    f"Keycloak token creation failed. Response from the server was: {response_token.json()}"
                )

    def query(self, footprint: str, start_date: str, end_date: str, product_type: str, cloud_cover_percentage: str,
              platform_name: str):
        """ Queries the Sentinel data based on the provided parameters.
        Args:
            footprint (str): The footprint to define the geographic area of interest.
                It should be in Well-Known Text (WKT) format.
                Example: 'POLYGON((longitude1 latitude1, longitude2 latitude2, longitude3 latitude3, ...))'
            start_date (str): The start date of the data acquisition period.
            end_date (str): The end date of the data acquisition period.
            product_type (str): The type of Sentinel product to query.
            cloud_cover_percentage (str): The maximum cloud cover percentage allowed.
            platform_name (str): The name of the Sentinel platform.

        Returns:
            dict: The JSON response containing the queried products.

        Raises:
            Exception: If any of the required parameters is missing.
        """

        if footprint and start_date and end_date and platform_name and cloud_cover_percentage and product_type:
            params = {
                '$filter': f"""OData.CSC.Intersects(area=geography'SRID=4326;{footprint}')
                            and ContentDate/Start gt {start_date}T00:00:00.000Z and
                            ContentDate/Start lt {end_date}T00:00:00.000Z and
                            Collection/Name eq '{platform_name}' and
                            Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and
                            att/OData.CSC.DoubleAttribute/Value lt {cloud_cover_percentage}) and 
                            contains(Name,'{product_type}')""",
                '$orderby': 'ContentDate/Start'
            }
            url = self.api_url
            response = requests.get(url, params=params)
            if response.status_code == 200:
                for product in response.json()['value']:
                    if product['Online']:
                        self.product_name = response.json()['value']
                        return response.json()['value']
            else:
                return None
        else:
            raise Exception("parameter 'year or land_type' is required")

    def download(self, product_id, directory_path):
        """Downloads the Sentinel product with the specified product ID.
            Args:
                product_id (str, optional): The ID of the product to download.
                    If not provided, downloads the last queried product.
                directory_path (str, optional): The directory path to save the downloaded product.
                    Default is the current directory.
            Raises:
                requests.exceptions.RequestException: If the download fails or the status code is not 200.
        """
        headers = {'Authorization': f'Bearer {self.token["access_token"]}'}
        product_list = self.product_name
        product_name = [p for p in product_list if p['Id'] == f'{product_id}'][0]['Name']
        url = self.api_url
        try:
            session = requests.Session()
            session.headers.update(headers)
            response_download = session.get(f"{url}({product_id})/$value", allow_redirects=False)
            while response_download.status_code in (301, 302, 303, 307):
                url = response_download.headers['Location']
                response_download = session.get(url, allow_redirects=False)
            response_download = session.get(url, verify=False, allow_redirects=True)

            if response_download.status_code == 200:
                final_directory = os.path.abspath(directory_path)
                os.makedirs(final_directory, exist_ok=True)

                file_path = os.path.join(final_directory, f"{product_name}.zip")
                total_size = int(response_download.headers.get('content-length', 0))

                with open(file_path, 'wb') as f, tqdm(
                        desc=f"Downloading {product_name}:",
                        total=total_size,
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024,
                        dynamic_ncols=True) as progress_bar:
                    downloaded_size = 0
                    block_size = 1024
                    start_time = time.time()

                    for data in response_download.iter_content(block_size):
                        downloaded_size += len(data)
                        f.write(data)
                        progress_bar.update(len(data))

                    elapsed_time = time.time() - start_time
                    speed = (downloaded_size / elapsed_time) / 1024 if elapsed_time > 0 else 0
                    progress_bar.set_postfix(speed=f"{speed:.2f} kB/s", elapsed=f"{elapsed_time:.2f} s")
                    progress_bar.close()

                print("Download complete!")
            else:
                raise requests.exceptions.RequestException("Status code is not 200")
        except Exception as e:
            raise requests.exceptions.RequestException(e)
