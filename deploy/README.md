The infrastructure stored as code in this repository is deployed on AWS using the AWS CDK stacks defined in the `/deploy` folder.

## Requirements

### libraries

- `docker` is installed an running
- `Node.js` is installed
- the CLI for the AWS CDK is installed. See [cdk-getting-started](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html).
- the environment variables in `/deploy/.env` are populated. 
- The python requirements in `/deploy/requirements.txt` are installed.

### infrastructure dependencies

These https://github.com/MAAP-Project/maap-cdk-pgstac https://github.com/MAAP-Project/MAAP-STAC-auth should be deployed first to the same AWS account. 

## Deployment

From the `/deploy` folder : 
- populate the `.env` file. Most of the configuration is determined programatically, see below script.
- run `deploy.sh`. 