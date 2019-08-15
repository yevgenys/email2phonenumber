from colorama import init, Fore, Style

init()

GREEN = Fore.LIGHTGREEN_EX
YELLOW = Fore.LIGHTYELLOW_EX
RED = Fore.LIGHTRED_EX
ENDC = Style.RESET_ALL


class Actions(object):
    SCRAPE = 'scrape'
    GENERATE = 'generate'
    BRUTE_FORCE = 'bruteforce'
