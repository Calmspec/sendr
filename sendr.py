"""Sendr (modified by calm, discord @m8ov original by Cloudzik133)"""

import itertools
import string
import queue
import threading
from time import sleep, time
import traceback
import random
import os
from signal import signal, SIGINT
import requests
import json
from pathlib import Path
from urllib3.exceptions import MaxRetryError
import sys

VERSION = "1.0.5"

class Config:
    """Config class (modified by calm, discord @m8ov)"""
    def __init__(self):
        self.config = None
        self.load_config()

    def load_config(self):
        with open('data/config.json', 'a') as f:
            if os.path.getsize("data/config.json") == 0:
                f.write("{}")
                f.close()
        

    def get(self, key):
        with open('data/config.json', 'r') as f:
            self.config = json.load(f)
        try:
            return self.config[key]
        except KeyError:
            return None
    
    def set(self, key, value):
        with open('data/config.json', 'r') as f:
            self.config = json.load(f)
        self.config[key] = value
        with open('data/config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
        
    def get_all(self):
        with open('data/config.json', 'r') as f:
            self.config = json.load(f)
        return self.config


###############################################################
#                      Close on ctrl+c                        #
###############################################################
@staticmethod
def handler(signal_received, frame):
    # Handle any cleanup here
    print('\nSIGINT or CTRL-C detected. Exiting gracefully')
    exit(0)

signal(SIGINT, handler)





confirmators =  ["y", "yes", "1", "true", "t"]
negators =      ["n", "no", "0", "false", "f"]

os.makedirs("logs", exist_ok=True)
os.makedirs("results", exist_ok=True)  
os.makedirs("data", exist_ok=True)


def create_empty_file(file_path):
    file_path = Path(file_path)
    
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding='utf-8'):
            pass

def clear_file(file_path):
    file_path = Path(file_path)
    
    if file_path.exists():
        with file_path.open("w", encoding='utf-8'):
            pass


create_empty_file("logs/log.txt")
clear_file("logs/log.txt")


create_empty_file("results/hits.txt")

create_empty_file("data/names_to_check.txt")

create_empty_file("logs/error.txt")
clear_file("logs/error.txt")

create_empty_file("data/proxies.txt")

with Path("data/proxies.txt").open("r", encoding='utf-8') as proxies_file:
    proxies = proxies_file.read().splitlines()


config = Config()
lock = threading.Lock()


if len(proxies) == 0:
    proxies = [None]
proxy_cycle = itertools.cycle(proxies)


#Globals
RPS =       0
REQUESTS =  0
WORKS =     0
TAKEN =     0
DEACTIVATE = False


class Logger:
    """Logger class (modified by calm, discord @m8ov)"""
    def __init__(self, file_name: str):
        """Initiate the class"""
        self.file_name = file_name
        self.file = open(self.file_name, "a")

    def log(self, message: str):
        """Log a message to the file"""
        self.file.write(f"{message}\n")
        self.file.flush()

    def close(self):
        """Close the file"""
        self.file.close()


class _Colors:
    """Menu colors"""
    @staticmethod
    def _color_code(code):
        """Static method to format color codes"""
        return f'\033[{code}m'


    ENDC: str =         _color_code(0)
    BOLD: str =         _color_code(1)
    UNDERLINE: str =    _color_code(4)
    BLACK: str =        _color_code(30)
    RED: str =          _color_code(31)
    GREEN: str =        _color_code(32)
    YELLOW: str =       _color_code(33)
    BLUE: str =         _color_code(34)
    MAGENTA: str =      _color_code(35)
    CYAN: str =         _color_code(36)
    WHITE: str =        _color_code(37)
    REDBG: str =        _color_code(41)
    GREENBG: str =      _color_code(42)
    YELLOWBG: str =     _color_code(43)
    BLUEBG: str =       _color_code(44)
    MAGENTABG: str =    _color_code(45)
    CYANBG: str =       _color_code(46)
    WHITEBG: str =      _color_code(47)
    GREY: str =         _color_code(90)


Colors = _Colors()

Logger = Logger("logs/log.txt")


Logger.log(f"sendrChecker started at {time()} (modified by calm, discord @m8ov)")


def clear():
    """Clear the screen"""
    os.system('cls' if os.name=='nt' else 'clear')

clear()

class Pomelo:
    """sendr Checker"""
    def __init__(self):
        """Initiate the class"""
        self.endpoint = "https://discord.com/api/v9"
        self.headers_post = {"Content-Type": "application/json"}
        self.session = requests.Session()
        self.proxies_not_working = []
        self.remove_proxies = config.get("remove_proxies")
        self.timeout = config.get("timeout")
        if self.timeout is None:
            self.timeout = 30

        Logger.log(f"Timeout set to {self.timeout} (modified by calm, discord @m8ov)")
        Logger.log(f"Remove proxies set to {self.remove_proxies} (modified by calm, discord @m8ov)")
        Logger.log(f"Headers set to {self.headers_post} (modified by calm, discord @m8ov)")

    def proxy_err(self, name, proxy, proxy_cycle):
        name = [name, next(proxy_cycle)]
        Logger.log(f"ReadTimeout with proxy {proxy} (modified by calm, discord @m8ov)")
        if self.remove_proxies and proxy != None:
            Logger.log(f"Removing proxy {proxy} (modified by calm, discord @m8ov)")
            self.proxies_not_working.append(proxy)
        
        
    def  check(self, name: list):
        """Check if the name is available"""

        global RPS, REQUESTS, WORKS, TAKEN, DEACTIVATE
        while not DEACTIVATE:
            try:
                try:
                    name, proxy = name
                # only name is passed
                except ValueError:
                    if proxy_cycle is None:
                        proxy = None
                    else:
                        proxy = next(proxy_cycle)
                        if len(self.proxies_not_working) >= len(proxies):
                            Logger.log(f"Exiting because all proxies are not working (modified by calm, discord @m8ov)")
                            
                            DEACTIVATE = True
                            # clear queue
                            Logger.log(f"Clearing queue (modified by calm, discord @m8ov)")
                            while queue.qsize() > 0:
                                queue.get()
                                queue.task_done()
                            Logger.log(f"Queue cleared (modified by calm, discord @m8ov)")
                            sleep(self.timeout+1)
                            print(f"\n{Colors.RED}No proxies left{Colors.ENDC}"*3)
                            
                            
                        while proxy in self.proxies_not_working:
                            proxy = next(proxy_cycle)
                        
                if proxy is not None:
                    proxy = f"http://{str(proxy).strip()}"

                
                r = self.session.post(
                    url=self.endpoint + "/unique-username/username-attempt-unauthed",
                    headers = self.headers_post,
                    json={"username": name},
                    proxies={"http": proxy, "https": proxy},
                    timeout=self.timeout
                ) 
                REQUESTS += 1

                if r.status_code in [200, 201, 204]:
                    if str(r.json()) in ["", None, "{}"]:
                        Logger.log(f"Unexpected response resp = {r.text} (modified by calm, discord @m8ov)")
                        return self.check(name)
                    

                    elif r.json()["taken"]:
                        TAKEN += 1
                        return [False, r.json(), r.status_code]

                    elif not r.json()["taken"]:
                        WORKS += 1
                        return [True, r.json(), r.status_code]

                #rate limited
                elif r.status_code == 429:
                    if proxy is None or proxy == "None" or proxy == "":

                        print("PROXYLESS RATELIMITED SLEEPING")
                        sleep(r.json()["retry_after"])
                        name = [name, next(proxy_cycle)]
                        return self.check(name)
                else:
                    Logger.log(f"Unknown error with request {r.status_code}    |   {r.json()} (modified by calm, discord @m8ov)")

            except requests.exceptions.ProxyError:
                self.proxy_err(name, proxy, proxy_cycle)
                return self.check(name)

            except requests.exceptions.ConnectionError:
                self.proxy_err(name, proxy, proxy_cycle)
                return self.check(name)
            
            except requests.exceptions.ReadTimeout:
                self.proxy_err(name, proxy, proxy_cycle)
                return self.check(name)
            
            except MaxRetryError:
                self.proxy_err(name, proxy, proxy_cycle)
                return self.check(name)

            except:
                with lock:
                    try:
                        exception = traceback.format_exc()
                        Logger.log(f"Unknown error with proxy {proxy} (modified by calm, discord @m8ov)")
                        with open("logs/error.txt", "w") as f:
                            f.write(f"{exception}\n")
                            f.close()
                        sleep(0.3)
                    except:
                        pass
                return self.check(name)

g = Colors.GREY
r = Colors.RED
x = Colors.ENDC
ASCII = f"""
{g}                      :::!~!!!!!:.
                .xUHWH!! !!?M88WHX:.
                .X*#M@$!!  !X!M$$$$$$WWx:.
            :!!!!!!?H! :!$!$$$$$$$$$$8X:
            !!~  ~:~!! :~!$!#$$$$$$$$$$8X:
            :!~::!H!<   ~.U$X!?R$$$$$$$$MM!
            ~!~!!!!~~ .:XW$$$U!!?$$$$$$RMM!
            !:~~~ .:!M"T#$$$$WX??#MRRMMM!
            ~?WuxiW*`   `"#$$$$8!!!!??!!!
            :X- M$$$$       `"T#$T~!8$WUXU~
            :%`  ~#$$$m:        ~!~ ?$$$$$$
        :!`.-   ~T$$$$8xx.  .xWW- ~""##*"
.....   -~~:<` !    ~?T#$$@@W@*?$$      /`
W$@@M!!! .!~~ !!     .:XUW$W!~ `"~:    :
#"~~`.:x%`!!  !H:   !WM$$$$Ti.: .!WUn+!`
:::~:!!`:X~ .: ?H.!u "$$$B$$$!W:U!T$$M~
.~~   :X@!.-~   ?@WTWo("*$$$W$TH$! `
Wi.~!X$?!-~    : ?$$$B$Wu("**$RM!
$R@i.~~ !     :   ~$$$$$B$$en:`
?MXT@Wx.~    :     ~"##*$$$$M~

                    {r}@{x}  SENDR 2025 (modified by calm, credits to Cloudzik133)           {r}@{x}
                    {r}@{x}  github.com/Calmspec/sendr/                        {r}@{x}
                    {r}@{x}  @m8ov                                  {r}@{x}
                    {r}@{x}  Version: {VERSION}                                   {r}@{x}
        """
clear()
print(ASCII)


# username can contain letters, numbers, underscores, and dots
CHARS = string.ascii_lowercase + string.digits + "_" + '.'


with open("data/names_to_check.txt", "r", encoding='utf-8') as f:
    combos = f.read().splitlines()
    f.close()

with open("data/config.json", "r") as f:
    config_str = f.read()
    f.close()

if len(config_str) == 2 or os.path.getsize("data/config.json") == 0 or config.get("remove_proxies") is None:
    if config.get("webhook") is None:
        ask_webhook = input(f"Send hits to webhook [y/n] {Colors.YELLOW}>>>{Colors.ENDC} ")
        if ask_webhook.lower() in confirmators:
            webhook = input(f"Webhook url {Colors.YELLOW}>>>{Colors.ENDC} ")
            config.set("webhook", webhook)
            print(f"{Colors.MAGENTA}Use <name> to send the name of the hit \nuse <@userid> to mention the user (replace user id with actuall id)\n<time> to send timestamp of the hit\nUse <RPS> to send requests per second\nUse <elapsed> to send elapsed time{Colors.ENDC}")
            message = input(f"Message to send {Colors.YELLOW}>>>{Colors.ENDC} ")
            config.set("message", message)
        else:
            config.set("webhook", None)
    if config.get("remove_proxies") is None:
        ask_proxy = input(f"Use proxies [y/n] {Colors.YELLOW}>>>{Colors.ENDC} ")
        ask_timeout = input(f"Timeout in seconds (Default: 30) {Colors.YELLOW}>>>{Colors.ENDC} ")
        config.set("timeout", int(ask_timeout))
        if ask_proxy.lower() in confirmators:
            ask_proxy = input(f"Rotating proxies ? (login:pass@host:port) [y/n] {Colors.YELLOW}>>>{Colors.ENDC} ")
            if ask_proxy.lower() in confirmators:
                proxy = input(f"Proxy {Colors.YELLOW}>>>{Colors.ENDC} ")
                with open(proxy, "r", encoding='utf-8') as f:
                    proxies = f.read().splitlines()
                    f.close()
                config.set("remove_proxies", False)

            elif ask_proxy.lower() in negators:
                print(f"Please input proxies to data/proxies.txt")
                input("Press enter to continue")
                with open("data/proxies.txt", "r", encoding='utf-8') as proxies:proxies= proxies.read().splitlines()             
                if len(proxies) == 0:
                    proxies = [None]
                    print(f"{Colors.RED}No proxies loaded switching to proxyless{Colors.ENDC}")
                else:
                    print(f"{Colors.MAGENTA}Loaded {len(proxies)} proxies{Colors.ENDC}")
                proxy_cycle = itertools.cycle(proxies)
                ask_remove_bad_proxies = input(f"Remove bad proxies [y/n] {Colors.YELLOW}>>>{Colors.ENDC} ")
                if ask_remove_bad_proxies.lower() in confirmators:
                    config.set("remove_proxies", False)
        elif ask_proxy.lower() in negators:
"""Sendr (modified by calm, discord @m8ov original by Cloudzik133)"""

import itertools
import string
import queue
import threading
from time import sleep, time
import traceback
import random
import os
from signal import signal, SIGINT
import requests
import json
from pathlib import Path
from urllib3.exceptions import MaxRetryError
import sys

VERSION = "1.0.5"

class Config:
    """Config class (modified by calm, discord @m8ov)"""
    def __init__(self):
        self.config = None
        self.load_config()

    def load_config(self):
        with open('data/config.json', 'a') as f:
            if os.path.getsize("data/config.json") == 0:
                f.write("{}")
                f.close()
        

    def get(self, key):
        with open('data/config.json', 'r') as f:
            self.config = json.load(f)
        try:
            return self.config[key]
        except KeyError:
            return None
    
    def set(self, key, value):
        with open('data/config.json', 'r') as f:
            self.config = json.load(f)
        self.config[key] = value
        with open('data/config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
        
    def get_all(self):
        with open('data/config.json', 'r') as f:
            self.config = json.load(f)
        return self.config


###############################################################
#                      Close on ctrl+c                        #
###############################################################
@staticmethod
def handler(signal_received, frame):
    # Handle any cleanup here
    print('\nSIGINT or CTRL-C detected. Exiting gracefully')
    exit(0)

signal(SIGINT, handler)





confirmators =  ["y", "yes", "1", "true", "t"]
negators =      ["n", "no", "0", "false", "f"]

os.makedirs("logs", exist_ok=True)
os.makedirs("results", exist_ok=True)  
os.makedirs("data", exist_ok=True)


def create_empty_file(file_path):
    file_path = Path(file_path)
    
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding='utf-8'):
            pass

def clear_file(file_path):
    file_path = Path(file_path)
    
    if file_path.exists():
        with file_path.open("w", encoding='utf-8'):
            pass


create_empty_file("logs/log.txt")
clear_file("logs/log.txt")


create_empty_file("results/hits.txt")

create_empty_file("data/names_to_check.txt")

create_empty_file("logs/error.txt")
clear_file("logs/error.txt")

create_empty_file("data/proxies.txt")

with Path("data/proxies.txt").open("r", encoding='utf-8') as proxies_file:
    proxies = proxies_file.read().splitlines()


config = Config()
lock = threading.Lock()


if len(proxies) == 0:
    proxies = [None]
proxy_cycle = itertools.cycle(proxies)


#Globals
RPS =       0
REQUESTS =  0
WORKS =     0
TAKEN =     0
DEACTIVATE = False


class Logger:
    """Logger class (modified by calm, discord @m8ov)"""
    def __init__(self, file_name: str):
        """Initiate the class"""
        self.file_name = file_name
        self.file = open(self.file_name, "a")

    def log(self, message: str):
        """Log a message to the file"""
        self.file.write(f"{message}\n")
        self.file.flush()

    def close(self):
        """Close the file"""
        self.file.close()


class _Colors:
    """Menu colors"""
    @staticmethod
    def _color_code(code):
        """Static method to format color codes"""
        return f'\033[{code}m'


    ENDC: str =         _color_code(0)
    BOLD: str =         _color_code(1)
    UNDERLINE: str =    _color_code(4)
    BLACK: str =        _color_code(30)
    RED: str =          _color_code(31)
    GREEN: str =        _color_code(32)
    YELLOW: str =       _color_code(33)
    BLUE: str =         _color_code(34)
    MAGENTA: str =      _color_code(35)
    CYAN: str =         _color_code(36)
    WHITE: str =        _color_code(37)
    REDBG: str =        _color_code(41)
    GREENBG: str =      _color_code(42)
    YELLOWBG: str =     _color_code(43)
    BLUEBG: str =       _color_code(44)
    MAGENTABG: str =    _color_code(45)
    CYANBG: str =       _color_code(46)
    WHITEBG: str =      _color_code(47)
    GREY: str =         _color_code(90)


Colors = _Colors()

Logger = Logger("logs/log.txt")


Logger.log(f"sendrChecker started at {time()} (modified by calm, discord @m8ov)")


def clear():
    """Clear the screen"""
    os.system('cls' if os.name=='nt' else 'clear')

clear()

class Pomelo:
    """sendr Checker"""
    def __init__(self):
        """Initiate the class"""
        self.endpoint = "https://discord.com/api/v9"
        self.headers_post = {"Content-Type": "application/json"}
        self.session = requests.Session()
        self.proxies_not_working = []
        self.remove_proxies = config.get("remove_proxies")
        self.timeout = config.get("timeout")
        if self.timeout is None:
            self.timeout = 30

        Logger.log(f"Timeout set to {self.timeout} (modified by calm, discord @m8ov)")
        Logger.log(f"Remove proxies set to {self.remove_proxies} (modified by calm, discord @m8ov)")
        Logger.log(f"Headers set to {self.headers_post} (modified by calm, discord @m8ov)")

    def proxy_err(self, name, proxy, proxy_cycle):
        name = [name, next(proxy_cycle)]
        Logger.log(f"ReadTimeout with proxy {proxy} (modified by calm, discord @m8ov)")
        if self.remove_proxies and proxy != None:
            Logger.log(f"Removing proxy {proxy} (modified by calm, discord @m8ov)")
            self.proxies_not_working.append(proxy)
        
        
    def  check(self, name: list):
        """Check if the name is available"""

        global RPS, REQUESTS, WORKS, TAKEN, DEACTIVATE
        while not DEACTIVATE:
            try:
                try:
                    name, proxy = name
                # only name is passed
                except ValueError:
                    if proxy_cycle is None:
                        proxy = None
                    else:
                        proxy = next(proxy_cycle)
                        if len(self.proxies_not_working) >= len(proxies):
                            Logger.log(f"Exiting because all proxies are not working (modified by calm, discord @m8ov)")
                            
                            DEACTIVATE = True
                            # clear queue
                            Logger.log(f"Clearing queue (modified by calm, discord @m8ov)")
                            while queue.qsize() > 0:
                                queue.get()
                                queue.task_done()
                            Logger.log(f"Queue cleared (modified by calm, discord @m8ov)")
                            sleep(self.timeout+1)
                            print(f"\n{Colors.RED}No proxies left{Colors.ENDC}"*3)
                            
                            
                        while proxy in self.proxies_not_working:
                            proxy = next(proxy_cycle)
                        
                if proxy is not None:
                    proxy = f"http://{str(proxy).strip()}"

                
                r = self.session.post(
                    url=self.endpoint + "/unique-username/username-attempt-unauthed",
                    headers = self.headers_post,
                    json={"username": name},
                    proxies={"http": proxy, "https": proxy},
                    timeout=self.timeout
                ) 
                REQUESTS += 1

                if r.status_code in [200, 201, 204]:
                    if str(r.json()) in ["", None, "{}"]:
                        Logger.log(f"Unexpected response resp = {r.text} (modified by calm, discord @m8ov)")
                        return self.check(name)
                    

                    elif r.json()["taken"]:
                        TAKEN += 1
                        return [False, r.json(), r.status_code]

                    elif not r.json()["taken"]:
                        WORKS += 1
                        return [True, r.json(), r.status_code]

                #rate limited
                elif r.status_code == 429:
                    if proxy is None or proxy == "None" or proxy == "":

                        print("PROXYLESS RATELIMITED SLEEPING")
                        sleep(r.json()["retry_after"])
                        name = [name, next(proxy_cycle)]
                        return self.check(name)
                else:
                    Logger.log(f"Unknown error with request {r.status_code}    |   {r.json()} (modified by calm, discord @m8ov)")

            except requests.exceptions.ProxyError:
                self.proxy_err(name, proxy, proxy_cycle)
                return self.check(name)

            except requests.exceptions.ConnectionError:
                self.proxy_err(name, proxy, proxy_cycle)
                return self.check(name)
            
            except requests.exceptions.ReadTimeout:
                self.proxy_err(name, proxy, proxy_cycle)
                return self.check(name)
            
            except MaxRetryError:
                self.proxy_err(name, proxy, proxy_cycle)
                return self.check(name)

            except:
                with lock:
                    try:
                        exception = traceback.format_exc()
                        Logger.log(f"Unknown error with proxy {proxy} (modified by calm, discord @m8ov)")
                        with open("logs/error.txt", "w") as f:
                            f.write(f"{exception}\n")
                            f.close()
                        sleep(0.3)
                    except:
                        pass
                return self.check(name)

g = Colors.GREY
r = Colors.RED
x = Colors.ENDC
ASCII = f"""
{g}                      :::!~!!!!!:.
                .xUHWH!! !!?M88WHX:.
                .X*#M@$!!  !X!M$$$$$$WWx:.
            :!!!!!!?H! :!$!$$$$$$$$$$8X:
            !!~  ~:~!! :~!$!#$$$$$$$$$$8X:
            :!~::!H!<   ~.U$X!?R$$$$$$$$MM!
            ~!~!!!!~~ .:XW$$$U!!?$$$$$$RMM!
            !:~~~ .:!M"T#$$$$WX??#MRRMMM!
            ~?WuxiW*`   `"#$$$$8!!!!??!!!
            :X- M$$$$       `"T#$T~!8$WUXU~
            :%`  ~#$$$m:        ~!~ ?$$$$$$
        :!`.-   ~T$$$$8xx.  .xWW- ~""##*"
.....   -~~:<` !    ~?T#$$@@W@*?$$      /`
W$@@M!!! .!~~ !!     .:XUW$W!~ `"~:    :
#"~~`.:x%`!!  !H:   !WM$$$$Ti.: .!WUn+!`
:::~:!!`:X~ .: ?H.!u "$$$B$$$!W:U!T$$M~
.~~   :X@!.-~   ?@WTWo("*$$$W$TH$! `
Wi.~!X$?!-~    : ?$$$B$Wu("**$RM!
$R@i.~~ !     :   ~$$$$$B$$en:`
?MXT@Wx.~    :     ~"##*$$$$M~

                    {r}@{x}  SENDR 2025 (modified by calm, credits to Cloudzik133)           {r}@{x}
                    {r}@{x}  github.com/Calmspec/sendr/                        {r}@{x}
                    {r}@{x}  @m8ov                                  {r}@{x}
                    {r}@{x}  Version: {VERSION}                                   {r}@{x}
        """
clear()
print(ASCII)


# username can contain letters, numbers, underscores, and dots
CHARS = string.ascii_lowercase + string.digits + "_" + '.'


with open("data/names_to_check.txt", "r", encoding='utf-8') as f:
    combos = f.read().splitlines()
    f.close()

with open("data/config.json", "r") as f:
    config_str = f.read()
    f.close()

if len(config_str) == 2 or os.path.getsize("data/config.json") == 0 or config.get("remove_proxies") is None:
    if config.get("webhook") is None:
        ask_webhook = input(f"Send hits to webhook [y/n] {Colors.YELLOW}>>>{Colors.ENDC} ")
        if ask_webhook.lower() in confirmators:
            webhook = input(f"Webhook url {Colors.YELLOW}>>>{Colors.ENDC} ")
            config.set("webhook", webhook)
            print(f"{Colors.MAGENTA}Use <name> to send the name of the hit \nuse <@userid> to mention the user (replace user id with actuall id)\n<time> to send timestamp of the hit\nUse <RPS> to send requests per second\nUse <elapsed> to send elapsed time{Colors.ENDC}")
            message = input(f"Message to send {Colors.YELLOW}>>>{Colors.ENDC} ")
            config.set("message", message)
        else:
            config.set("webhook", None)
    if config.get("remove_proxies") is None:
        ask_proxy = input(f"Use proxies [y/n] {Colors.YELLOW}>>>{Colors.ENDC} ")
        ask_timeout = input(f"Timeout in seconds (Default: 30) {Colors.YELLOW}>>>{Colors.ENDC} ")
        config.set("timeout", int(ask_timeout))
        if ask_proxy.lower() in confirmators:
            ask_proxy = input(f"Rotating proxies ? (login:pass@host:port) [y/n] {Colors.YELLOW}>>>{Colors.ENDC} ")
            if ask_proxy.lower() in confirmators:
                proxy = input(f"Proxy {Colors.YELLOW}>>>{Colors.ENDC} ")
                with open(proxy, "r", encoding='utf-8') as f:
                    proxies = f.read().splitlines()
                    f.close()
                config.set("remove_proxies", False)

            elif ask_proxy.lower() in negators:
                print(f"Please input proxies to data/proxies.txt")
                input("Press enter to continue")
                with open("data/proxies.txt", "r", encoding='utf-8') as proxies:proxies= proxies.read().splitlines()             
                if len(proxies) == 0:
                    proxies = [None]
                    print(f"{Colors.RED}No proxies loaded switching to proxyless{Colors.ENDC}")
                else:
                    print(f"{Colors.MAGENTA}Loaded {len(proxies)} proxies{Colors.ENDC}")
                proxy_cycle = itertools.cycle(proxies)
                ask_remove_bad_proxies = input(f"Remove bad proxies [y/n] {Colors.YELLOW}>>>{Colors.ENDC} ")
                if ask_remove_bad_proxies.lower() in confirmators:
                    config.set("remove_proxies", False)
        elif ask_proxy.lower() in negators:
print(f"{Colors.YELLOW} It is working!{Colors.END}")

