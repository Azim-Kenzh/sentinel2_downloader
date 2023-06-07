import requests


class SentinelAPI:
    def __init__(self, username, password, api_url='https://catalogue.dataspace.copernicus.eu/odata/v1/Products'):
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

    def query(self, footprint: str,
              start_date: str,
              end_date: str,
              product_type: str,
              cloud_cover_percentage: str,
              platform_name: str):
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

    def download(self, product_id=None, directory_path='.'):
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
                with open(f"{directory_path}/{product_name}.zip", 'wb') as f:
                    f.write(response_download.content)
            else:
                raise requests.exceptions.RequestException("Status code is not 200")
        except Exception as e:
            raise requests.exceptions.RequestException(e)
