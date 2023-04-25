#!/bin/bash

# This script is used to set up the environment variables needed for publication.

# load config from .env, assumed to be in the same directory as this script and a valid bash file
set -a # automatically export all variables
source .env
set +a


# outputs or resources of other stacks. Get them programmatically based on assumptions regarding the stack names and their structure.
# to infer the pgstac stack name, using the `ENV` variable set in the .env file, so we're using the same stage as the one we're deploying to. 
# for the auth deployment, we're always using the `dev` stage, so we can hardcode that.
export PGSTAC_STACK_NAME="MAAP-STAC-${ENV}-pgSTAC"
export AUTH_STACK_NAME="maap-auth-stack-dev"
export APP_NAME="maap-data-pipelines"

export COGNITO_APP_SECRET=$(aws cloudformation describe-stacks --stack-name $AUTH_STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`MAAPworkflowssecretoutput`].OutputValue' --output text)
export STAC_INGESTOR_API_URL=$(aws cloudformation describe-stacks --stack-name $PGSTAC_STACK_NAME --query "Stacks[0].Outputs[?ExportName==\`ingestor-api-${ENV}\`].OutputValue" --output text)

# print out the environment variables created here with a nice header
echo "Environment variables set:"
echo "=========================="
echo "COGNITO_APP_SECRET=$COGNITO_APP_SECRET"
echo "STAC_INGESTOR_API_URL=$STAC_INGESTOR_API_URL"
echo "=========================="
