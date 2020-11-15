# How to run Selenium Acceptance Tests

## Setup

Geckodriver needs to be installed in the $PATH from: https://github.com/mozilla/geckodriver/releases
Firefox Extended Support Release needs to be installed from: https://www.mozilla.org/en-US/firefox/organizations/all/

Install the testing requirements via:

    pip install -r selenium_tests/requirements.txt

The tests expect a running zope instance on http://localhost:8080 with login admin:admin - and you will have to create a file `zms/selenium_tests/credentials.txt` with content:

    [ac_server]
    base_url=http://localhost:8080
    login=admin
    password=admin
    firefox_path=/absolute/path/to/your/extended/support/version/of/firefox
    # last key is optional. If it is missing, the system firefox has to be an ESR build

If you want to test against a different server, you will have to modify / swap this file accoringly.

When starting from scratch, the full sequence of commands to get a working checkout to run unit tests from should be:

    $ cd /path/where/the/virtualenv/should/be
    $ virtualenv zms_virtualenv
    $ source zms_virtualenv/bin/activate # on windows probably $ path/to/zms_virtualenv/bin/activate.bat
    $ cd /path/to/zms3/repo/checkout
    $ pip install -r requirements.txt
    $ pip install -r selenium_tests/requirements.txt
    $ pip install -e . # equivalent to python setup.py develop

## Run them

To run all tests:

    python -m unittest discover -s selenium_tests -p '*test.py'

or

    pytest selenium_tests

`pytest` is used on the server (and has nice features) so it might be usefull locally too.

To run a specific test:

    python -m unittest selenium_tests.example_test.LoginTestCase.test_login

Here `selenium_tests.login_test.LoginTestCase` would run all tests in that class or `selenium_tests.login_test` all tests in all `unittest.TestCase` subclasses in the module.


## Write new tests

Every test should be a function starting with "test_" in a file in
the test folder. Usually one class groups multiple tests, for example

class PageTest(SeleniumTestCase):
    def test_create_page(self):
        ....
    def test_delete_page(self):
        ....
    def test_publish_page(self):
        ....
    
New files and tests are found automatically, there is no need to include
or declare them somewhere. Every test method will execute "setUp" before.
Tests run independently from each other (i.e. "self" will be "clean" on
every test).

Find out more about the TestCase superclass and Python testing at:
https://docs.python.org/2/library/unittest.html

## Hints / Links

The "example" test should give you an idea of how a general Selenium
test could work. The setUp (in SeleniumTestCase) creates a "WebDriver"
in `self.driver`, this is basically a browser session.
You can use this WebDriver to find DOM elements, or to change frames,
etc.
See https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html
for API of the driver element.

The self.driver.find* methods usually return a WebElement (basically a
dom node) that you can do assertions with:
https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webelement.html#selenium.webdriver.remote.webelement.WebElement

Output from acceptance tests should be put into `/test_output` - this directory is also exposed in jenkins, so anything put there will be available via the web interface. To generate unique paths in that directory that include the testname use the method `_unique_test_output_filename()` 

Great overview of the Selenium Python API: https://selenium-python.readthedocs.io/
Official API documentation: https://seleniumhq.github.io/selenium/docs/api/py/api.html
Consider to use PageObjects: https://selenium-python.readthedocs.io/page-objects.html

Wait for everything! If something is not waited for, the test will sometimes not work.

## Selenium interactively

If you want to explore the Selenium API, it is best to set a debugger
into a test (import pdb; pdb.set_trace()) and run the test (see above how to do that).
Or you can use a python interactive console and use Selenium through that. See this example for that:

    from selenium import webdriver
    
    driver = webdriver.Firefox()
    driver.implicitly_wait(10)
    driver.get("http://docs.seleniumhq.org/")
    driver.find_element_by_link_text('Download').click()
    driver.find_element_by_link_text('Selenium Html Runner').click()

## System under Test

The tests run against a private instance of zms on dev.yeepa.de which is not accessible from the outside. 
The admin login information are simply hard coded in the test (for now). The system can updates itself
and installs a new ZMS on every commit to the repo. Dependencies are updated to what is specified in the requirements.txt in the repository.
