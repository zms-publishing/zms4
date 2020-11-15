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

# python -m unittest selenium_tests.workflow_manager_test.WorkflowManagerTest
class WorkflowManagerTest(ZMSTestCase):
    
    def test_conf(self):
        print('<WorkflowManagerTest.test_conf>')
        self._set_up()
        
        # open config
        navbar = self._find_element(By.CSS_SELECTOR, '.navbar-main')
        navbar.find_element_by_css_selector('.dropdown-toggle').click()
        navitem = navbar.find_element_by_link_text('System')
        self._wait(lambda driver: navitem.is_displayed())
        with self._wait_for_page_load():
            navitem.click()
        
        # wait until opened
        self._find_element(By.CSS_SELECTOR, 'body.customize.config')
        
        # insert workflow-manager
        select = Select(self._find_element(By.CSS_SELECTOR, '#Manager select#meta_type'))
        select.select_by_visible_text('ZMSWorkflowProvider')
        with self._wait_for_page_load():
            self._find_element(By.CSS_SELECTOR, '#Manager .btn[value="Add"]').click()
        
        # wait until saved
        self._find_element(By.CSS_SELECTOR, '.alert-success')
        
        # open workflow tab
        with self._wait_for_page_load():
            self._find_element(By.XPATH, '//ul/li/a[text()="Workflow"]').click()
        
        # wait until opened
        self._find_element(By.CSS_SELECTOR, 'body.workflow_manager_main.config')
        
        # open workflow tab
        with self._wait_for_page_load():
            self._find_element(By.XPATH, '//ul/li/a[text()="System"]').click()
        
        # wait until opened
        self._find_element(By.CSS_SELECTOR, 'body.customize.config')
        
        # delete workflow-manager
        checkbox = self._find_element(By.CSS_SELECTOR, '#Manager input[name="ids:list"][value="workflow_manager"]')
        checkbox.send_keys(Keys.NULL)
        checkbox.click()
        with self._wait_for_page_load():
            self._find_element(By.CSS_SELECTOR, '#Manager .btn[value="Remove"]').click()
        
        # wait until saved
        self._find_element(By.CSS_SELECTOR, '.alert-success')
        
        self._tear_down()
        print('</WorkflowManagerTest.test_conf>')


if __name__ == "__main__":
    unittest.main()
