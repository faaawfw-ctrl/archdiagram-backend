from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

# === Переменные окружения (токены) ===
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
SUBSCRIPTIONS_FILE = 'subscribers.json'

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("⚠️ ВНИМАНИЕ: TELEGRAM_TOKEN и TELEGRAM_CHAT_ID не заданы!")

# === Загрузка подписчиков ===
def load_subscribers():
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_subscriber(email, plan):
    subs = load_subscribers()
    subs[email] = {
        'plan': plan,
        'active': True,
        'subscribed_at': datetime.now().isoformat()
    }
    with open(SUBSCRIPTIONS_FILE, 'w') as f:
        json.dump(subs, f, indent=2)

# === Отправка в Telegram ===
def send_telegram_message(chat_id, text):
    if not TELEGRAM_TOKEN:
        return
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    try:
        requests.post(url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }, timeout=5)
    except Exception as e:
        print('Ошибка отправки в Telegram:', e)

# === Webhook для Lava ===
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print('Получен webhook:', data)

    status = data.get('status')
    if status != 'success':
        return 'OK', 200

    email = data.get('email') or data.get('customer_email')
    plan = data.get('product_name') or 'Pro'

    if not email:
        return 'OK', 200

    save_subscriber(email, plan)

    # Уведомление админу
    admin_msg = f'✅ Новая подписка!\n📧 {email}\n📦 {plan}'
    send_telegram_message(TELEGRAM_CHAT_ID, admin_msg)

    # Доступ пользователю
    user_msg = f'''🎉 Спасибо за подписку на {plan}!

🚀 Ваш доступ: https://archdiagram.netlify.app/generator.html
🔑 email: {email}'''
    send_telegram_message(email, user_msg)

    return 'OK', 200

@app.route('/')
def index():
    return '✅ ArchDiagram бэкенд работает'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)