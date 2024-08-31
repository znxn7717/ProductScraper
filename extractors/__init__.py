# __init__.py
import json
import logging
from dotenv import load_dotenv
from selenium import webdriver
from models.Product import Database
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service

class ProductExtractor:
    def __init__(self,
                 firefox_driver_path='/geckodriver.exe',
                 chrome_driver_path='/chromedriver.exe',
                 firefox_binary_path='C:\\Program Files\\Mozilla Firefox\\firefox.exe',
                 chrome_binary_path='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                 window_size='--window-size=1920,1080',
                 incognito_mode=True,
                 headless_mode=True):
        self.firefox_driver_path = firefox_driver_path
        self.chrome_driver_path = chrome_driver_path
        self.firefox_binary_path = firefox_binary_path
        self.chrome_binary_path = chrome_binary_path
        self.window_size = window_size
        self.incognito_mode = incognito_mode
        self.headless_mode = headless_mode
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.db = Database()
        self.db.connect_to_database()
        self.db.setup_product_table()

    def init_firefox_driver(self):
        service = Service(self.firefox_driver_path)
        options = FirefoxOptions()
        options.binary_location = self.firefox_binary_path
        options.add_argument(self.window_size)
        if self.incognito_mode:
            options.add_argument("--private")
        if self.headless_mode:
            options.add_argument("--headless")
        return webdriver.Firefox(service=service, options=options)

    def init_chrome_driver(self):
        options = ChromeOptions()
        options.binary_location = self.chrome_binary_path
        options.add_argument(self.window_size)
        if self.incognito_mode:
            options.add_argument("--incognito")
        if self.headless_mode:
            options.add_argument("--headless")
        return webdriver.Chrome(options=options)

    def reset_driver(self, driver):
        self.logger.info("Resetting driver...")
        driver.quit()
        if self.firefox_driver_path:
            return self.init_firefox_driver()
        elif self.chrome_driver_path:
            return self.init_chrome_driver()
        else:
            raise ValueError("No driver path specified.")

    def write_json(self, prefix, type, data):
        with open(f'data/{prefix}_{type}.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def read_json(self, prefix, type):
        with open(f'data/{prefix}_{type}.json', 'r', encoding='utf-8') as file:
            return json.load(file)

    def find_key_by_value(self, path, value):
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        for key, values in data.items():
            if value in values:
                return key
        return "سایر"