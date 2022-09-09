import time, re
import pandas as pd
from lxml import html

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.proxy import Proxy, ProxyType

from webdriver_manager.chrome import ChromeDriverManager

from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

software_names = [SoftwareName.CHROME.value]
operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
user_agent_rotator = UserAgent(
    software_names=software_names, operating_systems=operating_systems, limit=100
)


def readyDriver():
    chrome_options = Options()
    chrome_options.add_argument("log-level=3")
    chrome_options.add_experimental_option(
        "prefs", {"profile.managed_default_content_settings.images": 2}
    )
    chrome_options.add_experimental_option(
        "excludeSwitches",
        [
            "disable-background-networking",
            "disable-default-apps",
            "disable-hang-monitor",
            "disable-popup-blocking",
            "disable-prompt-on-repost",
            "disable-sync",
            "enable-automation",
            "enable-blink-features",
            "log-level",
            "no-first-run",
            "no-service-autorun",
            "password-store",
            "test-type",
            "use-mock-keychain",
        ],
    )
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option(
        "mobileEmulation", {"deviceName": "iPhone X"}
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )
    driver.implicitly_wait(180)
    driver.set_page_load_timeout(180)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    driver.execute_cdp_cmd(
        "Network.setBlockedURLs",
        {
            "urls": [
                "cloudflare.hcaptcha.com",
                "cf-assets.hcaptcha.com",
                "cloudflare.com",
                "m.add-this.com" "",
            ]
        },
    )
    time.sleep(1)
    return driver


def bkup(out):
    pd.DataFrame(out).to_csv("export(backup).csv", index=False)


out = []

driver = readyDriver()

urls = pd.read_csv("storeboard_profile_urls.csv").links.tolist()


for i, url in enumerate(urls):
    try:
        driver.get(url)
        print("\npage load complete")
        time.sleep(1)
        if driver.title == "Just a moment...":
            wait_time = 2
            while True:
                driver.delete_all_cookies()
                time.sleep(wait_time)
                driver.execute_cdp_cmd(
                    "Network.setUserAgentOverride",
                    {"userAgent": user_agent_rotator.get_random_user_agent()},
                )
                driver.refresh()
                time.sleep(2)
                if driver.title != "Just a moment...":
                    break
                wait_time += 2
                print(f"stuck at robot test\nwait time increased to {wait_time}")
        print("waiting for data")
        if "Page Not Found" in driver.page_source:
            pass
        else:
            WebDriverWait(driver, 200).until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//td[text()="Directory Category"]')
                )
            )
        print("wait complete")
        doc = html.fromstring(driver.page_source)
    except Exception as e:
        print(e)
    try:
        name = re.sub(":$", "", doc.xpath('//b[@class="XSmallBlueTitle"]//text()')[0])
    except:
        name = None
    try:
        website = (
            doc.xpath('//a[@title="Visit Our Website"]/@href')[0]
            .replace("http://https//", "https://")
            .replace("http://https://", "https://")
        )
    except:
        website = None
    try:
        directory_category = doc.xpath(
            '//*[text()="Directory Category"]/following-sibling::td//text()'
        )[0]
    except:
        directory_category = None
    try:
        business_category = doc.xpath(
            '//td[text()="Business" and text()="Categories"]/following-sibling::td//text()'
        )[0]
    except:
        business_category = None
    try:
        location = doc.xpath(
            '//td[text()="Address " or text()="Location "]/following-sibling::td//td[@valign="top"]/text()'
        )[0]
    except:
        location = None
    try:
        phone = doc.xpath('//td[text()="Phone "]/following-sibling::td//text()')[0]
    except:
        phone = None
    try:
        business_description = doc.xpath(
            '//td[text()="Business Description "]/following-sibling::td//td[@class="mainlink-u"]/text()'
        )[0]
    except:
        business_description = None
    try:
        email = doc.xpath('//td[text()="E-mail "]/following-sibling::td//text()')[0]
    except:
        email = None
    print("value collected")
    info = {
        "url": url,
        "name": name,
        "website": website,
        "directory_category": directory_category,
        "business_category": business_category,
        "business_description": business_description,
        "phone": phone,
        "location": location,
        "email": email,
    }
    out.append(info)
    bkup(out)
    print("backup done")
    print(i, " -- ", out[-1], "\n")
    driver.delete_all_cookies()
    driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {"userAgent": user_agent_rotator.get_random_user_agent()},
    )
    time.sleep(1)

driver.quit()

pd.DataFrame(out).to_csv("export.csv", index=False)
