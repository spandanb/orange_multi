import yaml
import sys

def read_yaml(filepath=""):
    """
    reads topology file at `filepath` and
    returns corresponding object
    """

    with open(filepath, 'r') as stream:
        try:
            template = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)

    return template

def write_yaml(data, filepath=""):
    """
    Writes obj in YAML format at filename
    """
    with open(filepath, 'w') as filedesc:
        filedesc.write(yaml.dump(data))

def create_and_raise(exception_name, exception_msg):
    """
    Creates a new Exception sub class and raises it.
    Arguments:
        exception_name:- name of exception class
        exception_msg: msg associated with exception
    """
    #Create exception
    ExceptionClass = type(exception_name, (Exception, ), {})
    #define __init__ method
    def exception__init__(self, message):
        super(ExceptionClass, self).__init__(message)
    ExceptionClass.__init__ = exception__init__

    #Now raise the exception
    raise ExceptionClass(exception_msg)

def printobj(obj):
    pprint.pprint(obj)
    #print json.dumps(obj, sort_keys=True, indent=4)


