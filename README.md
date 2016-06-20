Orange Multi Domain
===================
Framework for extending SDI to legacy and  multi-domain orchestration.

Usage
=====
VINOENV=/path/to/vino-virtualenv
source $VINOENV/bin/activate

Specify credentials: 

`$ cp secret_envvars.sample.sh secret_envvars.sh`

Fill in the appropriate values and

`source ./secret_envvars.sh`

To deploy the wordpress example over AWS and SAVI, run 
`python orange_parser.py -s <SAVI Keyname> -a <AWS Keyname>`

Then run the following to configure the nodes:
`configure_wordpress.sh`

To cleanup:
`python orange_parser.py -c`


Dependencies
============
boto3, 
ansible
requests

NOTES
=====
env vars override topology, specifically specifying region-name, tenat has no 
effect since nodes are booted based on env vars.
