import os
import time
import logging
from decouple import config
from tqdm import tqdm
import pandas as pd

import requests
from abc import ABC, abstractmethod


class IApiClient(ABC):
    @abstractmethod
    def authorize(self) -> str:
        pass


class ApiClient(IApiClient):
    def __init__(self, username: str, password: str) -> None:
        self.USERNAME = username
        self.PASSWORD = password

    def authorize(self) -> str:
        data = {
            "client_id": "cdse-public",
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "grant_type": "password",
        }
        try:
            r = requests.post(
                "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
                data=data,
            )
            r.raise_for_status()
        except Exception as e:
            raise Exception(f"Access token creation failed: {e}")

        return r.json()["access_token"]


class IDownloaderService(ABC):
    @abstractmethod
    def set_config(
        self,
        start_date: str,
        end_date: str,
        data_collection: str,
        aoi: str,
        cloud_cover_percentage: int,
    ) -> None:
        pass

    @abstractmethod
    def download_product(self, token: str, product_id: str) -> None:
        pass

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def create_url_process(self) -> str:
        pass

    @abstractmethod
    def get_products(self, url: str) -> pd.DataFrame:
        pass


class Sentinel2Downloader(IDownloaderService):
    def __init__(self, client: ApiClient):
        """
        Initialize the Sentinel2Downloader with an ApiClient instance.

        :param client: ApiClient
            An instance of ApiClient used for authentication.
        """
        self.client = client

    def set_config(
        self,
        start_date: str,
        end_date: str,
        data_collection: str,
        aoi: str,
        cloud_cover_percentage: int,
        product_type: str,
        download_path: str,
    ) -> None:
        """
        Set configuration parameters for the Sentinel-2 downloader.

        :param start_date: str
            Start date for the data collection period.
        :param end_date: str
            End date for the data collection period.
        :param data_collection: str
            Name of the data collection to filter.
        :param aoi: str
            Area of interest (AOI) in a specific format.
        :param cloud_cover_percentage: int
            Maximum cloud cover percentage for filtering.
        :param product_type: str
            Type of dataspace picture: for example (L2M, MSIL1C)
        """
        self.start_date = start_date
        self.end_date = end_date
        self.data_collection = data_collection
        self.aoi = aoi
        self.cloud_cover_percentage = cloud_cover_percentage
        self.product_type = product_type
        self.download_path = download_path

    def create_url_process(self) -> str:
        """
        Create a URL for querying Sentinel-2 products based on configuration.

        :return: str
            The generated query URL.
        """
        url = f"""https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{self.data_collection}' and OData.CSC.Intersects(area=geography'SRID=4326;{self.aoi}) and ContentDate/Start gt {self.start_date}T00:00:00.000Z and ContentDate/Start lt {self.end_date}T00:00:00.000Z and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {self.cloud_cover_percentage}) and contains(Name,'{self.product_type}')"""
        return url

    def get_products(self, url) -> pd.DataFrame:
        """
        Get a DataFrame of Sentinel-2 products from a query URL.

        :param url: str
            The query URL to fetch products.
        :return: pd.DataFrame
            A DataFrame containing product information.
        """
        json = requests.get(url).json()
        dt = pd.DataFrame.from_dict(json["value"]).head(5)
        print(dt)
        return dt

    def download_product(self, token: str, product_id: int) -> None:
        """
        Download product of Sentinel-2 product

        :param token: Your access token
        :param product_id: id of sentinel-2 product
        """
        url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            with requests.get(url, headers=headers, stream=True) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))
                os.makedirs(str(self.download_path), exist_ok=True)
                full_path = os.path.join(self.download_path)
                with open(f"{full_path}/product{product_id}.zip", "wb") as file, tqdm(
                        desc=f"Downloading:",
                        total=total_size,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                        dynamic_ncols=True,
                ) as progress_bar:
                    for data in response.iter_content(chunk_size=1024):
                        file.write(data)
                        progress_bar.update(len(data))
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to download product {product_id}: {e}")

    def execute(self) -> None:
        """
        Main process for downloading Sentinel-2 data.
        """
        try:
            client = self.client
            token = client.authorize()
            product_url = self.create_url_process()
            product_data = self.get_products(product_url)
            product_ids = product_data.get("Id")

            if product_ids is not None:
                for product_id in product_ids:
                    self.download_product(token, product_id)
        except Exception as e:
            print(e)

# Usage example
if __name__ == "__main__":
    start_date = "2023-08-01"
    end_date = "2023-08-30"
    data_collection = "SENTINEL-2"
    aoi = "POLYGON((77.42729554874207 42.302451615096686, 78.81812370370375 42.302451615096686, 78.81812370370375 43.32625697132075, 77.42729554874207 43.32625697132075, 77.42729554874207 42.302451615096686))'"

    username = config("S2_USERNAME")
    password = config("S2_PASSWORD")
    client = ApiClient(username=username, password=password)

    downloader = Sentinel2Downloader(client=client)
    downloader.set_config(
        start_date,
        end_date,
        data_collection,
        aoi,
        cloud_cover_percentage=20,
        product_type="MSIL1C",
        download_path="s2_result"
    )
    downloader.execute()
