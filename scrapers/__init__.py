import abc


class Scraper(object):
    """
    parent for all scrapers
    """
    def __init__(self, email, user_agents, proxy, colors):
        self.email = email
        self.user_agents_instance = user_agents
        self.proxy_instance = proxy
        self.colors = colors

    @abc.abstractmethod
    def scrape(self):
        pass
