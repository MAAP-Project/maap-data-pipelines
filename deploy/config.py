import os


ENV = os.environ.get("ENV")

COGNITO_APP_SECRET = os.environ["COGNITO_APP_SECRET"]
STAC_INGESTOR_API_URL = os.environ["STAC_INGESTOR_API_URL"]

EARTHDATA_USERNAME = os.environ.get("EARTHDATA_USERNAME", "XXXX")
EARTHDATA_PASSWORD = os.environ.get("EARTHDATA_PASSWORD", "XXXX")

APP_NAME = "maap-data-pipelines"
MAAP_DATA_BUCKET = "maap-data-store"
MAAP_EXTERNAL_BUCKETS = []
MCP_BUCKETS = {
    "prod": ["nasa-maap-data-store", "maap-ops-workspace"],
    "stage": ["nasa-maap-data-store", "maap-ops-workspace"],
    "dev": ["nasa-maap-data-store", "maap-ops-workspace"],
    "test": ["nasa-maap-data-store", "maap-ops-workspace"],
}
DATA_TRANSFER_BUCKET = "nasa-maap-data-store"
USER_SHARED_BUCKET = "maap-user-shared-data"

# This should throw if it is not provided
DATA_MANAGEMENT_ROLE_ARN = os.environ.get("DATA_MANAGEMENT_ROLE_ARN")
CMR_API_URL = os.environ.get("CMR_API_URL")
