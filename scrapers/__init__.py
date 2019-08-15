import abc


class Scraper(object):
    """
    paren for all scrapers
    """
    def __init__(self, email, user_agents, proxy):
        self.email = email
        self.user_agents_instance = user_agents
        self.proxy_instance = proxy

    @abc.abstractmethod
    def scrape(self):
        pass
