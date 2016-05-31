"""
Various utility methods for dealing with AWS/SAVI clients
"""
import os
from aws import AwsClient
from vino.servers import ServerManager

def get_aws_client():
    """
    Returns clients for AWS
    """
    
    if os.environ.get('AWS_DEFAULT_REGION'):
        return AwsClient(aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"], 
                        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
                        region=os.environ['AWS_DEFAULT_REGION'])
    else:
        return AwsClient(aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"], 
                        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"])

def get_savi_client():
    """
    Returns clients for SAVI
    """
    server_manager = ServerManager(os.environ["OS_USERNAME"],
                                   os.environ["OS_PASSWORD"],
                                   os.environ["OS_REGION_NAME"],
                                   os.environ["OS_TENANT_NAME"])
    return server_manager
