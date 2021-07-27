#!/usr/bin/python
import sys

## primary server details
primary_server_ip="18.212.55.3"
primary_aws_name_tag="odoo-primary"

## ec2 instance parameters
aws_region="us-east-1"
aws_security_group="sg-09c6a44f594881b82"
aws_instance_type="t2.micro"
aws_subnet="subnet-675a3949"
aws_key="architecture"

## ec2 ami
ami_prefix="odoo12-ami"
image_description="odoo12-ami"

## Instance user data
user_data="""#!/bin/bash
h#add something"""

## autoscaling group
autoscaling_group="odoo12-ASG"
autoscaled_aws_name_tag="odoo12-ASG"
launch_configuration="odoo12-LC"

ag_desired_capacity=1
ag_min_size=1
ag_max_size=2

## Application elastic load balancer and target groups
aws_elb="odoo-ALB"
#aws_target_group="arn:aws:elasticloadbalancing:us-east-1:276307182872:targetgroup/chatwhizz-target-group/5077b9413981d9c1"
aws_target_group="arn:aws:elasticloadbalancing:us-east-1:936266536970:targetgroup/odoo-TG/2478978657e9e159"
aws_target_group_80="arn:aws:elasticloadbalancing:us-east-1:936266536970:targetgroup/odoo-TG/2478978657e9e159"

## SMTP Credentials
SMTP_SERVER = "zsmtp.hybridzimbra.com"
SMTP_PORT = 587
sender = ""
password = ""
recipient = []
subject = ""
