## AWS resources glossary

### Lambdas

#### 1. s3-discovery

Discovers all the files in an S3 bucket, based on the prefix and filename regex.

#### 2. cmr-query

Discovers all the files in a CMR collection, based on the version, temporal, bounding box, and include. Returns objects that follow the specified criteria.

#### 3. cogify

Converts the input file to a COG file, writes it to S3, and returns the S3 key.

#### 4. data-transfer

Copies the data to the MAAP MCP bucket if necessary.

#### 5. build-stac

Given an object received from the `STAC_READY_QUEUE`, builds a STAC Item, writes it to S3, and returns the S3 key.

#### 6. submit-stac

Submits STAC items to STAC Ingestor system via POST requests.

#### 7. proxy

Reads objects from the specified queue in batches and invokes the specified step function workflow with the objects from the queue as the input.

### Step Function Workflows

#### 1. Discover

Discovers all the files that need to be ingested either from s3 or cmr.

#### 2. Cogify

Converts the input files to COGs, runs in parallel.

#### 3. Publication

Publishes the item to the STAC database (and MCP bucket if necessary).