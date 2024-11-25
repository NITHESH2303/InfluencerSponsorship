import random

import requests


def get_follower_count(platform):
    if platform == 'Twitter':
        return random.randint(1000, 10000)
    elif platform == 'Instagram':
        return random.randint(5000, 20000)
    elif platform == 'Youtube':
        return random.randint(10000, 50000)
    return 0

def send_google_chat_message(webhook_url, message):
    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to send Google Chat message: {response.text}")
