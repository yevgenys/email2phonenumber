import abc

from constants import Colors
from core.user_agents import UserAgentsCycle
from core.proxy import Proxy


class Bruteforcer:
    def __init__(self, possible_phone_numbers, email, verbose, user_agents_instance: UserAgentsCycle, proxy_instance: Proxy):
        self.possible_phone_numbers = possible_phone_numbers
        self.email = email
        self.verbose = verbose
        self.user_agents_instance = user_agents_instance
        self.proxy_instance = proxy_instance
        self.colors = Colors()

    @abc.abstractmethod
    def bruteforce(self):
        pass
