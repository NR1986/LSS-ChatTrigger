from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
import time
from datetime import datetime
import mysql.connector

# Beschreibung: Script welches auf [Target-Text] im Chat vom Leitstellenspiel reagiert und diesen in eine 'MariaDB' speichert.
# Author:   NiRoLP
# Version: 1.0.0


# Benutzerdaten
username = 'mailadresse'
password = 'passwort'

# MariaDB-Verbindungsinformationen
db_config = {
    'user': 'username',
    'password': 'passwort',
    'host': 'ipadresse',
    'database': 'datenbankname',
    'raise_on_warnings': True,
}

last_event_timestamp = None

def login(driver, username, password):
    driver.get('https://www.leitstellenspiel.de/users/sign_in')

    email_field = driver.find_element(By.NAME, 'user[email]')
    password_field = driver.find_element(By.NAME, 'user[password]')

    email_field.send_keys(username)
    password_field.send_keys(password)

    password_field.submit()

    chat_panel_selector = By.ID, 'chat_panel'
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(chat_panel_selector))

def insert_message_into_database(timestamp, username, message_text, db_cursor):
    timestamp_mysql_format = datetime.strptime(timestamp, '%d.%m.%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')

    insert_query = "INSERT INTO chat_messages (timestamp, username, message_text) VALUES (%s, %s, %s)"
    data = (timestamp_mysql_format, username, message_text)
    db_cursor.execute(insert_query, data)

def monitor_chat(driver):
    global last_event_timestamp

    chat_panel_selector = By.ID, 'mission_chat_messages'
    chat_panel = WebDriverWait(driver, 10).until(EC.presence_of_element_located(chat_panel_selector))

    while True:
        chat_messages = chat_panel.find_elements(By.XPATH, './/li')

        for message in chat_messages:
            timestamp = message.get_attribute('data-message-time')
            username = message.find_element(By.CLASS_NAME, 'chat-username').text
            message_text = message.text

            target_text = 'Hallo' #Hier steht das Trigger-Wort. In diesem Fall reagiert das Script auf das Wort Hallo
            if target_text.lower() in message_text.lower():
                timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')
                timestamp_str = timestamp.strftime('%d.%m.%Y %H:%M:%S')

                if last_event_timestamp is None or timestamp.timestamp() > last_event_timestamp:
                    print(f'Die Nachricht "{message_text}" wurde um {timestamp_str} von {username} im Chat gefunden!')
                    last_event_timestamp = timestamp.timestamp()

                    db_connection = mysql.connector.connect(**db_config)
                    
                    db_cursor = db_connection.cursor()
                    
                    insert_message_into_database(timestamp_str, username, message_text, db_cursor)
                    
                    db_connection.commit()
                    
                    db_cursor.close()
                    
                    db_connection.close()

        time.sleep(1)

chrome_driver_path = ChromeDriverManager().install()

chrome_service = ChromeService(chrome_driver_path)

with webdriver.Chrome(service=chrome_service) as driver:
    login(driver, username, password)
    monitor_chat(driver)
    keep_script_running()
