import logging
import os
import re
import requests
import time
import tempfile
import zipfile
from copy import copy
from itertools import product

from bs4 import BeautifulSoup


class USPhoneNumberSupplier:
    def __init__(self, cache, user_agent_instance, proxy_instance, colors, mask):
        self.user_agent_instance = user_agent_instance
        self.proxy_instance = proxy_instance
        self.cache = cache
        self.mask = copy(mask)
        self.colors = colors
        self.tmp_file = tempfile.mktemp()
        self.logger = logging.getLogger(__name__)

    def _cache_valid_block_numbers(self, state, area_code):
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
                                     "&npaId=" + area_code +
                                     "&rtCntrId=" + "ALL" +
                                     "&reportType=" + "3",
                                proxies=proxy,
                                verify=self.proxy_instance.verify_proxy)

        soup = BeautifulSoup(response.text, 'html.parser')
        areacode_cells = soup.select("form table td:nth-of-type(1)")
        for area_code_cell in areacode_cells:
            if area_code_cell.string and area_code_cell.string.strip() == area_code:
                exchange = area_code_cell.next_sibling.next_sibling.string.strip()
                block_number = area_code_cell.next_sibling.next_sibling.next_sibling.next_sibling.string.strip()

                if area_code not in self.cache:
                    self.cache[area_code] = {}
                    self.cache[area_code][exchange] = {}
                    self.cache[area_code][exchange]['blockNumbers'] = []
                elif exchange not in self.cache[area_code]:
                    self.cache[area_code][exchange] = {}
                    self.cache[area_code][exchange]['blockNumbers'] = []

                self.cache[area_code][exchange]['blockNumbers'].append(
                    block_number)  # Temporarely we store the invalid blocknumbers

        for area_code in self.cache:  # Let's switch invalid blocknumbers for valid ones
            for exchange in self.cache[area_code]:
                self.cache[area_code][exchange]['blockNumbers'] = [n for n in
                                                                  ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] if
                                                                  n not in self.cache[area_code][exchange][
                                                                      'blockNumbers']]

    def supply(self):
        if not re.match("^[0-9X]{10}", self.mask):
            exit(self.colors.RED + "You need to pass a US phone number masked as in: 555XXX1234" + self.colors.ENDC)

        possible_phone_numbers = []
        nanpa_file_url = "https://www.nationalnanpa.com/nanp1/allutlzd.zip"
        file = self._read_or_download_nanpa_zip_archive(nanpa_file_url)
        # Only assigned area codes and exchanges
        assigned_regex = r'\s[0-9A-Z\s]{4}\t.*\t[A-Z\-\s]+\t[0-9\\]*[\t\s]+AS'
        # Area code + exchange
        areacode_exchange_regex = re.sub("X", "[0-9]{1}", "(" + self.mask[:3] + "-" + self.mask[3:6] + ")")
        # Format: [state, areacode-exchange]
        possible_areacode_exchanges = re.findall(r"([A-Z]{2})\s\t" + areacode_exchange_regex + assigned_regex, file)

        remaining_unsolved_digits = self.mask[7:].count("X")
        masked_phone_formatted = self.mask[7:].replace("X", "{}")
        for possible_areacode_exchange in possible_areacode_exchanges:
            state = possible_areacode_exchange[0]
            area_code = possible_areacode_exchange[1].split("-")[0]
            exchange = possible_areacode_exchange[1].split("-")[1]

            if area_code not in self.cache:
                self._cache_valid_block_numbers(state, area_code)

            if self.mask[6] == 'X':  # Check for available block numbers for that area code and exchange
                if area_code in self.cache and exchange in self.cache[area_code]:
                    block_numbers = self.cache[area_code][exchange]['blockNumbers']
                else:
                    block_numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

            else:  # User provided blocknumber
                if area_code in self.cache and exchange in self.cache[area_code] and self.mask[6] not in \
                        self.cache[area_code][exchange]['blockNumbers']:  # User provided invalid block number
                    block_numbers = []
                else:
                    block_numbers = [self.mask[6]]

            for blockNumber in block_numbers:  # Add the rest of random subscriber number digits
                for x in product("0123456789", repeat=remaining_unsolved_digits):
                    possible_phone_numbers.append(area_code + exchange + blockNumber + masked_phone_formatted.format(*x))

        return possible_phone_numbers

    def _read_or_download_nanpa_zip_archive(self, nanpa_file_url):                
        if not os.path.exists(self.tmp_file) or (time.time() - os.path.getmtime(self.tmp_file)) > (24 * 60 * 60):
            self.logger.info("NANPA file missing or needs to be updated. Downloading now...")
            response = requests.get(nanpa_file_url)
            with open(self.tmp_file, "wb") as code:
                code.write(response.content)
            self.logger.info("NANPA file downloaded successfully")

        with zipfile.ZipFile(self.tmp_file, 'r') as archive:
            return archive.read('allutlzd.txt')
