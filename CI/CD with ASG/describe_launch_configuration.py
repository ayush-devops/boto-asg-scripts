import boto3
from config import *
import json

client = boto3.client('autoscaling')
response = client.describe_launch_configurations()
#print dir(response)
def pretty_print(data):
          return json.dumps(data, indent=4, default=str)

print(pretty_print(response))
