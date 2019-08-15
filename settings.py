import os


class Settings:
    """
    note: this file should be in root of the project, otherwice tweak root_dit
    """
    verifyProxy = False
    root_dir = os.path.dirname(os.path.realpath(__file__))
