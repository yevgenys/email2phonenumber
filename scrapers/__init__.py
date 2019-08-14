import abc


class Scraper(object):
    """
    paren for all scrapers
    """
    def __init__(self, email):
        self.email = email

    @abc.abstractmethod
    def scrape(self):
        pass
