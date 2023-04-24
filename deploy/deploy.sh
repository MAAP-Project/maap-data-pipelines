#!/bin/bash

# load config from .env, assumed to be in the same directory as this script and a valid bash file
set -a # automatically export all variables
source .env
set +a

cdk synth --all --require-approval never
cdk deploy --all --require-approval never