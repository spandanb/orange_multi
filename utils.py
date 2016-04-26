import yaml

def read_yaml(template_file=""):
    """
    reads topology file at `template_file` and
    returns corresponding object
    """

    with open(template_file, 'r') as stream:
        try:
            template = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)

    return template

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
    ExceptionClass.__init__ = exception_init

    #Now raise the exception
    raise ExceptionClass(exception_msg)

