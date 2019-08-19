import abc


class Bruteforcer:
    def __init__(self, possible_phone_numbers, email, verbose, user_agents_instance, proxy_instance):
        self.possible_phone_numbers = possible_phone_numbers
        self.email = email
        self.verbose = verbose
        self.user_agents_instance = user_agents_instance
        self.proxy_instance = proxy_instance

    @abc.abstractmethod
    def bruteforce(self):
        pass
