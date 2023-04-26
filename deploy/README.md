The code in this folder deploys AWS Cloudformation stacks used to publish STAC metadata for the MAAP project. 

## Requirements

### libraries

- `docker` is installed an running
- `Node.js` is installed
- the [CLI for the AWS CDK is installed](https://docs.aws.amazon.com/cdk/v2/guide/cli.html)
- the environment variables in `.env` are populated. Most of the configuration is determined programatically, see below.
- The python requirements in `requirements.txt` are installed.

### infrastructure dependencies

These https://github.com/MAAP-Project/maap-cdk-pgstac https://github.com/MAAP-Project/MAAP-STAC-auth should be deployed first to the same AWS account. The deployment process here relies on resources produced by these.

## Deployment

Run `./deploy.sh`. Make sure to use `./` and not `source`. 