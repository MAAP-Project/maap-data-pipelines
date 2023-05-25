import configparser
import os
import requests

import boto3

import numpy as np

from affine import Affine
from netCDF4 import Dataset
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rasterio.warp import calculate_default_transform
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles


config = configparser.ConfigParser()
config.read("example.ini")
s3 = boto3.client(
    "s3",
)

# Set COG inputs
output_profile = cog_profiles.get(
    "deflate"
)  # if the files aren't uint8, this will need to be changed
output_profile["blockxsize"] = 256
output_profile["blockysize"] = 256
output_bucket = config["DEFAULT"]["output_bucket"]
output_dir = config["DEFAULT"]["output_dir"]


def build_output_location(outfilename, collection, suffix):
    """return bucket and key"""
    return (
        output_bucket,
        f"{output_dir}/{collection}/{outfilename.split('/tmp/')[1]}{suffix}",
    )


def upload_file(outfilename, collection, suffix=""):
    print("Uploading file to S3")
    bucket, key = build_output_location(outfilename, collection, suffix)
    try:
        s3.upload_file(
            outfilename,
            bucket,
            key,
        )
        print("File uploaded to s3")
        return f"s3://{bucket}/{key}"
    except:
        print(f"Failed to copy to S3 bucket and key : {bucket}/{key}")
        raise


def download_file(file_uri: str):
    filename = os.path.splitext(os.path.basename(file_uri))[0]
    filename = f"/tmp/{filename}"
    if "http" in file_uri:
        # This isn't working for GPMIMERG, need to use .netrc
        username = os.environ.get("EARTHDATA_USERNAME")
        password = os.environ.get("EARTHDATA_PASSWORD")
        with requests.Session() as session:
            session.auth = (username, password)
            request = session.request("get", file_uri)
            response = session.get(request.url, auth=(username, password))
            print("RESPONSE IS")
            print(response.status_code)
            with open(filename, "wb") as f:
                f.write(response.content)
    elif "s3://" in file_uri:
        path_parts = file_uri.split("://")[1].split("/")
        bucket = path_parts[0]
        path = "/".join(path_parts[1:])
        s3.download_file(bucket, path, filename)
    else:
        print(f"{filename} file already downloaded")
    return filename


def hdf5_to_cog(upload, **config):
    """HDF5 to COG."""
    # Open existing dataset
    filename = str(config["filename"])
    variable_name = config["variable_name"]
    x_variable, y_variable = config.get("x_variable"), config.get("y_variable")
    group = config.get("group")
    src = Dataset(filename, "r")

    if group is None:
        variable = src[variable_name][:]
        nodata_value = variable.fill_value
    else:
        variable = src.groups[group][variable_name]
        nodata_value = variable._FillValue
    # This may be just what we need for IMERG
    if config["collection"] == "GPM_3IMERGM":
        variable = np.transpose(variable[0])
    if config["collection"] == "OMDOAO3e":
        variable = np.flipud(variable)

    # This implies a global spatial extent, which is not always the case
    src_height, src_width = variable.shape[0], variable.shape[1]
    if x_variable and y_variable:
        xmin = src[x_variable][:].min()
        xmax = src[x_variable][:].max()
        ymin = src[y_variable][:].min()
        ymax = src[y_variable][:].max()
    else:
        xmin, ymin, xmax, ymax = [-180, -90, 180, 90]

    src_crs = config.get("src_crs")
    if src_crs:
        src_crs = CRS.from_proj4(src_crs)
    else:
        src_crs = CRS.from_epsg(4326)

    dst_crs = CRS.from_epsg(3857)

    # calculate dst transform
    dst_transform, dst_width, dst_height = calculate_default_transform(
        src_crs,
        dst_crs,
        src_width,
        src_height,
        left=xmin,
        bottom=ymin,
        right=xmax,
        top=ymax,
    )

    # https://github.com/NASA-IMPACT/cloud-optimized-data-pipelines/blob/rwegener2-envi-to-cog/docker/omno2-to-cog/OMNO2d.003/handler.py
    affine_transformation = config.get("affine_transformation")
    if affine_transformation:
        xres = (xmax - xmin) / float(src_width)
        yres = (ymax - ymin) / float(src_height)
        geotransform = eval(affine_transformation)
        dst_transform = Affine.from_gdal(*geotransform)

    # Save output as COG
    output_profile = dict(
        driver="GTiff",
        dtype=variable.dtype,
        count=1,
        transform=dst_transform,
        crs=src_crs,
        height=src_height,
        width=src_width,
        nodata=nodata_value,
        tiled=True,
        compress="deflate",
        blockxsize=256,
        blockysize=256,
    )
    print("profile h/w: ", output_profile["height"], output_profile["width"])
    outfilename = f"{filename}.tif"
    with MemoryFile() as memfile:
        with memfile.open(**output_profile) as mem:
            data = variable.astype(np.float32)
            mem.write(data, indexes=1)
        cog_translate(
            memfile,
            outfilename,
            output_profile,
            config=dict(GDAL_NUM_THREADS="ALL_CPUS", GDAL_TIFF_OVR_BLOCKSIZE="128"),
        )
    return_obj = {
        "filename": outfilename,
    }
    if upload:
        s3location = upload_file(outfilename, config["collection"])
        return_obj["remote_fileurl"] = s3location

    return return_obj


def geotiff_to_cog(upload: bool, **config):
    """Convert image to COG and write to S3"""

    # using default rio cogeo settings
    output_profile = cog_profiles.get("deflate")
    output_profile.update(dict(BIGTIFF="IF_SAFER"))

    # Dataset Open option (see gdalwarp `-oo` option)
    gdal_config = dict(
        GDAL_NUM_THREADS="ALL_CPUS",
        GDAL_TIFF_INTERNAL_MASK=True,
        GDAL_TIFF_OVR_BLOCKSIZE="128",
    )

    filename = config["filename"]

    cog_translate(
        source=filename,
        dst_path=filename,
        dst_kwargs=output_profile,
        config=gdal_config,
        in_memory=False,
        quiet=True,
    )

    return_obj = {"filename": filename}

    if upload:
        s3location = upload_file(filename, config["collection"], suffix=".tif")
        return_obj["remote_fileurl"] = s3location

    return return_obj


def handler(event, context):
    filename = event["remote_fileurl"]
    collection = event["collection"]
    downloaded_filename = download_file(file_uri=filename)

    to_cog_config = {}
    to_cog_config["filename"] = downloaded_filename
    to_cog_config["collection"] = collection

    return_obj = {"collection": event["collection"]}

    if filename.endswith(".he5"):
        config._sections[collection]
        output_locations = hdf5_to_cog(
            upload=event.get("upload", False), **to_cog_config
        )
    elif filename.endswith(".tif"):
        output_locations = geotiff_to_cog(
            upload=event.get("upload", False), **to_cog_config
        )
    else:
        raise ValueError(f"File type not supported: {filename}")

    return_obj = {**return_obj, **output_locations}

    print(f"Returning data: {return_obj}")
    return return_obj


if __name__ == "__main__":
    sample_event = {
        "collection": "ESACCI_Biomass_L4_AGB_V4_100m_2020",
        "remote_fileurl": "s3://maap-ops-workspace/nehajo88/Data/CCI_2020/N00E000_ESACCI-BIOMASS-L4-AGB-MERGED-100m-2020-fv4.0.tif",
        "upload": True,
    }
    handler(sample_event, {})
