Orange Multi Domain
===================
Framework for extending SDI to legacy and  multi-domain orchestration.

Usage
=====
Specify credentials: 

`$ cp secret_envvars.sample.sh secret_envvars.sh`

Fill in the appropriate values and

`source ./secret_envvars.sh`

To deploy the wordpress example over AWS and SAVI, run vino_wordpress.sh

Dependencies
============
boto3, i.e. pip install boto3
ansible
