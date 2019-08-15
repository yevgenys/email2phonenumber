import re
import os
import requests
import time
import zipfile
from bs4 import BeautifulSoup
from itertools import product

class USPhoneNumberGenerator(object):
    def __init__(self, cache, user_agent_instance, proxy_instance, verify_proxy):
        self.cache = cache
        self.user_agent_instance = user_agent_instance
        self.proxy_instance = proxy_instance
        self.verify_proxy = verify_proxy

    def cacheValidBlockNumbers(self, state, areacode):
        proxy = self.proxy_instance.get_random_proxy()
        session = requests.Session()
        session.get(
            "https://www.nationalpooling.com/pas/blockReportSelect.do?reloadModel=N")  # We need the cookies or it will error
        response = session.post("https://www.nationalpooling.com/pas/blockReportDisplay.do",
                                headers={"Upgrade-Insecure-Requests": "1",
                                        "User-Agent": self.userAgents.next(),
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
                                verify=self.verify_proxy)

        soup = BeautifulSoup(response.text, 'html.parser')
        availableBlockNumbers = []
        areacodeCells = soup.select("form table td:nth-of-type(1)")
        for areaCodeCell in areacodeCells:
            if areaCodeCell.string and areaCodeCell.string.strip() == areacode:
                exchange = areaCodeCell.next_sibling.next_sibling.string.strip()
                blockNumber = areaCodeCell.next_sibling.next_sibling.next_sibling.next_sibling.string.strip()

                if areacode not in self.cache:
                    self.cache[areacode] = {}
                    self.cache[areacode][exchange] = {}
                    self.cache[areacode][exchange]['blockNumbers'] = []
                elif exchange not in self.cache[areacode]:
                    self.cache[areacode][exchange] = {}
                    self.cache[areacode][exchange]['blockNumbers'] = []

                self.cache[areacode][exchange]['blockNumbers'].append(blockNumber)  # Temporarely we store the invalid blocknumbers

        for areacode in self.cache:  # Let's switch invalid blocknumbers for valid ones
            for exchange in self.cache[areacode]:
                self.cache[areacode][exchange]['blockNumbers'] = [n for n in
                                                                    ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] if
                                                                    n not in self.cache[areacode][exchange][
                                                                        'blockNumbers']]

    def getPossiblePhoneNumbers(self, maskedPhone):
        possiblePhoneNumbers = []
        nanpaFileUrl = "https://www.nationalnanpa.com/nanp1/allutlzd.zip"

        # Check if we need to download/update NANPA file
        if not os.path.exists("./allutlzd.zip") or (time.time() - os.path.getmtime("./allutlzd.zip")) > (24 * 60 * 60):
            print("NANPA file missing or needs to be updated. Downloading now...")
            response = requests.get(nanpaFileUrl)
            with open("allutlzd.zip", "wb") as code:
                code.write(response.content)
            print("NANPA file downloaded successfully")

        archive = zipfile.ZipFile('./allutlzd.zip', 'r')
        file = archive.read('allutlzd.txt')
        archive.close()

        assignedRegex = '\s[0-9A-Z\s]{4}\t.*\t[A-Z\-\s]+\t[0-9\\]*[\t\s]+AS'  # Only assigned area codes and exchanges
        areacodeExchangeRegex = re.sub("X", "[0-9]{1}",
                                    "(" + maskedPhone[:3] + "-" + maskedPhone[3:6] + ")")  # Area code + exchange
        possibleAreacodeExchanges = re.findall("([A-Z]{2})\s\t" + areacodeExchangeRegex + assignedRegex,
                                            file)  # Format: [state, areacode-exchange]

        remainingX = maskedPhone[7:].count("X")
        maskedPhoneFormatted = maskedPhone[7:].replace("X", "{}")
        for possibleAreacodeExchange in possibleAreacodeExchanges:
            state = possibleAreacodeExchange[0]
            areacode = possibleAreacodeExchange[1].split("-")[0]
            exchange = possibleAreacodeExchange[1].split("-")[1]

            if areacode not in self.cache:
                self.cacheValidBlockNumbers(state, areacode)

            if maskedPhone[6] == 'X':  # Check for available block numbers for that area code and exchange
                if areacode in self.cache and exchange in self.cache[areacode]:
                    blockNumbers = self.cache[areacode][exchange]['blockNumbers']
                else:
                    blockNumbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

            else:  # User provided blocknumber
                if areacode in self.cache and exchange in self.cache[areacode] and maskedPhone[6] not in \
                        self.cache[areacode][exchange]['blockNumbers']:  # User provided invalid block number
                    blockNumbers = []
                else:
                    blockNumbers = [maskedPhone[6]]

            for blockNumber in blockNumbers:  # Add the rest of random subscriber number digits
                for x in product("0123456789", repeat=remainingX):
                    possiblePhoneNumbers.append(areacode + exchange + blockNumber + maskedPhoneFormatted.format(*x))

        return possiblePhoneNumbers


class PhonenumberGenerator(object):
    def __init__(self, settings, cache, user_agent_instance, proxy_instance, colors):
        self.region = settings.region
        self.colors = colors
        self.map_region = {
            "US": USPhoneNumberGenerator(cache, user_agent_instance, proxy_instance, settings.verify_proxy)
        }

    def getPossiblePhoneNumbers(self, maskedPhone):
        return self.map_region[self.region].getPossiblePhoneNumbers(maskedPhone)
    
    def generate(self, args):
        if not re.match("^[0-9X]{10}", args.mask):
            exit(self.colors.RED + "You need to pass a US phone number masked as in: 555XXX1234" + self.colors.ENDC)
        possiblePhoneNumbers = self.getPossiblePhoneNumbers(args.mask)
        if args.file:
            with open(args.file, 'w') as f:
                f.write('\n'.join(possiblePhoneNumbers))
            print(self.colors.GREEN + "Dictionary created successfully at " + os.path.realpath(f.name) + self.colors.ENDC)
            f.close()

        else:
            print(self.colors.GREEN + "There are " + str(len(possiblePhoneNumbers)) + " possible numbers" + self.colors.ENDC)
            print(self.colors.GREEN + str(possiblePhoneNumbers) + self.colors.ENDC)


