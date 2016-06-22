from utils.path import selfpath
import os
import subprocess as sp
import pprint
import json
#See: https://aws.amazon.com/blogs/aws/new-aws-price-list-api/
#See: http://stackoverflow.com/questions/7334035/get-ec2-pricing-programmatically
#See: http://stackoverflow.com/questions/3636578/are-there-any-apis-for-amazon-web-services-pricing


def get_filepath(filename, url):
    """
    Returns the filepath of the `filename`. If file does 
    not exist in local directory, downloads it.
    Arguments:-
        filename
        url
    """
    #Data file are located in ./data
    fpath = os.path.join(selfpath(), "data", filename)
    if not os.path.exists(fpath):
        print "fetching file from {}".format(url)
        #requests was having an issue: https://github.com/kennethreitz/requests/issues/2022
        sp.call(["curl", "-o", filename, url])
    
    return fpath 

def main(region="us-east-1"):
    """
    The workflow for getting prices is as follows:
        - get the offer_code from the offer index
        - get the offer file and parse it 
    """
    #handle indexfile
    fname =  "aws_index.json"
    url = "https://pricing.{}.amazonaws.com/offers/v1.0/aws/index.json".format(region)
    with open(get_filepath(fname, url)) as fileptr:
        indices = json.load(fileptr)
        #Look up the index for ec2
        #This is unnecessary, since the offercode is "AmazonEC2"
        offer_code = indices["offers"]["AmazonEC2"]["offerCode"]

    #handle offerfile
    fname = "aws_{}.json".format(offer_code)
    url = "https://pricing.{}.amazonaws.com/offers/v1.0/aws/{}/current/index.json".format(region, offer_code)
    with open(get_filepath(fname, url)) as fileptr:
        data = json.load(fileptr)
        pprint.pprint(data)




if __name__ == "__main__":
    main()

