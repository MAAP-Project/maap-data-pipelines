#!/bin/bash

# load config from .env, assumed to be in the same directory as this script and a valid bash file
set -a # automatically export all variables
source .env
set +a

# constants
export CMR_API_URL=https://cmr.maap-project.org
export USER_SHARED_BUCKET=maap-user-shared-data
export BUCKET=nasa-maap-data-store

# outputs or resources of other stacks. Get them programmatically based on assumptions regarding the stack names and their structure.
# to infer the pgstac stack name, using the `ENV` variable set in the .env file, so we're using the same stage as the one we're deploying to. 
# for the auth deployment, we're always using the `dev` stage, so we can hardcode that.
export PGSTAC_STACK_NAME="MAAP-STAC-${ENV}-pgSTAC"
export AUTH_STACK_NAME="maap-auth-stack-dev"

export COGNITO_APP_SECRET=$(aws cloudformation describe-stacks --stack-name $AUTH_STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`MAAPworkflowssecretoutput`].OutputValue' --output text)
export STAC_INGESTOR_API_URL=$(aws cloudformation describe-stacks --stack-name $PGSTAC_STACK_NAME --query "Stacks[0].Outputs[?ExportName==\`ingestor-api-${ENV}\`].OutputValue" --output text)
export DATA_MANAGEMENT_ROLE_ARN=$(aws cloudformation describe-stack-resources --stack-name $PGSTAC_STACK_NAME --query 'StackResources[?contains(LogicalResourceId, `dataaccessrole`) && ResourceType==`AWS::IAM::Role`].{Arn:PhysicalResourceId}' --output text)

# print out the environment variables created here with a nice header
echo "Environment variables set:"
echo "=========================="
echo "CMR_API_URL=$CMR_API_URL"
echo "USER_SHARED_BUCKET=$USER_SHARED_BUCKET"
echo "BUCKET=$BUCKET"
echo "COGNITO_APP_SECRET=$COGNITO_APP_SECRET"
echo "STAC_INGESTOR_API_URL=$STAC_INGESTOR_API_URL"
echo "DATA_MANAGEMENT_ROLE_ARN=$DATA_MANAGEMENT_ROLE_ARN"
echo "=========================="

# prompt user to continue. If yes, continue. If no, exit.
read -p "Continue? (y/n) " -n 1 -r
# inform that we are deploying
echo ""
echo "Deploying..."

cdk synth --all --require-approval never
cdk deploy --all --require-approval never
