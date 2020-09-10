#!/usr/bin/python3
import argparse
import base64
import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options, DesiredCapabilities

config_file = 'torbridge.conf'

# Making the browser run headless.
options = Options()
options.add_argument("--headless")
capabilities = DesiredCapabilities.CHROME.copy()
capabilities['acceptSslCerts'] = True
capabilities['acceptWebsiteCerts'] = True

# Parsing the CLI arguments.
parser = argparse.ArgumentParser()
parser.add_argument('-a', '--add', action='store_true', help='appends bridges to torrcfile')
parser.add_argument('-c', '--clear', action='store_true', help='clears config file')
args = parser.parse_args()


# Setting config file and getting bridges and appending them to torrc file.
def add_bridges():
    if os.path.isfile(config_file):
        with open(config_file, 'r') as in_file:
            for line in in_file:
                if line.startswith('http'):
                    base_url = line
                elif line.startswith('/'):
                    torrc_path = line
    else:
        torrc_path = input("Enter your torrcfile path (Default: /etc/tor/torrc) ") or '/etc/tor/torrc'
        proxy_type = input("Enter your desired proxy type (obfs4proxy[default] or obfsproxy) ") or 'obfs4proxy'
        ip_type = input("Do you want to use ipv6? (yes(y) or no(n)[default: no]) ") or ''

        if proxy_type != 'obfs4proxy':
            proxy_type = '0'
        positive = ['Yes', 'yes', 'Y', 'y']
        negative = ['No', 'no', 'N', 'n']
        for answer in positive:
            if ip_type == answer:
                ip_type = '&ipv6=yes'
        for answer in negative:
            if ip_type == answer:
                ip_type = ''

        with open(config_file, 'w') as out_file:
            base_url = "https://bridges.torproject.org/bridges?transport=" + proxy_type + ip_type
            print(base_url, file=out_file)
            print(torrc_path, file=out_file)

    try:
        with webdriver.Chrome(options=options, desired_capabilities=capabilities) as driver:
            driver.get(base_url)
    except WebDriverException:
        print("No chrome driver found, please refer to "
              "https://sites.google.com/a/chromium.org/chromedriver/downloads and download it.")

    image = driver.find_element_by_tag_name('img').get_attribute('src')
    stripped_string = image.lstrip('data:image/jpeg;base64')
    photo = base64.b64decode(stripped_string)
    with open("photo.jpg", "wb") as fh:
        fh.write(photo)

    os.system("feh photo.jpg &")

    captcha = input("Enter the captcha: ")

    input_field = driver.find_element_by_id('captcha_response_field')
    input_field.send_keys(captcha)
    driver.find_element_by_class_name('btn-primary').click()

    try:
        bridges = driver.find_element_by_class_name('bridge-lines').text
        with open(torrc_path, 'a') as torrc_file:
            for bridge in bridges.split('\n'):
                print('Bridge ' + bridge)
                print('Bridge ' + bridge, file=torrc_file)
    except NoSuchElementException:
        error = driver.find_element_by_css_selector('.alert p:nth-child(2)').text
        print(error)
    except PermissionError:
        print("You don't have sufficient permissions to open " + torrc_path + " file.")


# Clearing the config file.

def clear_config_file():
    if os.path.exists(config_file):
        os.remove(config_file)
        print(config_file + " has been deleted.")
    else:
        print(config_file + " doesn't exist.")


if __name__ == '__main__':
    # Calling functions according to the provided arguments.
    if args.add:
        add_bridges()
    elif args.clear:
        clear_config_file()
    else:  # Prompt to use help if no arguments are provided.
        print("No arguments provided.")
        print("Use -h or --help for help.")
