#!/usr/bin/python
import sys 
import boto3
import time
from colorama import Fore, Back, Style
from config import *
import urllib3
urllib3.disable_warnings()


def main():
    try:
        con = boto3.client('ec2', region_name=aws_region)
        conn = boto3.resource('ec2', region_name=aws_region)
        elb = boto3.client('elbv2', region_name=aws_region)
        ag = boto3.client('autoscaling', region_name=aws_region)

        res = elb.describe_target_health(TargetGroupArn = aws_target_group)['TargetHealthDescriptions']

        print Fore.BLACK + Back.GREEN + "Retreiving list of Instances Under the Application Load Balancer" + Style.RESET_ALL + "\n\n"

	print Fore.BLACK + Back.GREEN + "For Target Group 443:" + Style.RESET_ALL + "\n"
        res_1 = elb.describe_target_health(TargetGroupArn = aws_target_group)['TargetHealthDescriptions']
        for i in res_1:
          ip_address = con.describe_instances(InstanceIds=[i['Target']['Id']])['Reservations'][0]['Instances'][0]['PublicIpAddress']
          instance = conn.Instance(i['Target']['Id'])
          instance_health = i['TargetHealth']['State']
          tags = instance.tags or []
          names = [tag.get('Value') for tag in tags if tag.get('Key') == 'Name']
          name = names[0] if names else None
          print Fore.GREEN + '{0}: {1} {2}'.format(name, ip_address, instance_health)  + Style.RESET_ALL

        print "\n\n" + Fore.BLACK + Back.GREEN + "For Target Group 80:" + Style.RESET_ALL + "\n"
        res_2 = elb.describe_target_health(TargetGroupArn = aws_target_group_80)['TargetHealthDescriptions']
        for i in res_2:
          ip_address = con.describe_instances(InstanceIds=[i['Target']['Id']])['Reservations'][0]['Instances'][0]['PublicIpAddress']
          instance = conn.Instance(i['Target']['Id'])
          instance_health = i['TargetHealth']['State']
          tags = instance.tags or []
          names = [tag.get('Value') for tag in tags if tag.get('Key') == 'Name']
          name = names[0] if names else None
          print Fore.GREEN + '{0}: {1} {2}'.format(name, ip_address, instance_health)  + Style.RESET_ALL


        print "\n\n" + Fore.BLACK + Back.GREEN + "Retreiving Details of current ec2 AMI attached with the launch configuration" + Style.RESET_ALL + "\n"
        current_imageID = ag.describe_launch_configurations(LaunchConfigurationNames=[launch_configuration])['LaunchConfigurations'][0]['ImageId']
        imageID_description = con.describe_images(ImageIds=[current_imageID])['Images'][0]['Description']
        ImageID_date = con.describe_images(ImageIds=[current_imageID])['Images'][0]['CreationDate']
        print Fore.GREEN + "ec2 AMI:" + "\t" + current_imageID + "\n" + "Commit Message:" + "\t" + imageID_description + "\n" + "Commit Date:" + "\t" + ImageID_date + Style.RESET_ALL

    except Exception, e1:
        error1 = "Error1: %s" % str(e1)
        print Fore.RED + Back.GREEN + error1 + Style.RESET_ALL
        sys.exit(0)

if __name__ == '__main__':
    main()
