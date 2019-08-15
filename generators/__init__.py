import abc


class Generator(object):
    """
    paren for all scrapers
    """
    def __init__(self, email, user_agents, proxy):
        self.email = email
        self.user_agents_instance = user_agents
        self.proxy_instance = proxy

    @abc.abstractmethod
    def generate(self):
        pass
