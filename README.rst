sentinel2_downloader
====================

Overview
--------

`sentinel2_downloader` is a Python library that allows you to search, download, and retrieve metadata of Sentinel satellite images from the Copernicus Data Space.

Features
--------

- Search for Sentinel satellite images based on various parameters such as footprint, date range, product type, cloud cover percentage, and platform name.
- Download Sentinel satellite images using their product IDs.
- Save downloaded images to the specified directory.
- Display a progress bar during the download process, showing the download speed, elapsed time, and percentage of completion.

Installation
------------

You can install `sentinel2_downloader` using pip:

.. code:: bash

    pip install sentinel2_downloader

Usage
-----

Here's an example of how to use `sentinel2_downloader`:

.. code:: python

    from sentinel2_downloader import SentinelAPI

    # Create an instance of the SentinelAPI
    api = SentinelAPI(username='your_username', password='your_password')

    # Perform a search for Sentinel satellite images
    products = api.query(footprint='POLYGON((longitude1 latitude1, longitude2 latitude2, longitude3 latitude3, ...))',
    start_date='2020-01-01', end_date='2020-01-31', cloud_cover_percentage='20', product_type='MSIL1C',
    platform_name='SENTINEL-2')
    if len(products) > 1:
        for product in products:
            # Download the images
            a = api.download(product_id=product['Id'], directory_path='output')

Args:
    * footprint (str): The footprint to define the geographic area of interest. It should be in the Well-Known Text (WKT) format.
    * start_date (str): The start date of the data acquisition period in the format 'yyyy-mm-dd'.
    * end_date (str): The end date of the data acquisition period in the format 'yyyy-mm-dd'.
    * product_type (str): The type of Sentinel product to query.
    * cloud_cover_percentage (str): The maximum cloud cover percentage allowed.
    * platform_name (str): The name of the Sentinel platform.