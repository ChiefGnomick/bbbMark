from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import threading
import time
import re

class BBBBot:
    def __init__(self, username, bbb_url, max_wait, leave_percent, 
                 greeting_msg, farewell_msg, send_greeting, send_farewell):
        self.driver = webdriver.Chrome()
        self.username = username
        self.bbb_url = bbb_url
        self.max_users = 0
        self.start_time = time.time()
        self.exit_flag = False
        self.MAX_WAIT = max_wait
        self.LEAVE_PERCENT = leave_percent
        self.CHECK_INTERVAL = 10
        self.greeting_msg = greeting_msg
        self.farewell_msg = farewell_msg
        self.send_greeting = send_greeting
        self.send_farewell = send_farewell

    def login(self):
        self.driver.get(self.bbb_url)
        
        # Поиск поля ввода по плейсхолдеру на русском или английском
        username_input = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, 
                "//input[@placeholder='Введите ваше имя!' or @placeholder='Enter your name!']"))
        )
        username_input.clear()
        username_input.send_keys(self.username)

        # Поиск кнопки присоединения по тексту
        join_button = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, 
                "//button[contains(., 'Присоединиться') or contains(., 'Join')]"))
        )
        join_button.click()
        
        try:
            # Поиск кнопки "Только слушать" по тексту в дочернем элементе
            listen_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[.//*[contains(text(), 'Только слушать') or contains(text(), 'Only Listen')]]"))
            )
            listen_button.click()
        except TimeoutException:
            pass

    def send_message(self, message):
        if not message:
            return
            
        try:
            # Поиск поля ввода сообщения по плейсхолдеру
            chat_input = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, 
                    "//textarea[@placeholder='Сообщение в Общий чат' or @placeholder='Message Public Chat']"))
            )
            chat_input.send_keys(message)
            
            # Поиск кнопки отправки по тексту в дочернем элементе
            send_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[.//*[contains(text(), 'Отправить сообщение') or contains(text(), 'Send message')]]"))
            )
            send_button.click()
        except TimeoutException:
            pass

    def get_user_count(self):
        try:
            user_counter = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, 
                    '//h2[contains(., "Users") or contains(., "Пользователи")]'))
            )
            count_text = user_counter.text
    
            match = re.search(r'\((\d+)\)', count_text)
            return int(match.group(1)) if match else 0
                
        except TimeoutException:
            try:
                user_counter = self.driver.find_element(By.CSS_SELECTOR, '[data-test="userListCounter"]')
                return int(re.search(r'\d+', user_counter.text).group())
            except:
                return 0
    
    def check_conditions(self):
        while not self.exit_flag:
            elapsed_time = (time.time() - self.start_time) / 60
            if elapsed_time >= self.MAX_WAIT:
                self.exit_procedure()
                break

            current_users = self.get_user_count()
            
            if current_users > self.max_users:
                self.max_users = current_users

            if self.max_users > 0 and current_users <= self.LEAVE_PERCENT * self.max_users:
                self.exit_procedure()
                break

            time.sleep(self.CHECK_INTERVAL)

    def exit_procedure(self):
        self.exit_flag = True
        if self.send_farewell:
            self.send_message(self.farewell_msg)
        time.sleep(3)
        self.driver.quit()

    def run(self):
        try:
            self.login()
            time.sleep(15)
            if self.send_greeting:
                self.send_message(self.greeting_msg)
            thread = threading.Thread(target=self.check_conditions)
            thread.start()
            thread.join()
        except:
            self.driver.quit()

if __name__ == "__main__":
    bbb_url = input("Введите URL конференции BBB: ").strip()
    while not bbb_url:
        bbb_url = input("Введите URL конференции BBB: ").strip()

    username = input("Введите ваше имя пользователя: ").strip()
    while not username:
        username = input("Введите ваше имя пользователя: ").strip()

    while True:
        try:
            max_wait = int(input("Максимальное время работы (минут): "))
            break
        except:
            pass

    while True:
        try:
            leave_percent = float(input("Процент для выхода (0-1): "))
            if 0 <= leave_percent <= 1:
                break
        except:
            pass

    send_greeting = input("Отправлять приветствие? (y/n): ").lower() == 'y'
    greeting_msg = ""
    if send_greeting:
        greeting_msg = input("Введите приветственное сообщение: ").strip()

    send_farewell = input("Отправлять прощальное сообщение? (y/n): ").lower() == 'y'
    farewell_msg = ""
    if send_farewell:
        farewell_msg = input("Введите прощальное сообщение: ").strip()

    bot = BBBBot(
        username=username, 
        bbb_url=bbb_url, 
        max_wait=max_wait, 
        leave_percent=leave_percent,
        greeting_msg=greeting_msg,
        farewell_msg=farewell_msg,
        send_greeting=send_greeting,
        send_farewell=send_farewell
    )
    bot.run()