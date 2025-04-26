import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import os






def random_sleep(min_time=1, max_time=3):
    time.sleep(random.uniform(min_time, max_time))


def random_movement(driver, element):
    try:
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(element, random.randint(-10, 10), random.randint(-10, 10))
        actions.perform()
        random_sleep(0.5, 1.5)
    except:
        pass


def wait_and_find_element(driver, selector_type, selector_value, wait_time=10):
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((selector_type, selector_value))
        )
        return element
    except (TimeoutException, NoSuchElementException) as e:
        print(f"Element not found: {selector_value}")
        return None


def twitter_login(driver, email, username, password):
    try:
        driver.get("https://twitter.com/i/flow/login")
        random_sleep(5, 7)

        # Email field
        email_field = wait_and_find_element(driver, By.CSS_SELECTOR, "input[autocomplete='username']")
        if not email_field:
            print("Taking screenshot of login page...")
            driver.save_screenshot("login_page.png")
            return False

        random_movement(driver, email_field)
        email_field.clear()
        for char in email:
            email_field.send_keys(char)
            random_sleep(0.05, 0.15)

        # Next button
        next_button = wait_and_find_element(driver, By.XPATH,
                                            "//span[contains(text(), 'Next')]/ancestor::div[@role='button']")
        if next_button:
            random_movement(driver, next_button)
            next_button.click()
        else:
            email_field.send_keys(Keys.ENTER)

        random_sleep(3, 4)

        # Username field (if appears)
        username_field = wait_and_find_element(driver, By.CSS_SELECTOR, "input[data-testid='ocfEnterTextTextInput']", 5)
        if username_field:
            random_movement(driver, username_field)
            username_field.clear()
            for char in username:
                username_field.send_keys(char)
                random_sleep(0.05, 0.15)

            next_button = wait_and_find_element(driver, By.XPATH,
                                                "//span[contains(text(), 'Next')]/ancestor::div[@role='button']")
            if next_button:
                random_movement(driver, next_button)
                next_button.click()
            else:
                username_field.send_keys(Keys.ENTER)

            random_sleep(3, 4)

        # Password field
        password_field = wait_and_find_element(driver, By.CSS_SELECTOR, "input[name='password']")
        if not password_field:
            print("Taking screenshot of password page...")
            driver.save_screenshot("password_page.png")
            return False

        random_movement(driver, password_field)
        password_field.clear()
        for char in password:
            password_field.send_keys(char)
            random_sleep(0.05, 0.15)

        # Login button
        login_button = wait_and_find_element(driver, By.XPATH,
                                             "//span[contains(text(), 'Log in')]/ancestor::div[@role='button']")
        if login_button:
            random_movement(driver, login_button)
            login_button.click()
        else:
            password_field.send_keys(Keys.ENTER)

        random_sleep(6, 8)
        return True

    except Exception as e:
        print(f"Login error: {str(e)}")
        driver.save_screenshot("login_error.png")
        return False


def type_reply_text(driver, reply_text):
    try:
        # Find the reply text box
        reply_box = wait_and_find_element(driver, By.CSS_SELECTOR, "div[data-testid='tweetTextarea_0']", 10)
        if not reply_box:
            print("Could not find reply text box")
            return False

        # Click the reply box to focus
        random_movement(driver, reply_box)
        reply_box.click()
        random_sleep(1, 2)

        # Type the reply text character by character (more human-like)
        for char in reply_text:
            reply_box.send_keys(char)
            random_sleep(0.05, 0.2)  # Random delay between keystrokes

        print(f"Typed reply text: {reply_text}")
        return True

    except Exception as e:
        print(f"Error typing reply text: {str(e)}")
        return False


def click_reply_button(driver, post_url, reply_text):
    try:
        print(f"Navigating to post: {post_url}")
        driver.get(post_url)
        random_sleep(5, 7)

        # Scroll to the tweet
        driver.execute_script("window.scrollBy(0, 500);")
        random_sleep(2, 3)

        # Find the tweet container
        tweet_container = wait_and_find_element(driver, By.CSS_SELECTOR, "article[data-testid='tweet']", 15)
        if not tweet_container:
            print("Could not find tweet container")
            return False

        # Find reply button within the tweet container
        reply_button = None
        reply_selectors = [
            "div[data-testid='reply']",
            "div[aria-label='Reply']",
            "div[role='button'][aria-label*='eply']",
            "//*[contains(@aria-label, 'Reply')]",
            "//*[contains(text(), 'Reply')]/ancestor::div[@role='button']"
        ]

        for selector in reply_selectors:
            try:
                if selector.startswith("//"):
                    reply_button = tweet_container.find_element(By.XPATH, selector)
                else:
                    reply_button = tweet_container.find_element(By.CSS_SELECTOR, selector)
                if reply_button:
                    break
            except:
                continue

        if not reply_button:
            print("All reply button selectors failed")
            return False

        # Click the reply button
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reply_button)
        random_sleep(1, 2)

        try:
            random_movement(driver, reply_button)
            reply_button.click()
        except:
            driver.execute_script("arguments[0].click();", reply_button)

        print("Reply button clicked")
        random_sleep(3, 5)

        # Type the reply text
        if not type_reply_text(driver, reply_text):
            return False

        # Verify text was entered
        reply_box = wait_and_find_element(driver, By.CSS_SELECTOR, "div[data-testid='tweetTextarea_0']", 10)
        if reply_box and reply_text in reply_box.text:
            print("Reply text successfully entered")
            driver.save_screenshot("reply_text_entered.png")
            return True

        print("Reply text verification failed")
        return False

    except Exception as e:
        print(f"Error in reply process: {str(e)}")
        driver.save_screenshot("reply_error.png")
        return False


def get_reply_text():
    """Get the reply text from file if it exists"""
    try:
        with open("selected_response.txt", "r") as f:
            return f.read().strip()
    except:
        return reply_text  # fallback to default

# Then modify where you set the reply text to use:
reply_text = get_reply_text()


def main():
    email = "ahmed19904888@gmail.com"
    username = "@rajlokkhi123"
    password = "Sajal12345"
    post_url = "https://x.com/rajlokkhi123/status/1915251831619436771"
    ##
    reply_text = get_reply_text()
    ##
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Mask selenium detection
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.navigator.chrome = {
                runtime: {},
            };
        '''
    })

    try:
        if twitter_login(driver, email, username, password):
            print("Login successful")
            if click_reply_button(driver, post_url, reply_text):
                print("Reply text entered successfully - ready for manual posting")
                # The reply text is now in the box but not posted
                # Browser will stay open so you can review before posting
            else:
                print("Failed to enter reply text")
        else:
            print("Login failed")

        input("Press Enter to close browser...")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()