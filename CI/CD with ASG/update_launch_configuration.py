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
        ami=  con.describe_images(Owners=['self'])
        current_imageID = ag.describe_launch_configurations(LaunchConfigurationNames=[launch_configuration])['LaunchConfigurations'][0]['ImageId']
        print(Fore.GREEN  + "Updating launch configuration with new AMI" + Style.RESET_ALL + "\n")
        imageId= ami['Images'][0]['ImageId']
        update_launchconfiguration(con, ag, imageId, aws_security_group, aws_instance_type, aws_subnet, aws_key, autoscaling_group, launch_configuration, user_data)
    except botocore.exceptions.ClientError as e:
          logger.debug("Error while updating Launch Configuration %r"%e)




def update_launchconfiguration(con, ag, imageId, aws_security_group, aws_instance_type, aws_subnet, aws_key, autoscaling_group, launch_configuration, user_data):

    try:

        ag.create_launch_configuration(LaunchConfigurationName='copy-'+launch_configuration, ImageId=imageId, KeyName=aws_key, SecurityGroups=[aws_security_group], AssociatePublicIpAddress=True, InstanceType=aws_instance_type, UserData=user_data, BlockDeviceMappings=[{'Ebs': {'DeleteOnTermination': True}, 'DeviceName': '/dev/sda1'}])
        ag.update_auto_scaling_group(AutoScalingGroupName=autoscaling_group, LaunchConfigurationName='copy-'+launch_configuration)

        ag.delete_launch_configuration(LaunchConfigurationName=launch_configuration)
        ag.create_launch_configuration(LaunchConfigurationName=launch_configuration, ImageId=imageId, KeyName=aws_key, SecurityGroups=[aws_security_group], AssociatePublicIpAddress=True, InstanceType=aws_instance_type, UserData=user_data, BlockDeviceMappings=[{'Ebs': {'DeleteOnTermination': True}, 'DeviceName': '/dev/sda1'}])

        ag.update_auto_scaling_group(AutoScalingGroupName=autoscaling_group, LaunchConfigurationName=launch_configuration)
        ag.delete_launch_configuration(LaunchConfigurationName='copy-'+launch_configuration)

        print(Fore.GREEN + "launch configuration updated" + Style.RESET_ALL)
    except botocore.exceptions.ClientError as e:
          logger.debug("Error while updating Launch Configuration %r"%e)
    except botocore.exceptions.ParamValidationError as e:
          logger.debug("Error  while modifying lauc configurtion"%e)


if __name__ == '__main__':

    main()

