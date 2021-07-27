#!/usr/bin/python
import boto3
import time
from datetime import datetime
from colorama import Fore, Back, Style
from boto3.exceptions import botocore
from config import *

import logging
logging.basicConfig(filename='error.log',filemode="a",format='%(asctime)s %(message)s')
logger=logging.getLogger()

def main():
    try:

        start_time = datetime.now()      
        print(Fore.BLACK + Back.GREEN + "<-------- Initiating quick deployment -------->" + Style.RESET_ALL+ "\n" + "\n")
        print(Fore.BLACK + Back.GREEN + "Establishing Connection with AWS using Boto3" + Style.RESET_ALL+ "\n")        

        var = datetime.now().strftime("%y-%m-%d-%H-%M")
        con = boto3.client('ec2', region_name=aws_region)
        ag = boto3.client('autoscaling', region_name=aws_region)
        elb = boto3.client('elbv2', region_name=aws_region)

        #print(Fore.GREEN + "Checking Chatwhizz Primary Instance Health under loadbalancer"+ Style.RESET_ALL+ "\n")
        #chk_primaryHealth(primary_server_ip, con, elb)

        print(Fore.GREEN + "Fetching Current ec2 AMI from launch configuration" + Style.RESET_ALL+ "\n")   
        current_imageID = ag.describe_launch_configurations(LaunchConfigurationNames=[launch_configuration])['LaunchConfigurations'][0]['ImageId']
        print(Fore.GREEN  + "creating ec2 AMI from primary server instance: %s" %(primary_aws_name_tag) + Style.RESET_ALL + "\n")
        imageId=create_ami(primary_server_ip, con, ami_prefix, var)
        print(Fore.GREEN  + "ec2 AMI created: %s" %(imageId) + Style.RESET_ALL + "\n")
    except botocore.exceptions.ClientError as e:
          logger.debug("Error while creating AMI %r"%e)

def create_ami(primary_server_ip, con, ami_prefix, var):

    try:
        i = con.describe_instances(Filters=[{'Name' : 'ip-address', 'Values' : [primary_server_ip]}])['Reservations'][0]['Instances'][0]['InstanceId']
        imageId=con.create_image(InstanceId=i, Name=ami_prefix+var, Description=image_description, NoReboot=True, BlockDeviceMappings=[{'Ebs': {'DeleteOnTermination': True}, 'DeviceName': '/dev/sda1'}])['ImageId']

        print(Fore.GREEN + "checking Image status of Imageid: "+imageId + Style.RESET_ALL)
        image_status=con.describe_images(ImageIds=[imageId])['Images'][0]['State']

        x=0

        while image_status != 'available':

          if image_status == 'failed':
             print(Fore.GREEN + "Image status of Imageid %s: %s" %(imageId,image_status) + Style.RESET_ALL)
             sys.exit(1)

          else:
             image_status=con.describe_images(ImageIds=[imageId])['Images'][0]['State']
             print(Fore.GREEN + "Trial %s: ec2 AMI %s status" %(x, image_status) + Style.RESET_ALL)
             time.sleep(20)

             x=x+1
             if x == 40:
               exception = "Even after 41 attempts, state of ec2 AMI is still pending. Aborting ec2 AMI update process. Exiting !!"
               print(Fore.RED + Back.GREEN + exception + Style.RESET_ALL)
               raise Exception(exception)
        return (imageId)
    
    except botocore.exceptions.ParamValidationError as e:
          logger.debug("Error  while modifying listener %r"%e)


if __name__ == '__main__':

    main()

