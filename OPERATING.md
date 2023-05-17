# Operating Guide: Data Transformation and Ingest for MAAP

This guide provides information on how to run ingest, transformation and metadata (STAC) publication workflows for MAAP.

## Requirements 

We rely on a set of [poetry](https://pypi.org/project/poetry/) scripts to publish data to the catalog. 

- run `pip install poetry` to install poetry.
- run `source setupenv.sh` to set up your environment variables for publication. Make sure to use `source` so that your environment variables persist. 
- run `poetry install` to install the project and the dependencies.

## Usage

- to insert a collection, run `poetry run insert-collection COLLECTION_NAME`
- to ingest items, run `poetry run insert-item COLLECTION_NAME` 

See more information below about these commands. 

## More information

The set of poetry commands above relies on input JSON files stored in the `data/` folder. 

### `collections/`

The `collections/` directory holds json files representing the data for MAAP collection metadata (STAC). `poetry run insert-collection COLLECTION_NAME` assumes there is a valid file for `COLLECTION_NAME` in that folder.

### `step_function_inputs/`

The `step_function_inputs/` directory holds json files representing the step function inputs for initiating the discovery, ingest and publication workflows. `poetry run insert-item COLLECTION_NAME` assumes there is a valid file for `COLLECTION_NAME` in that folder.

## Step Function Inputs
"bucket": String name of the bucket where the data is located
"collection": String name of the collection
"cogify": Boolean value to queue data files for transformation into Cloud Optimized GeoTIFFs
"directory": String bucket prefix, defaults to "file-staging"
"discovery": String type of discovery ("s3" or "inventory")
"filename_regex": String regex of data file naming e.g "^(.*).tif$"
"prefix": String prefix inside of the bucket where the data is located
"start_after": Integer used in boto3.client("s3").paginate to indicate which page to start after
"upload": true
"user_shared": Boolean value data upload to USER_SHARED_BUCKET

**_DEPRECATED_**: Step Function inputs used to discover granules from CMR
"asset_media_type": 
"asset_name":
"asset_roles":
"data_file": String regex of the data file to build STAC record around for a multi-data file CMR collection
"data_file_regex": String regex of multiple data files in a CMR collection
"link_rel": 
"mode": "stac" or "cmr"
"queue_messages": Boolean
"reverse_coords": Boolean value to reverse the generated geoJSON object from the list of coordinates provided by CMR
"temporal":
"test_links": 
"version": Version of the CMR Collection
