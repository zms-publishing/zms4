# encoding: utf-8

import unittest
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .ZMSTestCase import ZMSTestCase

# python -m unittest selenium_tests.metacmd_manager_test.MetacmdManagerTest
class MetacmdManagerTest(ZMSTestCase):
   
      def test_conf(self):
        print('<MetacmdManagerTest.test_conf>')
        self._set_up()
        
        # open config
        navbar = self._find_element(By.CSS_SELECTOR, '.navbar-main')
        navbar.find_element_by_css_selector('.dropdown-toggle').click()
        navitem = navbar.find_element_by_link_text('Aktionen')
        self._wait(lambda driver: navitem.is_displayed())
        with self._wait_for_page_load():
            navitem.click()
        
        # wait until opened
        self._find_element(By.CSS_SELECTOR, 'body.metas.config')
        
        # open insert dialog
        self._find_element(By.CSS_SELECTOR, '.btn.btn-primary[title="Einfügen..."]').click()
        
        dialog = self._find_element(By.CSS_SELECTOR, '#zmiModalinsertObj')
        self._wait(lambda driver: dialog.is_displayed())
        dialog.find_element(By.CSS_SELECTOR, 'input[name="_id"]').send_keys('manage_LgTest')
        dialog.find_element(By.CSS_SELECTOR, 'input[name="_name"]').send_keys('Test')
        dialog.find_element(By.CSS_SELECTOR, 'input[name="_title"]').send_keys('Test')
        with self._wait_for_page_load():
            dialog.find_element(By.CSS_SELECTOR, '.btn.btn-primary[value="Einfügen"]').click()
        
        # wait until saved
        self._find_element(By.CSS_SELECTOR, '.alert-success')
        
        # close dialog
        dialog = self._find_element(By.CSS_SELECTOR, '#zmiModaleditObj')
        self._wait(lambda driver: dialog.is_displayed())
        dialog.find_element(By.CSS_SELECTOR, '.btn[value="Schließen"]').click()
        self._wait(lambda driver: not dialog.is_displayed())
        
        # reload page (also removes .alert-success)
        with self._wait_for_page_load():
            self._find_element(By.CSS_SELECTOR, '.nav.nav-tabs .active').click()
        
        # open delete dialog
        self._find_element(By.CSS_SELECTOR, 'input[name="ids:list"][value="manage_LgTest"]').click()
        self._find_element(By.CSS_SELECTOR, '.btn.btn-default[title="Löschen..."]').click()
        self._wait(EC.alert_is_present())
        with self._wait_for_page_load():
            self.driver.switch_to.alert.accept()
        
        # wait until saved
        self._find_element(By.CSS_SELECTOR, '.alert-success')
        
        self._tear_down()
        print('</MetacmdManagerTest.test_conf>')


if __name__ == "__main__":
    unittest.main()
