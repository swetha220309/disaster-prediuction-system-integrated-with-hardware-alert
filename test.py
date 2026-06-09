from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()
driver.get("http://127.0.0.1:8000/")

time.sleep(2)

driver.find_element(By.NAME, "latitude").send_keys("1.3521")
driver.find_element(By.NAME, "longitude").send_keys("103.8198")

magnitude_input = driver.find_element(By.NAME, "magnitude")
magnitude_input.clear()
driver.find_element(By.NAME, "magnitude").send_keys("58.2")

duration_input = driver.find_element(By.NAME, "duration")
duration_input.clear()
driver.find_element(By.NAME, "duration").send_keys("0")

# Fix date input
date_input = driver.find_element(By.NAME, "date")
driver.execute_script(
    "arguments[0].value = '2026-03-01';",
    date_input
)
time.sleep(3) # comment if not need delay
driver.find_element(By.TAG_NAME, "form").submit()

time.sleep(5)

print(driver.page_source)

driver.quit()