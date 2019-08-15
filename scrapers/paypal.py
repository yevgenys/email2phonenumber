import re

import requests

from globals import YELLOW, ENDC, GREEN
from scrapers import Scraper


class PayPal(Scraper):
    def scrape(self):
        print("Scraping Paypal...")
        user_agent = self.user_agents_instance.next()
        proxy = self.proxy_instance.get_random_proxy()

        session = requests.Session()
        response = session.get("https://www.paypal.com/authflow/password-recovery/",
                               headers={"Upgrade-Insecure-Requests": "1",
                                        "User-Agent": user_agent,
                                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                        "Accept-Encoding": "gzip, deflate",
                                        "Accept-Language": "en-US,en;q=0.9",
                                        },
                               proxies=proxy,
                               verify=self.proxy_instance.verify_proxy)

        _csrf = ""
        regex_output = re.search('"_csrf":"([a-zA-Z0-9+\/]+={0,3})"', response.text)
        if regex_output and regex_output.group(1):
            _csrf = regex_output.group(1)
        else:
            print(YELLOW + "Paypal did not report any digits" + ENDC)
            return

        response = session.post("https://www.paypal.com/authflow/password-recovery",
                                headers={"Upgrade-Insecure-Requests": "1",
                                         "Origin": "https://www.paypal.com",
                                         "X-Requested-With": "XMLHttpRequest",
                                         "User-Agent": user_agent,
                                         "Accept": "*/*",
                                         "Referer": "https://www.paypal.com/authflow/password-recovery/",
                                         "Accept-Encoding": "gzip, deflate",
                                         "Accept-Language": "en-US,en;q=0.9",
                                         },
                                data="email=" + self.email +
                                     "&_csrf=" + _csrf,
                                proxies=proxy,
                                verify=self.proxy_instance.verify_proxy)

        _csrf = _sessionID = jse = ""
        regex_output = re.search('"_csrf":"([a-zA-Z0-9+\/]+={0,3})"', response.text)
        if regex_output and regex_output.group(1): _csrf = regex_output.group(1)

        regex_output = re.search('_sessionID" value="(\w+)"', response.text)
        if regex_output and regex_output.group(1): _sessionID = regex_output.group(1)

        regex_output = re.search('jse="(\w+)"', response.text)
        if regex_output and regex_output.group(1): jse = regex_output.group(1)

        if not _csrf or not _sessionID or not jse:
            print(YELLOW + "Paypal did not report any digits" + ENDC)
            return

        response = session.post("https://www.paypal.com/auth/validatecaptcha",
                                headers={"Upgrade-Insecure-Requests": "1",
                                         "Origin": "https://www.paypal.com",
                                         "X-Requested-With": "XMLHttpRequest",
                                         "User-Agent": user_agent,
                                         "Content-Type": "application/x-www-form-urlencoded",
                                         "Accept": "*/*",
                                         "Referer": "https://www.paypal.com/authflow/password-recovery/",
                                         "Accept-Encoding": "gzip, deflate",
                                         "Accept-Language": "en-US,en;q=0.9",
                                         },
                                data="captcha=" +
                                     "&_csrf=" + _csrf +
                                     "&_sessionID=" + _sessionID +
                                     "&jse=" + jse +
                                     "&ads_token_js=b2c9ad327f5fa65af5a0a0a4cfa912d5cadf0f593027afffadd959390753d44d" +
                                     "&afbacc5007731416=2e21541bb2d5470b",  # TODO
                                proxies=proxy,
                                verify=self.proxy_instance.verify_proxy)

        regex_output = re.search('"clientInstanceId":"([a-zA-Z0-9-]+)"', response.text)
        if regex_output and regex_output.group(1):
            client_instance_id = regex_output.group(1)
        else:
            print(YELLOW + "Paypal did not report any digits" + ENDC)
            return

        response = session.get("https://www.paypal.com/authflow/entry/?clientInstanceId=" + client_instance_id,
                               headers={"Upgrade-Insecure-Requests": "1",
                                        "User-Agent": user_agent,
                                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                        "Referer": "https://www.paypal.com/authflow/password-recovery/",
                                        "Accept-Encoding": "gzip, deflate",
                                        "Accept-Language": "en-US,en;q=0.9",
                                        },
                               proxies=proxy,
                               verify=self.proxy_instance.verify_proxy)

        last_digits = ""
        regex_output = re.search("Mobile <span.+((\d+)\W+(\d+))<\/span>", response.text)
        if regex_output and regex_output.group(3):
            last4 = regex_output.group(3)
            print(GREEN + "Pyapal reports that the last " + len(
                regex_output.group(3)) + " digits are: " + last_digits + ENDC)

            if regex_output.group(2):
                firstDigit = regex_output.group(2)
                print(GREEN + "Paypal reports that the first digit is: " + regex_output.group(2) + ENDC)

            if regex_output.group(1):
                print(GREEN + "Paypal reports that the length of the phone number (without country code) is " + len(
                    regex_output.group(1)) + " digits" + ENDC)  # TODO: remove spaces

        else:
            print(YELLOW + "Paypal did not report any digits" + ENDC)
