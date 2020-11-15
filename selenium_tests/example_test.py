# encoding: utf-8

import unittest
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .ZMSTestCase import ZMSTestCase

# python -m unittest selenium_tests.example_test.EditPageExample
class EditPageExample(ZMSTestCase):
    
    def test_edit(self):
        print("<EditPageExample.test_edit>")
        self._set_up()
        
        # get id
        zmi_item = self._find_element(By.CSS_SELECTOR, '.zmi-item:last-of-type')
        id = zmi_item.get_attribute("id")
        
        # open actions-dropdown-menu and click create document
        el = self._show_zmi_action(id)
        item = el.find_element_by_link_text('Textabschnitt')
        self._wait_for_click(item, By.CSS_SELECTOR, '#zmiIframeAddDialog')
        self._hide_zmi_actions()
        
        # insert frame
        MARKER = "%s-%s" % (self.id(), random.randint(0, 100000))
        iframe = self._find_element(By.CSS_SELECTOR, 'iframe.cke_wysiwyg_frame')
        self.driver.switch_to.frame(iframe)
        self._find_element(By.CSS_SELECTOR, 'body').send_keys(MARKER)
        self.driver.switch_to.default_content()
        with self._wait_for_page_load():
            self._find_element(By.XPATH, '//button[text()="Einfügen"]').click()
        
        # wait until saved
        self._find_element(By.CSS_SELECTOR, '.alert-success')
        
        # open preview
        with self._wait_for_page_load(roottag='frameset'):
            self._wait_for_click(self._find_element(By.LINK_TEXT, "Vorschau"),By.CSS_SELECTOR,'frameset')
        
        frame = self._find_element(By.NAME, "partner")
        self.driver.switch_to.frame(frame)
        
        # ensure text is there
        self._find_element(By.XPATH, '//p[text()="%s"]' % MARKER)
        
        self._tear_down()
        print("<EditPageExample.test_edit>")

if __name__ == "__main__":
    unittest.main()
