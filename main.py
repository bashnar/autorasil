import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from telethon import TelegramClient
import logging
import json
import os

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8649564982:AAFnne80W_He29o6HrOMjpsjaAY3vEDX3RA"
ADMIN_ID = 8114200914

API_ID = 31926413
API_HASH = "506cd5d136a5381edc5eb573b4fe5c58"
SESSION_NAME = "xizxa"

CHANNEL_ID = -1003713838709
POST_ID = 12

CONFIG_FILE = "chat_config.json"

CHAT_CONFIG = {
    -1003797594714: 7200,
    -1002888378116: 3600,
    -1002776178020: 3600,
    -1003971552936: 3600,
    -1002660073561: 3600,
    -1002873200102: 7200,
    -1003795865443: 3600,
    -1002284543190: 3600,
    -1003140815802: 3600,
    -1002258244919: 10800,
    -1003084623439: 3600,
    -1003515586140: 3600,
    -1003992071760: 10800,
    -1003827811673: 3600,
    -1003945561142: 3600,
    -1002093198666: 21600,
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

broadcast_tasks = {}
client_connected = False

def load_config():
    global CHAT_CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                CHAT_CONFIG = json.load(f)
        except:
            pass

def save_config():
    with open(CONFIG_FILE, 'w') as f:
        json.dump(CHAT_CONFIG, f, indent=2)

async def forward_to_chat(chat_id, interval):
    global client_connected
    while True:
        try:
            if not client_connected:
                await asyncio.sleep(5)
                continue
            await client.forward_messages(
                entity=chat_id,
                messages=POST_ID,
                from_peer=CHANNEL_ID
            )
            print(f"Отправлено в чат {chat_id}")
        except Exception as e:
            print(f"Ошибка отправки в {chat_id}: {e}")
        await asyncio.sleep(interval)

async def connect_telethon():
    global client_connected
    try:
        await client.connect()
        if await client.is_user_authorized():
            client_connected = True
            me = await client.get_me()
            print(f"Telethon подключен | {me.first_name}")
        else:
            client_connected = False
    except Exception as e:
        print(f"Ошибка подключения Telethon: {e}")
        client_connected = False

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещен")
        return
    await message.answer(
        "Авторассылка\n\n"
        "/broadcast - запустить\n"
        "/stop - остановить\n"
        "/status - статус\n"
        "/add_chat ID часы - добавить чат\n"
        "/del_chat ID - удалить чат\n"
        "/list_chats - список чатов\n"
        "/set_post ID - установить пост\n"
        "/test ID сообщение - тест\n"
        "/config - конфиг"
    )

@dp.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещен")
        return
    if not client_connected:
        await message.answer("Подключаюсь к Telethon...")
        await connect_telethon()
        await asyncio.sleep(2)
    if not client_connected:
        await message.answer("Не удалось подключиться к Telethon")
        return
    started = 0
    for chat_id, interval in CHAT_CONFIG.items():
        if chat_id not in broadcast_tasks:
            task = asyncio.create_task(forward_to_chat(chat_id, interval))
            broadcast_tasks[chat_id] = task
            started += 1
    await message.answer(
        f"Рассылка запущена\n"
        f"Чатов: {started}\n"
        f"Пост: {POST_ID}\n"
        f"Канал: {CHANNEL_ID}"
    )

@dp.message(Command("stop"))
async def stop_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещен")
        return
    count = len(broadcast_tasks)
    for task in broadcast_tasks.values():
        task.cancel()
    broadcast_tasks.clear()
    await message.answer(f"Рассылка остановлена. Чатов было: {count}")

@dp.message(Command("status"))
async def status_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещен")
        return
    text = "Статус:\n\n"
    text += f"Telethon: {'подключен' if client_connected else 'отключен'}\n"
    text += f"Пост: {POST_ID}\n"
    text += f"Чатов работает: {len(broadcast_tasks)}/{len(CHAT_CONFIG)}\n\n"
    for chat_id, interval in CHAT_CONFIG.items():
        h = interval // 3600
        m = (interval % 3600) // 60
        s = "on" if chat_id in broadcast_tasks else "off"
        text += f"{s} {chat_id} {h}ч {m}м\n"
    await message.answer(text)

@dp.message(Command("add_chat"))
async def add_chat_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещен")
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Использование: /add_chat ID часы")
        return
    try:
        chat_id = int(args[1])
        hours = int(args[2])
        CHAT_CONFIG[chat_id] = hours * 3600
        save_config()
        await message.answer(f"Чат {chat_id} добавлен на {hours}ч")
    except ValueError:
        await message.answer("Неверный формат")

@dp.message(Command("del_chat"))
async def del_chat_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещен")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /del_chat ID")
        return
    try:
        chat_id = int(args[1])
        if chat_id in CHAT_CONFIG:
            del CHAT_CONFIG[chat_id]
            if chat_id in broadcast_tasks:
                broadcast_tasks[chat_id].cancel()
                del broadcast_tasks[chat_id]
            save_config()
            await message.answer(f"Чат {chat_id} удален")
        else:
            await message.answer(f"Чат {chat_id} не найден")
    except ValueError:
        await message.answer("Неверный ID")

@dp.message(Command("list_chats"))
async def list_chats_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещен")
        return
    if not CHAT_CONFIG:
        await message.answer("Нет чатов")
        return
    text = "Чаты:\n\n"
    for chat_id, interval in CHAT_CONFIG.items():
        h = interval // 3600
        m = (interval % 3600) // 60
        s = "on" if chat_id in broadcast_tasks else "off"
        text += f"{s} {chat_id} {h}ч {m}м\n"
    await message.answer(text)

@dp.message(Command("set_post"))
async def set_post_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещен")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /set_post ID")
        return
    global POST_ID
    try:
        POST_ID = int(args[1])
        await message.answer(f"Пост установлен: {POST_ID}")
    except ValueError:
        await message.answer("Неверный ID")

@dp.message(Command("test"))
async def test_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещен")
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Использование: /test ID сообщение")
        return
    try:
        chat_id = int(args[1])
        test_msg = args[2]
        if not client_connected:
            await connect_telethon()
            await asyncio.sleep(2)
        if not client_connected:
            await message.answer("Не удалось подключиться")
            return
        try:
            await client.send_message(chat_id, test_msg)
            await message.answer(f"Отправлено в {chat_id}")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
    except ValueError:
        await message.answer("Неверный ID чата")

@dp.message(Command("config"))
async def config_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ запрещен")
        return
    text = "Конфиг:\n\n"
    text += f"Канал: {CHANNEL_ID}\n"
    text += f"Пост: {POST_ID}\n"
    text += f"Аккаунт: {SESSION_NAME}\n\n"
    text += "Чаты:\n"
    for chat_id, interval in CHAT_CONFIG.items():
        h = interval // 3600
        m = (interval % 3600) // 60
        text += f"{chat_id} {h}ч {m}м\n"
    await message.answer(text)

async def main():
    load_config()
    await connect_telethon()
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())