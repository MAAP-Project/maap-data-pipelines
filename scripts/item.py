import os
import json
import boto3

from .utils import args_handler, data_files, DATA_PATH, DISCOVERY_TRIGGER_ARN

items_path = os.path.join(DATA_PATH, "step_function_inputs")
sf_client = boto3.client("stepfunctions")


def insert_items(files):
    print("Inserting items:")
    for filename in files:
        print(filename)
        events = json.load(open(filename))
        if type(events) != list:
            events = [events]
        for event in events:
            lambda_client = boto3.client("lambda")
            response = lambda_client.invoke(
                FunctionName=DISCOVERY_TRIGGER_ARN,
                InvocationType="Event",
                Payload=json.dumps(event),
            )

            print(response)


@args_handler
def insert(items):
    print(items_path)
    files = data_files(items, items_path)
    print(files)
    insert_items(files)


def update(items):
    print("Function not implemented")


def delete(items):
    print("Function not implemented")
