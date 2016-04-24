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
