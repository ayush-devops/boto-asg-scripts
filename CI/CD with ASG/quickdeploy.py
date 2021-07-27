#!/usr/bin/python

import smtplib
import email.utils
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.MIMEText import MIMEText
import sys
import boto3
import time
from datetime import datetime
from colorama import Fore, Back, Style
from config import *
import urllib3
import paramiko
urllib3.disable_warnings()


def main():
    try:

        start_time = datetime.now()      
        print(Fore.BLACK + Back.GREEN + "<-------- Initiating quick deployment -------->" + Style.RESET_ALL+ "\n" + "\n")
        print(Fore.BLACK + Back.GREEN + "Establishing Connection with AWS using Boto3" + Style.RESET_ALL+ "\n")        

        var = datetime.now().strftime("%y-%m-%d-%H-%M")
        con = boto3.client('ec2', region_name=aws_region)
        ag = boto3.client('autoscaling', region_name=aws_region)
        elb = boto3.client('elbv2', region_name=aws_region)

        print(Fore.GREEN + "Checking Chatwhizz Primary Instance Health under loadbalancer"+ Style.RESET_ALL+ "\n")
        chk_primaryHealth(primary_server_ip, con, elb)

        print(Fore.GREEN + "Fetching Current ec2 AMI from launch configuration" + Style.RESET_ALL+ "\n")   
        current_imageID = ag.describe_launch_configurations(LaunchConfigurationNames=[launch_configuration])['LaunchConfigurations'][0]['ImageId']
        print(Fore.GREEN  + "creating ec2 AMI from primary server instance: %s" %(primary_aws_name_tag) + Style.RESET_ALL + "\n")
        imageId=create_ami(primary_server_ip, con, ami_prefix, var)

        print(Fore.GREEN  + "ec2 AMI created: %s" %(imageId) + Style.RESET_ALL + "\n")
        print(Fore.GREEN  + "Updating launch configuration with new AMI" + Style.RESET_ALL + "\n")

        update_launchconfiguration(con, ag, imageId, aws_security_group, aws_instance_type, aws_subnet, aws_key, autoscaling_group, launch_configuration, user_data)

        print(Fore.GREEN  + "Rebooting Autoscaling Group to generate new Instances" + Style.RESET_ALL + "\n")
        reboot_autoscalingGroup(con, ag)

        print(Fore.GREEN  + "Existing Chatwhizz Autoscaled Instances will be removed from load balancer after 5 minutes of draining period" + Style.RESET_ALL + "\n")
        print(Fore.GREEN + "Deleting Old ec2 AMI along with its snapshot" + Style.RESET_ALL + "\n")

        delete_oldImage(con, current_imageID)
        time_elapsed = datetime.now() - start_time

        print Fore.GREEN + 'Time elapsed (hh:mm:ss.ms) {}'.format(time_elapsed) + Style.RESET_ALL + "\n"
        print(Fore.GREEN  + "Triggering ec2 AMI quick deployment notification" + Style.RESET_ALL + "\n" + "\n")

        mail_message="Server Update Successful. ec2 AMI" + " " + imageId + " " + " has been updated on launch configuration." + "\n" + "Commit Message:-" + "\t" + image_description
        mailer(mail_message, SMTP_SERVER, SMTP_PORT, sender, password, recipient, subject)

        print(Fore.BLACK + Back.GREEN + "<-------- quick deployment done -------->" + Style.RESET_ALL)

    except Exception, e1:

        error1 = "main Error1: %s" % str(e1)
        print Fore.RED + Back.GREEN +  error1 + Style.RESET_ALL
        mailer(error1, SMTP_SERVER, SMTP_PORT, sender, password, recipient, subject)
        sys.exit(1)


def chk_primaryHealth(primary_server_ip, con, elb):

    try:

        i = con.describe_instances(Filters=[{'Name' : 'ip-address', 'Values' : [primary_server_ip]}])['Reservations'][0]['Instances'][0]['InstanceId']
        tgt_hlth_1 = elb.describe_target_health(TargetGroupArn=aws_target_group_80, Targets=[{'Id': i, 'Port': 80}])['TargetHealthDescriptions'][0]['TargetHealth']['State']
        #tgt_hlth_2 = elb.describe_target_health(TargetGroupArn=aws_target_group, Targets=[{'Id': i, 'Port': 443}])['TargetHealthDescriptions'][0]['TargetHealth']['State']
        y=0

        while tgt_hlth_1 != 'healthy':  #or tgt_hlth_2 != 'healthy':

          tgt_hlth_1 = elb.describe_target_health(TargetGroupArn=aws_target_group_80, Targets=[{'Id': i, 'Port': 80}])['TargetHealthDescriptions'][0]['TargetHealth']['State']
       #   tgt_hlth_2 = elb.describe_target_health(TargetGroupArn=aws_target_group, Targets=[{'Id': i, 'Port': 443}])['TargetHealthDescriptions'][0]['TargetHealth']['State']

          print("Trial %s: Primary Instance health under Target Group 1:%s"%(y,tgt_hlth_1))
          #print(Fore.GREEN + "Trial %s: Primary Instance health under Target Group 1: %s status and Target Group 2: %s status" %(y,tgt_hlth_1, tgt_hlth_2) + Style.RESET_ALL) + "\n"
          time.sleep(5)

          y=y+1

          if y == 5:

             exception = "Even after 5 attempts, state of Primary Instance under loadbalancer is still unhealthy. Aborting !!"
             print Fore.RED + Back.GREEN + exception + Style.RESET_ALL 
             raise Exception(exception)

    except Exception, e1:

        error1 = "chk_primaryHealth Error1: %s" % str(e1)
        print Fore.RED + Back.GREEN +  error1 + Style.RESET_ALL
        mailer(error1, SMTP_SERVER, SMTP_PORT, sender, password, recipient, subject)
        sys.exit(1)


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
               print Fore.RED + Back.GREEN + exception + Style.RESET_ALL 
               raise Exception(exception)
        return (imageId)

    except Exception, e1:
        error1 = "create_ami Error1: %s" % str(e1)
        print Fore.RED + Back.GREEN +  error1 + Style.RESET_ALL
        mailer(error1, SMTP_SERVER, SMTP_PORT, sender, password, recipient, subject)
        sys.exit(1)

def update_launchconfiguration(con, ag, imageId, aws_security_group, aws_instance_type, aws_subnet, aws_key, autoscaling_group, launch_configuration, user_data):

    try:

        ag.create_launch_configuration(LaunchConfigurationName='copy-'+launch_configuration, ImageId=imageId, KeyName=aws_key, SecurityGroups=[aws_security_group], AssociatePublicIpAddress=True, InstanceType=aws_instance_type, UserData=user_data, BlockDeviceMappings=[{'Ebs': {'DeleteOnTermination': True}, 'DeviceName': '/dev/sda1'}])
        ag.update_auto_scaling_group(AutoScalingGroupName=autoscaling_group, LaunchConfigurationName='copy-'+launch_configuration)

        ag.delete_launch_configuration(LaunchConfigurationName=launch_configuration)
        ag.create_launch_configuration(LaunchConfigurationName=launch_configuration, ImageId=imageId, KeyName=aws_key, SecurityGroups=[aws_security_group], AssociatePublicIpAddress=True, InstanceType=aws_instance_type, UserData=user_data, BlockDeviceMappings=[{'Ebs': {'DeleteOnTermination': True}, 'DeviceName': '/dev/sda1'}])

        ag.update_auto_scaling_group(AutoScalingGroupName=autoscaling_group, LaunchConfigurationName=launch_configuration)
        ag.delete_launch_configuration(LaunchConfigurationName='copy-'+launch_configuration)

        print(Fore.GREEN + "launch configuration updated" + Style.RESET_ALL)

    except Exception, e1:

        error1 = "update_launchconfiguration Error1: %s" % str(e1)
        print Fore.RED + Back.GREEN +  error1 + Style.RESET_ALL
        mailer(error1, SMTP_SERVER, SMTP_PORT, sender, password, recipient, subject)
        sys.exit(1)

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
            print "Curret Instnce count "
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

    except Exception, e1:
        error1 = "reboot_autoscalingGroup Error1: %s" % str(e1)
        print Fore.RED + Back.GREEN +  error1 + Style.RESET_ALL
        mailer(error1, SMTP_SERVER, SMTP_PORT, sender, password, recipient, subject)
        sys.exit(1)

def delete_oldImage(con, old_imageID):

    try:

        snap=con.describe_images(ImageIds=[old_imageID])['Images'][0]['BlockDeviceMappings'][0]['Ebs']['SnapshotId']
        print(Fore.GREEN + "Deregistering ec2 AMI: "+old_imageID + Style.RESET_ALL)
        con.deregister_image(ImageId=old_imageID)
        print(Fore.GREEN + "Deleting associated ec2 snapshot: "+snap + Style.RESET_ALL)
        con.delete_snapshot(SnapshotId=snap)

    except Exception, e1:

        error1 = "delete_oldImage Error1: %s" % str(e1)
        print Fore.RED + Back.GREEN +  error1 + Style.RESET_ALL
        mailer(error1, SMTP_SERVER, SMTP_PORT, sender, password, recipient, subject)
        sys.exit(1)


def mailer(mail_message, SMTP_SERVER, SMTP_PORT, sender, password, recipient, subject):

    try:

        msg = MIMEMultipart()
        msg['subject'] = subject
        msg['To'] = ','.join(recipient)
        msg['From'] = sender
        part = MIMEText('text', "plain")
        message = mail_message
        part.set_payload(message)
        msg.attach(part)
        session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        session.ehlo()
        session.starttls()
        session.ehlo
        session.login(sender, password)
        qwertyuiop = msg.as_string()
        session.sendmail(sender, recipient, qwertyuiop)
        session.quit()

    except Exception, e1:

        error1 = "Error1: %s" % str(e1)
        print Fore.RED + Back.GREEN +  error1 + Style.RESET_ALL
        sys.exit(1)

if __name__ == '__main__':

    main()
