import os


class Settings:
    """
    note: this file should be in root of the project, otherwice tweak root_dit
    """
    def __init__(self, parsed_args):
        self.verify_proxy = False
        self.root_dir = os.path.dirname(os.path.realpath(__file__))
        self.region = parsed_args.region if 'region' in parsed_args else 'US'
        self.path_to_proxy_file = parsed_args.proxies
