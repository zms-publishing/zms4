# encoding: utf-8

import unittest
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .ZMSTestCase import ZMSTestCase

# python -m unittest selenium_tests.multilang_manager_test.MultilangManagerTest
class MultilangManagerTest(ZMSTestCase):
   
      def test_conf(self):
        print('<MultilangManagerTest.test_conf>')
        self._set_up()
        
        # open config
        navbar = self._find_element(By.CSS_SELECTOR, '.navbar-main')
        navbar.find_element_by_css_selector('.dropdown-toggle').click()
        navitem = navbar.find_element_by_link_text('Sprachen')
        self._wait(lambda driver: navitem.is_displayed())
        with self._wait_for_page_load():
            navitem.click()
        
        # wait until opened
        self._find_element(By.CSS_SELECTOR, 'body.languages.config')
        
        # open insert dialog
        self._find_element(By.CSS_SELECTOR, '#changeLanguagesForm input[name="language_id"]').send_keys('eng')
        self._find_element(By.CSS_SELECTOR, '#changeLanguagesForm input[name="language_label"]').send_keys('English')
        with self._wait_for_page_load():
            self._find_element(By.CSS_SELECTOR, '#changeLanguagesForm .btn[value="Speichern"]').click()
        
        # wait until saved
        self._find_element(By.CSS_SELECTOR, '.alert-success')
        
        # reload page
        with self._wait_for_page_load():
            self._find_element(By.CSS_SELECTOR, '.nav.nav-tabs .active').click()
        
        # add key to lang-dict
        self._find_element(By.CSS_SELECTOR, '#changeLangDictForm input[name="_key"]').send_keys('HELLO_WORLD')
        self._find_element(By.CSS_SELECTOR, '#changeLangDictForm textarea[name="_value_ger"]').send_keys('Hallo Welt')
        self._find_element(By.CSS_SELECTOR, '#changeLangDictForm textarea[name="_value_eng"]').send_keys('Hello World')
        with self._wait_for_page_load():
            self._find_element(By.CSS_SELECTOR, '#changeLangDictForm .btn[value="Speichern"]').click()
        
        # wait until saved
        self._find_element(By.CSS_SELECTOR, '.alert-success')
        
        # reload page
        with self._wait_for_page_load():
            self._find_element(By.CSS_SELECTOR, '.nav.nav-tabs .active').click()
        
        # delete key from lang-dict
        self._find_element(By.CSS_SELECTOR, '#changeLangDictForm input[name="ids:list"][value="HELLO_WORLD"]').click()
        with self._wait_for_page_load():
            self._find_element(By.CSS_SELECTOR, '#changeLangDictForm .btn[value="Löschen"]').click()
        
        # wait until saved
        self._find_element(By.CSS_SELECTOR, '.alert-success')
        
        # reload page
        with self._wait_for_page_load():
            self._find_element(By.CSS_SELECTOR, '.nav.nav-tabs .active').click()
        
        # delete language
        self._find_element(By.CSS_SELECTOR, '#changeLanguagesForm input[name="ids:list"][value="eng"]').click()
        with self._wait_for_page_load():
            self._find_element(By.CSS_SELECTOR, '#changeLanguagesForm .btn[value="Löschen"]').click()
        
        # wait until saved
        self._find_element(By.CSS_SELECTOR, '.alert-success')
        
        self._tear_down()
        print('</MultilangManagerTest.test_conf>')


if __name__ == "__main__":
    unittest.main()
