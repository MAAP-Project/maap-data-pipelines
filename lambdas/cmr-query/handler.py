import datetime as dt
import json
import os
import re
from typing import Any, Dict, List, Pattern

import requests


def _get_asset_name(remote_fileurl: str, product_id: str) -> str:
    return re.sub(f".*{product_id}[-_.]?", "", remote_fileurl)


def _get_product_id(fileurls_pattern: Pattern, remote_fileurl: str) -> str:
    return re.search(fileurls_pattern, remote_fileurl).group()


def _multi_asset_check(granules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    assets = [obj for obj in granules if obj["rel"].endswith("/data#")]
    product_id = os.path.commonprefix(
        [os.path.basename(link["href"]) for link in assets]
    )
    return (product_id, assets) if len(assets) > 1 else (None, [])


def _stac_check(granules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        obj
        for obj in granules
        if (obj["href"].startswith("https") and obj["href"].endswith("stac.json"))
    ]


def get_cmr_granules_endpoint(event):
    default_cmr_api_url = (
        "https://cmr.maap-project.org"  # "https://cmr.earthdata.nasa.gov"
    )
    cmr_api_url = event.get(
        "cmr_api_url", os.environ.get("CMR_API_URL", default_cmr_api_url)
    )
    return f"{cmr_api_url}/search/granules.json"


def multi_asset_granule(
    file_obj: Dict[str, Any],
    assets: Dict[str, Any],
    product_id: str,
    data_file: List[str],
) -> Dict[str, Any]:
    """
    Processes multiple assets for a granule and updates the file object.

    This function iterates over the given assets and updates the file object with the asset information.
    It also sets the `remote_fileurl` field of the file object to the URL of the first asset that matches
    one of the strings in `data_file`, or to the URL of the first asset if no match is found.

    Args:
        file_obj (Dict[str, Any]): A dictionary representing the file object to update.
        assets (Dict[str, Any]): A dictionary containing the asset information.
        product_id (str): The product ID to use when generating asset names.
        data_file (List[str]): A list of strings to match against the asset names.

    Returns:
        Dict[str, Any]: The updated file object.
    """
    for asset in assets:
        asset_name = _get_asset_name(asset["href"], product_id)
        file_obj["assets"][asset_name] = asset["href"]
        if asset_name in data_file:
            file_obj["remote_fileurl"] = asset["href"]
    if not file_obj["remote_fileurl"]:
        file_obj["remote_fileurl"] = assets[0]["href"]
    return file_obj


def group_granules(
    data_files: List[str], fileurls_pattern: Pattern, data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Groups granules based on the given data files and file URL pattern.

    Args:
        data_files (List[str]): A list of data file names to group the granules by.
        fileurls_pattern (Pattern): A compiled regular expression pattern to match against the file URLs.
        data (List[Dict[str, Any]]): A list of dictionaries containing the granule data.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing the grouped granule data.
    """
    objects = []
    product_ids = {}

    # Creates a Dict[product_id, Dict[file_name, List[str]]]
    for item in data:
        if product_id := _get_product_id(fileurls_pattern, item["remote_fileurl"]):
            product_ids[product_id] = product_ids.get(product_id, {})

            product_ids[product_id][
                _get_asset_name(item["remote_fileurl"], product_id)
            ] = item["remote_fileurl"]

    # Creates an objects Dict of modified file_obj's, adding file_obj["assets"]
    if product_ids:
        for product_id in product_ids:
            for file_obj in data:
                if any(
                    re.search(
                        f".*{product_id}.*{data_file}", file_obj["remote_fileurl"]
                    )
                    for data_file in data_files
                ):
                    file_obj["assets"] = dict(sorted(product_ids[product_id].items()))
                    file_obj["product_id"] = product_id
                    objects.append(file_obj)
    return objects


def get_granules(
    event: Dict[str, Any], collection: str, granules: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    This function takes in an event dictionary, a collection string and a list of granule dictionaries and returns a list of granule dictionaries.

    Args:
        event (Dict[str, Any]): A dictionary representing the event.
        collection (str): A string representing the collection.
        granules (List[Dict[str, Any]]): A list of dictionaries representing the granules.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing the granules.
    """
    if isinstance(event.get("data_file"), str):
        event["data_file"] = [event.get("data_file")]
    multi_asset_granules = []
    stac_granules = []
    return_granules = []
    multi_granule_products = []

    for granule in granules:
        # Case: single granule is a STAC item
        if (records := _stac_check(granule["links"])) and event.get("mode") == "stac":
            stac_granules.extend(records)
            continue

        file_obj = {
            "collection": collection,
            "remote_fileurl": "",
            "granule_id": granule["id"],
            "id": granule["id"],
            "mode": event.get("mode"),
            "test_links": event.get("test_links"),
            "reverse_coords": event.get("reverse_coords"),
            "asset_name": event.get("asset_name"),
            "asset_roles": event.get("asset_roles"),
            "asset_media_type": event.get("asset_media_type"),
            "assets": {},
        }

        # Case: single granule has multiple assets
        product_id, assets = _multi_asset_check(granule["links"])
        if product_id and assets:
            file_obj = multi_asset_granule(
                file_obj, assets, product_id, event.get("data_file")
            )
            multi_asset_granules.append(file_obj)
            continue

        # Case: single granule has a single asset
        for link in granule["links"]:
            if link["rel"] in [
                "http://esipfed.org/ns/fedsearch/1.1/s3#",
                event.get("link_rel"),
            ]:
                file_obj["remote_fileurl"] = link["href"]
                return_granules.append(file_obj)

    # Case: multiple granules belong to a single product
    if event.get("data_file_regex"):
        fileurls_pattern = re.compile(event.get("data_file_regex"))
        multi_granule_products = group_granules(
            data_files=event.get("data_file"),
            fileurls_pattern=fileurls_pattern,
            data=return_granules,
        )
    return multi_granule_products + multi_asset_granules + stac_granules


def handler(event, context):
    """
    Lambda handler for the querying CMR and returning granules.
    """
    collection = event["collection"]
    version = event["version"]

    temporal = event.get("temporal", ["1000-01-01T00:00:00Z", "3000-01-01T23:59:59Z"])
    page = event.get("start_after", 1)
    limit = event.get("limit", 100)

    search_endpoint = (
        f"{get_cmr_granules_endpoint(event)}?short_name={collection}&version={version}"
        + f"&temporal[]={temporal[0]},{temporal[1]}&page_size={limit}"
    )
    search_endpoint = f"{search_endpoint}&page_num={page}"
    print(f"Discovering data from {search_endpoint}")
    response = requests.get(search_endpoint)

    if response.status_code != 200:
        print(f"Got an error from CMR: {response.status_code} - {response.text}")
        return

    hits = response.headers["CMR-Hits"]
    print(f"Got {hits} from CMR")
    granules = json.loads(response.text)["feed"]["entry"]
    print(f"Got {len(granules)} to insert")
    # Decide if we should continue after this page
    # Start paging if there are more hits than the limit
    # Stop paging when there are no more results to return
    if len(granules) > 0 and int(hits) > limit * page:
        print(f"Got {int(hits)} which is greater than {limit*page}")
        page += 1
        event["start_after"] = page
        print(f"Returning next page {event.get('start_after')}")
    else:
        event.pop("start_after", None)

    output = get_granules(event, collection, granules)
    return {
        **event,
        "cogify": event.get("cogify", False),
        "objects": output,
    }


if __name__ == "__main__":
    # sample_event = {
    #     "queue_messages": "true",
    #     "collection": "AfriSAR_UAVSAR_KZ",
    #     "version": "1",
    #     "discovery": "cmr",
    #     "temporal": ["2016-02-25T00:00:00Z", "2016-03-08T00:00:00Z"],
    #     "mode": "cmr",
    #     "asset_name": "data",
    #     "asset_roles": ["data"],
    #     "asset_media_type": {
    #         "vrt": "application/octet-stream",
    #         "bin": "binary/octet-stream",
    #         "hdr": "binary/octet-stream",
    #     },
    #     "data_file": "hdr",
    #     "data_file_regex": "uavsar_AfriSAR_v1-.*.{5}_.{5}_.{3}_.{3}_.{6}_kz",
    # }
    sample_event = {
        "queue_messages": "true",
        "collection": "AFRISAR_DLR",
        "temporal": ["2021-01-01T00:00:00Z", "2021-12-31T23:59:59Z"],
        "version": "1",
        "discovery": "cmr",
        "asset_name": "data",
        "asset_roles": {
            "prj": ["metadata"],
            "dbf": ["data"],
            "shp": ["data"],
            "shx": ["data"],
            "tiff": ["data"],
        },
        "asset_media_type": {
            "prj": "application/octet-stream",
            "dbf": "binary/octet-stream",
            "shp": "binary/octet-stream",
            "shx": "binary/octet-stream",
            "tiff": "image/tiff",
        },
        "reverse_coords": True,
        "link_rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
        "data_file": ["HH.tiff", "prj"],
        "data_file_regex": "afrisar_dlr_[^_]+",
    }
    with open("data.json", "w") as f:
        f.write(json.dumps(handler(sample_event, {}), indent=4))
