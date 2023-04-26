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