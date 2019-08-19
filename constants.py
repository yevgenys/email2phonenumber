from colorama import init, Fore, Style


class Colors:
    def __init__(self):
        init()
    
        self.GREEN = Fore.LIGHTGREEN_EX
        self.YELLOW = Fore.LIGHTYELLOW_EX
        self.RED = Fore.LIGHTRED_EX
        self.ENDC = Style.RESET_ALL


class Action:
    SCRAPE = 'scrape'
    GENERATE = 'generate'
    BRUTE_FORCE = 'bruteforce'


PHONE_NUMBER = 'PHONE_NUMBER'
