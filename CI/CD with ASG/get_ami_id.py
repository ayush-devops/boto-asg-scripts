#!/usr/bin/python
import boto3
client = boto3.client('ec2')
response = client.describe_images(Owners=['self'])
#imageid = response.ImageId()
#print(response)
#import json, ast
#response1 = ast.literal_eval(json.dumps(response))
#print(response1.get('ImageId','ayush'))


for key in response['Images']:#[0]:
    print key #print all the image ids

imageid =  response['Images'][0]['ImageId']  #If there are multiple AMI's and you want to print the first image_id;
print(imageid)
~                               
