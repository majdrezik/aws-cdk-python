from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_ec2 as ec2, CfnTag,
)


class MajdvpcCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        cidr = "192.168.0.0/16"
        max_azs = 3
        keyPair = "MajdVPC-KP"
        vpc = ec2.Vpc(
            self,
            id="majdvpc-cdk",
            vpc_name="majdvpc-cdk",
            cidr=cidr,
            max_azs=max_azs,
            nat_gateways=1,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                ####################################################
                #               Public Subnets
                ####################################################
                ec2.SubnetConfiguration(
                    name="public1",
                    cidr_mask=24,
                    subnet_type=ec2.SubnetType.PUBLIC,
                    map_public_ip_on_launch=True
                ),

                ####################################################
                #               Private Subnets
                ####################################################

                ec2.SubnetConfiguration(
                    name="private1",
                    cidr_mask=24,
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                ),

            ]
        )

        #######################################################################
        #                       Security Groups
        #######################################################################

        public_sg = ec2.SecurityGroup(
            self,
            id="public_sg",
            vpc=vpc,
            allow_all_outbound=True,
            description="majd-CDK Public Security Group",
            security_group_name="Majd-CDK-Public-SG"
        )

        # public_sg.security_group_id
        public_sg.connections.allow_from(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(22),
            "ssh"
        )

        private_sg = ec2.SecurityGroup(
            self,
            id="private_sg",
            vpc=vpc,
            allow_all_outbound=True,
            description="majd-CDK Private Security Group",
            security_group_name="Majd-CDK-Private-SG"
        )

        private_sg.connections.allow_from(
            ec2.Peer.ipv4(cidr),
            ec2.Port.tcp(22),
            "ssh"
        )

        #######################################################################
        #                           EC2 Instances
        #######################################################################

        # AMI
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
        )

        # Instance Role and SSM Managed Policy
        role = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))

        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        # Instance
        public_instance = ec2.Instance(self, "publicInstance",
                                       instance_name="majdvpc-cdk-public-EC2",
                                       instance_type=ec2.InstanceType("t3.nano"),
                                       machine_image=amzn_linux,
                                       vpc=vpc,
                                       role=role,
                                       key_name=keyPair,
                                       security_group=public_sg,
                                       vpc_subnets=ec2.SubnetSelection(
                                           subnet_type=ec2.SubnetType.PUBLIC
                                       ),
                                       )

        # Instance
        private_instance = ec2.Instance(self, "privateInstance",
                                        instance_name="majdvpc-cdk-private-EC2",
                                        instance_type=ec2.InstanceType("t3.nano"),
                                        machine_image=amzn_linux,
                                        vpc=vpc,
                                        role=role,
                                        key_name=keyPair,
                                        security_group=private_sg,
                                        )

# When using CDK VPC construct, an Internet Gateway is created by default
# whenever you create a public subnet. The default route is also setup for
# the public subnet.
# https://stackoverflow.com/questions/58812479/how-to-add-an-internet-gateway-to-a-vpc-using-aws-cdk
