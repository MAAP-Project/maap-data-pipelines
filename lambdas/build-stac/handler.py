import json
import os
from sys import getsizeof
from typing import Any, Dict, TypedDict, Union
from uuid import uuid4

import pystac
import smart_open
from utils import events, stac


class S3LinkOutput(TypedDict):
    stac_file_url: str


class StacItemOutput(TypedDict):
    stac_item: Dict[str, Any]


def handler(event: Dict[str, Any], context) -> Union[S3LinkOutput, StacItemOutput]:
    """
    Lambda handler for STAC Collection Item generation

    Arguments:
    event - object with event parameters to be provided in one of 2 formats.
        Format option 1 (with Granule ID defined to retrieve all metadata from CMR):
        {
            "collection": "OMDOAO3e",
            "remote_fileurl": "s3://climatedashboard-data/OMDOAO3e/OMI-Aura_L3-OMDOAO3e_2022m0120_v003-2022m0122t021759.he5.tif",
            "granule_id": "G2205784904-GES_DISC",
        }
        Format option 2 (with regex provided to parse datetime from the filename:
        {
            "collection": "OMDOAO3e",
            "remote_fileurl": "s3://climatedashboard-data/OMSO2PCA/OMSO2PCA_LUT_SCD_2005.tif",
        }

    """

    EventType = events.CmrEvent if event.get("granule_id") else events.RegexEvent
    parsed_event = EventType.parse_obj(event)
    stac_item = stac.generate_stac(parsed_event).to_dict()

    output: StacItemOutput = {"stac_item": stac_item}

    # Return STAC Item Directly
    if getsizeof(json.dumps(output)) < (256 * 1024):
        return output

    # Return link to STAC Item
    key = f"s3://{os.environ['BUCKET']}/{uuid4()}.json"
    with smart_open.open(key, "w") as file:
        file.write(json.dumps(stac_item))

    return {"stac_file_url": key}


if __name__ == "__main__":
    asset_event = {
        "collection": "ESACCI_Biomass_L4_AGB_V4_100m",
        "asset_roles": ["data"],
        "asset_media_type": {
            "estimates": "image/tiff; application=geotiff; profile=cloud-optimized",
            "standard deviation": "image/tiff; application=geotiff; profile=cloud-optimized",
        },
        "asset_name": "estimates",
        "metadata_file_url_key": "metadata",
        "metadata_type": "standard_deviation",
        "remote_fileurl": "s3://nasa-maap-data-store/file-staging/nasa-map/ESACCI_Biomass_L4_AGB_V4_100m_2017/N70E140_ESACCI-BIOMASS-L4-AGB-MERGED-100m-2017-fv4.0.tif",
    }

    print(json.dumps(handler(asset_event, {}), indent=2))
