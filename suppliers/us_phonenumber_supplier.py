import os
import re
import time
import zipfile
from itertools import product

import requests
from bs4 import BeautifulSoup

from suppliers import Supplier


class USPhoneNumberSupplier(Supplier):
    def __init__(self, cache, user_agent_instance, proxy_instance, mask):
        self.user_agent_instance = user_agent_instance
        self.proxy_instance = proxy_instance
        self.cache = cache
        self.mask = mask  # mask will be copied, so we safe to modify it

    def _cache_valid_block_numbers(self, state, areacode):
        proxy = self.proxy_instance.get_random_proxy()
        session = requests.Session()
        # We need the cookies or it will error
        session.get("https://www.nationalpooling.com/pas/blockReportSelect.do?reloadModel=N")
        response = session.post("https://www.nationalpooling.com/pas/blockReportDisplay.do",
                                headers={"Upgrade-Insecure-Requests": "1",
                                         "User-Agent": self.user_agent_instance.next(),
                                         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                         "Referer": "https://www.nationalpooling.com/pas/blockReportSelect.do?reloadModel=Y",
                                         "Accept-Encoding": "gzip, deflate, br",
                                         "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
                                         "Origin": "https://www.nationalpooling.com",
                                         "Content-Type": "application/x-www-form-urlencoded",
                                         "DNT": "1"
                                         },
                                data="stateAbbr=" + state +
                                     "&npaId=" + areacode +
                                     "&rtCntrId=" + "ALL" +
                                     "&reportType=" + "3",
                                proxies=proxy,
                                verify=self.proxy_instance.verify_proxy)

        soup = BeautifulSoup(response.text, 'html.parser')
        areacode_cells = soup.select("form table td:nth-of-type(1)")
        for areaCodeCell in areacode_cells:
            if areaCodeCell.string and areaCodeCell.string.strip() == areacode:
                exchange = areaCodeCell.next_sibling.next_sibling.string.strip()
                block_number = areaCodeCell.next_sibling.next_sibling.next_sibling.next_sibling.string.strip()

                if areacode not in self.cache:
                    self.cache[areacode] = {}
                    self.cache[areacode][exchange] = {}
                    self.cache[areacode][exchange]['blockNumbers'] = []
                elif exchange not in self.cache[areacode]:
                    self.cache[areacode][exchange] = {}
                    self.cache[areacode][exchange]['blockNumbers'] = []

                self.cache[areacode][exchange]['blockNumbers'].append(
                    block_number)  # Temporarely we store the invalid blocknumbers

        for areacode in self.cache:  # Let's switch invalid blocknumbers for valid ones
            for exchange in self.cache[areacode]:
                self.cache[areacode][exchange]['blockNumbers'] = [n for n in
                                                                  ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] if
                                                                  n not in self.cache[areacode][exchange][
                                                                      'blockNumbers']]

    def supply(self):
        possible_phone_numbers = []
        nanpa_file_url = "https://www.nationalnanpa.com/nanp1/allutlzd.zip"
        file = self._read_or_download_nanpa_zip_archive(nanpa_file_url)
        # Only assigned area codes and exchanges
        assigned_regex = '\s[0-9A-Z\s]{4}\t.*\t[A-Z\-\s]+\t[0-9\\]*[\t\s]+AS'
        # Area code + exchange
        areacode_exchange_regex = re.sub("X", "[0-9]{1}", "(" + self.mask[:3] + "-" + self.mask[3:6] + ")")
        # Format: [state, areacode-exchange]
        possible_areacode_exchanges = re.findall("([A-Z]{2})\s\t" + areacode_exchange_regex + assigned_regex, file)

        remaining_x = self.mask[7:].count("X")
        masked_phone_formatted = self.mask[7:].replace("X", "{}")
        for possible_areacode_exchange in possible_areacode_exchanges:
            state = possible_areacode_exchange[0]
            areacode = possible_areacode_exchange[1].split("-")[0]
            exchange = possible_areacode_exchange[1].split("-")[1]

            if areacode not in self.cache:
                self._cache_valid_block_numbers(state, areacode)

            if self.mask[6] == 'X':  # Check for available block numbers for that area code and exchange
                if areacode in self.cache and exchange in self.cache[areacode]:
                    block_numbers = self.cache[areacode][exchange]['blockNumbers']
                else:
                    block_numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

            else:  # User provided blocknumber
                if areacode in self.cache and exchange in self.cache[areacode] and self.mask[6] not in \
                        self.cache[areacode][exchange]['blockNumbers']:  # User provided invalid block number
                    block_numbers = []
                else:
                    block_numbers = [self.mask[6]]

            for blockNumber in block_numbers:  # Add the rest of random subscriber number digits
                for x in product("0123456789", repeat=remaining_x):
                    possible_phone_numbers.append(areacode + exchange + blockNumber + masked_phone_formatted.format(*x))

        return possible_phone_numbers

    def _read_or_download_nanpa_zip_archive(self, nanpa_file_url):
        #TODO: use tmpfile here
        if not os.path.exists("./allutlzd.zip") or (time.time() - os.path.getmtime("./allutlzd.zip")) > (24 * 60 * 60):
            print("NANPA file missing or needs to be updated. Downloading now...")
            response = requests.get(nanpa_file_url)
            with open("allutlzd.zip", "wb") as code:
                code.write(response.content)
            print("NANPA file downloaded successfully")

        with zipfile.ZipFile('./allutlzd.zip', 'r') as archive:
            return archive.read('allutlzd.txt')
