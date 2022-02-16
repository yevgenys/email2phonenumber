import logging
import re
import requests
from scrapers import Scraper


class Ebay(Scraper):
    logger = logging.getLogger(__name__)

    def scrape(self):
        self.logger.info("Scraping Ebay...")
        user_agent = self.user_agents_instance.next()
        proxy = self.proxy_instance.get_random_proxy()

        session = requests.Session()
        response = session.get(
            "https://fyp.ebay.com/EnterUserInfo?ru=https%3A%2F%2Fwww.ebay.com%2F&gchru=&clientapptype=19&rmvhdr=false",
            headers={"Upgrade-Insecure-Requests": "1",
                     "User-Agent": user_agent,
                     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                     "Accept-Encoding": "gzip, deflate",
                     "Accept-Language": "en-US,en;q=0.9",
                     },
            proxies=proxy,
            verify=self.proxy_instance.verify_proxy)

        regex_output = re.search(r'value="(\w{60,})"', response.text)
        if regex_output and regex_output.group(1):
            regex_input = regex_output.group(1)
        else:
            self.logger.warning(self.colors.YELLOW + "Ebay did not report any digits" + self.colors.ENDC)
            return

        response = session.post(
            "https://fyp.ebay.com/EnterUserInfo?ru=https%3A%2F%2Fwww.ebay.com%2F&gchru=&clientapptype=19&rmvhdr=false",
            headers={"Cache-Control": "max-age=0",
                     "Origin": "https://fyp.ebay.com",
                     "Upgrade-Insecure-Requests": "1",
                     "Content-Type": "application/x-www-form-urlencoded",
                     "User-Agent": user_agent,
                     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                     "Referer": "https://fyp.ebay.com/EnterUserInfo?ru=https%3A%2F%2Fwww.ebay.com%2F&clientapptype=19&signInUrl=https%3A%2F%2Fwww.ebay.com%2Fsignin%3Ffyp%3Dsgn%26siteid%3D0%26co_partnerId%3D0%26ru%3Dhttps%253A%252F%252Fwww.ebay.com%252F&otpFyp=1",
                     "Accept-Encoding": "gzip, deflate",
                     "Accept-Language": "en-US,en;q=0.9",
                     },
            data="ru=https%253A%252F%252Fwww.ebay.com%252F" +
                 "&showSignInOTP=" +
                 "&signInUrl=" +
                 "&clientapptype=19" +
                 "&reqinput=" + regex_input +
                 "&rmvhdr=false" +
                 "&gchru=&__HPAB_token_text__=" +
                 "&__HPAB_token_string__=" +
                 "&pageType=" +
                 "&input=" + self.email,
            proxies=proxy,
            verify=self.proxy_instance.verify_proxy)

        regex_output = re.search("text you at ([0-9]{1})xx-xxx-xx([0-9]{2})", response.text)
        if regex_output:
            if regex_output.group(1):
                first_digit = regex_output.group(1)
                self.logger.info(self.colors.GREEN + "Ebay reports that the first digit is: " + first_digit + self.colors.ENDC)
            if regex_output.group(2):
                last_two_digits = regex_output.group(2)
                self.logger.info(self.colors.GREEN + "Ebay reports that the last 2 digits are: " + last_two_digits + self.colors.ENDC)
        else:
            self.logger.warning(self.colors.YELLOW + "Ebay did not report any digits" + self.colors.ENDC)
