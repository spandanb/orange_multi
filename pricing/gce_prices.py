import json
from pprint import pprint

def get_prices(filepath="./data/gce_prices.json"):
    """
    Get the prices at the filepath
    """
    with open(filepath) as fileptr:    
        data = json.load(fileptr)
        pprint(data)


if __name__ == "__main__":
    get_prices()

