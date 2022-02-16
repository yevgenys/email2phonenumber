import logging
import re
import requests
from scrapers import Scraper


class LastPass(Scraper):
    logger = logging.getLogger(__name__)

    def scrape(self):
        self.logger.info("Scraping Lastpass...")
        user_agent = self.user_agents_instance.next()
        proxy = self.proxy_instance.get_random_proxy()
        session = requests.Session()
        response = session.get("https://lastpass.com/recover.php",
                               headers={"Upgrade-Insecure-Requests": "1",
                                        "User-Agent": user_agent,
                                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                        "Accept-Encoding": "gzip, deflate",
                                        "Accept-Language": "en-US,en;q=0.9",
                                        },
                               proxies=proxy,
                               verify=self.proxy_instance.verify_proxy)

        csrf_token = re.search('<input type="hidden" name="token" value="(.+?)">', response.text).group(1)

        response = session.post("https://lastpass.com/recover.php",
                                headers={"Cache-Control": "max-age=0",
                                         "Origin": "https://lastpass.com",
                                         "Upgrade-Insecure-Requests": "1",
                                         "Content-Type": "application/x-www-form-urlencoded",
                                         "User-Agent": user_agent,
                                         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                         "Referer": "https://lastpass.com/",
                                         "Accept-Encoding": "gzip, deflate",
                                         "Accept-Language": "en-US,en;q=0.9",
                                         },
                                data="cmd=sendemail" +
                                     "&token=" + csrf_token +
                                     "&username=" + self.email,
                                proxies=proxy,
                                verify=self.proxy_instance.verify_proxy)
        regex_output = re.search("We sent an SMS with a verification code to .*>(\+?)(.+([0-9]{2}))<\/strong>",
                                 response.text)
        if regex_output and regex_output.group(3):
            last_two_digits = regex_output.group(3)
            self.logger.info(
                self.colors.GREEN + "Lastpass reports that the last 2 digits are: " + last_two_digits + self.colors.ENDC)

            if regex_output.group(1):
                self.logger.info(self.colors.GREEN + "Lastpass reports a non US phone number" + self.colors.ENDC)
                self.logger.info(
                    self.colors.GREEN + "Lastpass reports that the length of the phone number (including country code) is " + str(
                        len(regex_output.group(2).replace("-", ""))) + " digits" + self.colors.ENDC)
            else:
                self.logger.info(self.colors.GREEN + "Lastpass reports a US phone number" + self.colors.ENDC)
                self.logger.info(
                    self.colors.GREEN + "Lastpass reports that the length of the phone number (without country code) is " + str(
                        len(regex_output.group(2).replace("-", ""))) + " digits" + self.colors.ENDC)
        else:
            self.logger.warning(self.colors.YELLOW + "Lastpass did not report any digits" + self.colors.ENDC)
