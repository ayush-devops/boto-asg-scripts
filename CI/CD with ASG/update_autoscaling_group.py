import boto3
from config import *
import sys
from boto3.exceptions import botocore
import time
from datetime import datetime
from colorama import Fore, Back, Style
import logging
logging.basicConfig(filename='error.log',filemode="a",format='%(asctime)s %(message)s')
logger=logging.getLogger()

def main():
    try:
        start_time = datetime.now()
        con = boto3.client('ec2', region_name=aws_region)
        ag = boto3.client('autoscaling', region_name=aws_region)
        elb = boto3.client('elbv2', region_name=aws_region)
         
        print(Fore.GREEN  + "Rebooting Autoscaling Group to generate new Instances" + Style.RESET_ALL + "\n")
        reboot_autoscalingGroup(con, ag)
    except botocore.exceptions.ClientError as e:
       # print(e)
        logger.debug("Error  while modifying Autoscaling group %r"%e)

def reboot_autoscalingGroup(con, ag):

    try:

        current_stat = ag.describe_auto_scaling_groups(AutoScalingGroupNames=[autoscaling_group])  

        #get the current max & desired in auto scaling group
        
        max_count = int(current_stat['AutoScalingGroups'][0]['MaxSize'])
        min_count = int(current_stat['AutoScalingGroups'][0]['MinSize'])
        desired_count = int(current_stat['AutoScalingGroups'][0]['DesiredCapacity'])*2
        
        # increase the desired to the double of it.
        #max_count = max(max_count,2*desired_count)
        
        print max_count, min_count, desired_count
        ag.update_auto_scaling_group(AutoScalingGroupName=autoscaling_group, MinSize = min_count, MaxSize = max(max_count,2*desired_count), DesiredCapacity = desired_count)
        
        print "Updated Group"
        
        count = 0
        while len(ag.describe_auto_scaling_groups(AutoScalingGroupNames=[autoscaling_group])['AutoScalingGroups'][0]['Instances']) < desired_count:
            time.sleep(6)
            print "Current Instance count "
            print  len(ag.describe_auto_scaling_groups(AutoScalingGroupNames=[autoscaling_group])['AutoScalingGroups'][0]['Instances'])
            if count > 20:
                break
            count += 1
        
        if len(ag.describe_auto_scaling_groups(AutoScalingGroupNames=[autoscaling_group])['AutoScalingGroups'][0]['Instances']) == desired_count:
            print  "Intermediate Instances added."
        else:
            print "Intermediate Instances couldn't be added."
        
        
        while True:
           state = ag.describe_auto_scaling_groups(AutoScalingGroupNames = [autoscaling_group])
           healthy_count = 0
           time.sleep(5)
           for each in state['AutoScalingGroups'][0]['Instances']:
              healthy_count += 1 if each['LifecycleState'] == "InService" else 0
           print str(healthy_count) + " Total healty"
           if healthy_count == desired_count:
              break
        desired_count = desired_count//2 
        print "Scaling In"
        ag.update_auto_scaling_group(AutoScalingGroupName=autoscaling_group, MinSize = min_count, MaxSize = max_count, DesiredCapacity = desired_count)
        
        print "DOne"
    except botocore.exceptions.ClientError as e:
#  print(e)
       logger.debug("Error  while modifying Autoscaling group %r"%e)


if __name__ == '__main__':

    main()

