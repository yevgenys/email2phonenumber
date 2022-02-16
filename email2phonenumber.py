#!/usr/bin/env python
import argparse
import os
import random
import re
import urllib
from collections import deque

import requests

from bruteforcers.amazon import Amazon
from bruteforcers.twitter import Twitter
from constants import Colors, Action, PHONE_NUMBER
from core.proxy import Proxy
from core.user_agents import UserAgentsCycle
from scrapers.ebay import Ebay
from scrapers.lastpass import LastPass
from scrapers.paypal import PayPal
from settings import Settings
from suppliers.agnostic_supplier import AgnosticSupplier

from itertools import product
from bs4 import BeautifulSoup
import logging

# Basic configuration for logging
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

requests.packages.urllib3.disable_warnings()


def bruteforce(args, colors, user_agents_instance, proxy_instance, settings):
    if args.email and not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", args.email):
        exit(colors.RED + "Email is invalid" + colors.ENDC)
    if (args.mask and args.file) or (not args.mask and not args.file):
        exit(colors.RED + "You need to provide a masked number or a file with numbers to try" + colors.ENDC)
    if args.mask and not re.match("^[0-9X]{10}", args.mask): exit(
        colors.RED + "You need to pass a 10-digit US phone number masked as in: 555XXX1234" + colors.ENDC)
    if args.file and not os.path.isfile(args.file): exit(colors.RED + "You need to pass a valid file path" + colors.ENDC)
    print(f"Looking for the phone number associated to {args.email}...")

    supplier_class = AgnosticSupplier.get_supplier(PHONE_NUMBER)
    phonenumber_supplier = supplier_class(settings, user_agents_instance, proxy_instance, colors, args.mask)
    if args.mask:
        possible_phone_numbers = phonenumber_supplier.get()
    else:
        possible_phone_numbers = phonenumber_supplier.get_from_dump(args.file)

    bruteforcers = get_bruteforcers(args, possible_phone_numbers, user_agents_instance, proxy_instance)
    deque(map(lambda b: b.bruteforce(), bruteforcers))


def get_bruteforcers(args, possible_phone_numbers, user_agents_instance, proxy_instance) -> list:
    bruteforcers_parameters = dict(possiblePhoneNumbers=possible_phone_numbers,
                                   email=args.email,
                                   verbose=args.verbose,
                                   user_agents_instance=user_agents_instance,
                                   proxy_instance=proxy_instance)
    twitter = Twitter(**bruteforcers_parameters)
    if args.quiet:
        return [twitter]
    return [twitter, Amazon(**bruteforcers_parameters)]


#TODO: move this also to agnostic class like suppliers
def start_scraping(email, quiet_mode, user_agents_instance, proxy_instance, colors):
    scrapers = get_scrapers(email, 
                            quiet_mode, 
                            user_agents_instance, 
                            proxy_instance,
                            colors)
    deque(map(lambda s: s.scrape(), scrapers))


def get_scrapers(email, quiet_mode, user_agents_instance, proxy_instance, colors):
    scraper_parameters = dict(email=email, 
                              user_agents=user_agents_instance, 
                              proxy=proxy_instance, 
                              colors=colors)
    if quiet_mode:
        return [
            PayPal(**scraper_parameters)
        ]
    return [
        Ebay(**scraper_parameters),
        LastPass(**scraper_parameters)
    ]


def parse_arguments():
    parser = argparse.ArgumentParser(description='An OSINT tool to find phone numbers associated to email addresses')
    subparsers = parser.add_subparsers(help='commands', dest='action')
    subparsers.required = True  # python3 compatibility, will generate slightly different error massage then python2
    
    scrape_parser = subparsers.add_parser(Action.SCRAPE, help='scrape online services for phone number digits')
    scrape_parser.add_argument("-e", required=True, metavar="EMAIL", dest="email", help="victim's email address")
    scrape_parser.add_argument("-p", metavar="PROXYLIST", dest="proxies",
                               help="a file with a list of https proxies to use. Format: https://127.0.0.1:8080")
    scrape_parser.add_argument("-q", dest="quiet", action="store_true",
                               help="scrape services that do not alert the victim")
    
    generator_parser = subparsers.add_parser(Action.GENERATE,
                                             help="generate all valid phone numbers based on NANPA's public records")
    generator_parser.add_argument("-m", required=True, metavar="MASK", dest="mask",
                                  help="a masked 10-digit US phone number as in: 555XXX1234")
    generator_parser.add_argument("-o", metavar="FILE", dest="file", help="outputs the list to a dictionary")
    generator_parser.add_argument("-q", dest="quiet", action="store_true",
                                  help="use services that do not alert the victim")
    generator_parser.add_argument("-p", metavar="PROXYLIST", dest="proxies",
                                  help="a file with a list of https proxies to use. Format: https://127.0.0.1:8080")
    generator_parser.add_argument("-r", metavar="REGION", dest="region", help="region, default region is US")
    
    bruteforce_parser = subparsers.add_parser(Action.BRUTE_FORCE,
                                              help='bruteforce using online services to find the phone number')
    bruteforce_parser.add_argument("-e", required=True, metavar="EMAIL", dest="email", help="victim's email address")
    bruteforce_parser.add_argument("-m", metavar="MASK", dest="mask",
                                   help="a masked, 10-digit US phone number as in: 555XXX1234")
    bruteforce_parser.add_argument("-d", metavar="DICTIONARY", dest="file", help="a file with a list of numbers to try")
    bruteforce_parser.add_argument("-p", metavar="PROXYLIST", dest="proxies",
                                   help="a file with a list of HTTPS proxies to use. Format: https://127.0.0.1:8080")
    bruteforce_parser.add_argument("-q", dest="quiet", action="store_true",
                                   help="use services that do not alert the victim")
    bruteforce_parser.add_argument("-v", dest="verbose", action="store_true", help="verbose output")
    
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    settings = Settings(args)
    colors = Colors()
    proxy_instance = Proxy(settings, colors)
    user_agents_instance = UserAgentsCycle(settings)

    if args.action == Action.SCRAPE:
        start_scraping(args.email, args.quiet, user_agents_instance, proxy_instance, colors)
    elif args.action == Action.GENERATE:
        phonenumber_supplier = AgnosticSupplier.get_supplier(PHONE_NUMBER)(settings,
                                                                           user_agents_instance,
                                                                           proxy_instance,
                                                                           colors,
                                                                           args.mask)
        possible_phone_numbers = phonenumber_supplier.get()
        phonenumber_supplier.dump_supplied_phones(args.file, possible_phone_numbers)
    elif args.action == Action.BRUTE_FORCE:
        bruteforce(args, colors, user_agents_instance, proxy_instance, settings)