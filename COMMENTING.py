from LOLZTEAM.API import Forum, Market
import json
from telethon import TelegramClient, events, utils
from telethon.tl.functions.messages import GetDialogFiltersRequest, UpdateDialogFilterRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.account import SetPrivacyRequest, UpdateProfileRequest, UpdateNotifySettingsRequest
from telethon.tl.types import InputPrivacyKeyProfilePhoto, InputPrivacyKeyAbout, InputPrivacyKeyPhoneCall, \
    InputPrivacyValueAllowAll, InputPrivacyValueDisallowAll, Channel, InputNotifyPeer, InputPeerNotifySettings
from telethon.tl.functions.chatlists import (
    JoinChatlistInviteRequest,
    CheckChatlistInviteRequest,
)
from telethon.errors.rpcerrorlist import ChannelsTooMuchError, BadRequestError
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged
import time
import asyncio
import os
import random

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzUxMiJ9.eyJzdWIiOjgwODI3NDksImlzcyI6Imx6dCIsImV4cCI6MCwiaWF0IjoxNzQ3MTczNjE1LCJqdGkiOjc4NDg1MCwic2NvcGUiOiJiYXNpYyByZWFkIHBvc3QgY29udmVyc2F0ZSBwYXltZW50IGludm9pY2UgbWFya2V0IG1hcmtldDpwMnAifQ.rKl-5vsAZCkXX9yiXlxn9atMRWffkhKt_EebvmuP95xRgO_A9Lls-PMwgGUN4swUt1yj9h5ter-fTldiro7q1apCjmMgj5m1LBO3HHhT-v6NOjb5wre27mjXM2UU-atJnelt5XsHkLfqIkSLKBU6YavK2KfPIOFyZlpEjxzFG-Q"
market = Market(token=token, language="en")
forum = Forum(token=token, language="en")

def purchase():
    response = market.category.telegram.get(pmax=50.0, password='no', spam='no', title = ['Продажа Прямо с панели | Мной не использовались | web | живой трафик'])
    for i in (response.json()['items']):

        print(i['title'], f'\nprice: {i['price']}')
        id = i['item_id']
        x = int(input())
        if x == 1:
            response = market.purchasing.confirm(id)
            print(response.json())
            break
        else:
            continue

async def authorization(price,index):
    response = market.list.purchased()
    data = response.json()
    item_id = int(data['items'][index]['item_id'])
    for item in data['items']:
        if item['item_id'] == item_id:
            phone_number = item["telegram_phone"]
            telegram_data = json.loads(item['telegram_json'])

            app_id = telegram_data.get("app_id")
            app_hash = telegram_data.get("app_hash")

            print(f"app_id: {app_id}")
            print(f"app_hash: {app_hash}")
            print(f'Номер телефона:{phone_number}')
            await normis(app_id,app_hash,phone_number,item_id,price)
            break
    else:
        print("item_id не найден.")

async def normis(api_id,api_hash,phone_number,item_id,price):
    s = find_unique_session_name()
    with open('Proxy.txt', 'r', encoding='utf-8') as filik:
        lines = filik.readlines()  # Читаем все строки в список
    proxy_str = random.choice(lines)
    host, port, username, password = proxy_str.split(":")
    port = int(port)
    proxy = ("socks5", host, port, username, password)
    client = TelegramClient(s, api_id, api_hash, proxy = proxy, connection=ConnectionTcpAbridged)
    account_link = f'https://lzt.market/{item_id}/'
    with open('Purchased.txt', 'a', encoding='utf-8') as log_file:
        log_file.write(f'{account_link} | Цена - {price}\n')
    await client.connect()
    flag = 0
    for g in range(2):
        if flag == 1:
            break
        await client.send_code_request(phone_number)
        for i in range(3):
            try:
                await asyncio.sleep(90)
                response = market.managing.telegram.code(item_id=item_id)
                print(response.json())
                print('Код подтверждения:', response.json()['codes'][0]['code'])  # Код подтверждения
                code = response.json()['codes'][0]['code']
                flag = 1
                break
            except Exception as e:
                print(f'Ошибка при получении кода: {e}\nСледующая попытка через 30 секунд. Попыток осталось: {3-i}')
                await asyncio.sleep(30)
    await client.sign_in(phone_number, code)
    print("Успешно авторизованы!")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    photos_folder = current_dir
    photos = [f for f in os.listdir(photos_folder) if f.endswith('.png')]
    if not photos:
        print("В папке нет .png файлов.")
        return
    random_photo = random.choice(photos)
    photo_path = os.path.join(photos_folder, random_photo)

    await client(DeletePhotosRequest(await client.get_profile_photos('me')))

    uploaded_file = await client.upload_file(photo_path)
    await client(UploadProfilePhotoRequest(file=uploaded_file))
    print(f"Аватарка успешно изменена на {random_photo}")

    await set_privacy_settings(client) #Настройки приватности
    await set_name(client)
    end_time = time.time() + 2 * 60 * 60  # 2 часа в секундах
    nach_time = time.time()

    await clear_folders(client)
    await subscribe(client)
    channels = await get_subscribed_channels(client)

    last_check_time = 0
    setup_event_handlers(client, channels)

    while time.time() < end_time:
        await asyncio.sleep(1)# Ждем 1 секунду перед следующей проверкой
        if time.time() - last_check_time >= 600:
            await client.send_message('@SpamBot','/start')
            await asyncio.sleep(5)
            result = await check_spam_bot(client)
            if result != 'Без блокировки':
                with open('Finish.txt', 'a', encoding='utf-8') as log_file:
                    log_file.write(f'{account_link}: Spam block, время работы - {(int(time.time()) - int(nach_time))/60} минут, цена - {price}\n')
                    await client.disconnect()
                    break
            last_check_time = time.time()
    if result == 'Без блокировки':
        with open('Finish.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(f'{account_link}: Без блокировки, время работы - {(int(time.time()) - int(nach_time)) / 60} минут\n')
        await client.disconnect()

with open('comments.txt', 'r', encoding='utf-8') as file:
    comments = file.read().splitlines()

def generate_session_name(length=15):
    characters = 'abcdefgqwertypolikujmnb'
    return ''.join(random.choice(characters) for _ in range(length))

async def set_name(client):
    with open('name.txt', 'r', encoding='utf-8') as f:
        names = f.readlines()
    first_name = random.choice(names)
    last_name = ''
    await client(UpdateProfileRequest(
        first_name=first_name,
        last_name=last_name
    ))
    print(f"Профиль обновлен: {first_name}")

def find_unique_session_name():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = current_dir
    while True:
        s_name = generate_session_name()
        full_path = os.path.join(folder_path, f"{s_name}.session")
        if not os.path.exists(full_path):
            return s_name

def setup_event_handlers(client,channels):
    @client.on(events.NewMessage(chats=channels))
    async def new_post_listener(event):
        print(f"Получено новое сообщение в канале: {event.chat.title}")
        try:
            random_comment = random.choice(comments)
            chat_id = event.chat_id
            message_id = event.message.id
            sent_message = await client.send_message(chat_id, random_comment, comment_to=message_id)
            print(f"Оставил комментарий под постом в канале {event.chat.title}: {random_comment}")
            await check_comment_status(client, sent_message, event.chat.username)
        except Exception as e:
            print(f"Не удалось оставить комментарий: {e}")
            return 0
        print('Функция для комментинга отработала')

async def clear_chat_by_username(client, username):
    try:
        entity = await client.get_entity(username)
        await client.delete_dialog(entity)
        print(f"Диалог с {username} очищен")
    except Exception as e:
        print(f"Ошибка при очистке диалога с {username}: {e}")

async def check_spam_bot(client):
    try:
        await client.send_message('@SpamBot', '/start')
        await asyncio.sleep(5)
        messages = await client.get_messages('@SpamBot', limit=1)

        if messages and messages[0].message:
            response_text = messages[0].message
            print(f"Сообщение от SpamBot: {response_text}")

            if "Ваш аккаунт свободен от каких-либо ограничений." in response_text or 'Good news, no limits are currently applied to your account. You’re free as a bird!' in response_text:
                await clear_chat_by_username(client, '@SpamBot')
                return "Без блокировки"
            else:
                await clear_chat_by_username(client, '@SpamBot')
                return "Spam block"
        else:
            print("Не удалось получить сообщение от SpamBot.")
            await clear_chat_by_username(client, '@SpamBot')
            return "Неизвестно"
    except Exception as e:
        print(f"Ошибка при проверке сообщений от SpamBot: {e}")
        await clear_chat_by_username(client, '@SpamBot')
        return "Ошибка"

async def check_comment_status(client,comment, channel_name):
    try:
        # Первая проверка через 10 секунд
        await asyncio.sleep(10)
        first_check = await client.get_messages(comment.chat_id, ids=comment.id)
        status_1 = "Да" if first_check else "Нет"

        # Вторая проверка через еще 10 секунд
        await asyncio.sleep(10)
        second_check = await client.get_messages(comment.chat_id, ids=comment.id)
        status_2 = "Да" if second_check else "Нет"

        # Записываем данные в файл logs.txt
        with open('Logs.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(f'"{channel_name}" | {status_1} | {status_2}\n')
    except Exception as e:
        print(f"Ошибка при проверке статуса комментария: {e}")

async def set_privacy_settings(client):
    await client(SetPrivacyRequest(
        key=InputPrivacyKeyProfilePhoto(),
        rules=[InputPrivacyValueAllowAll()]
    ))

    await client(SetPrivacyRequest(
        key=InputPrivacyKeyAbout(),
        rules=[InputPrivacyValueAllowAll()]
    ))

    await client(SetPrivacyRequest(
        key=InputPrivacyKeyPhoneCall(),
        rules=[InputPrivacyValueDisallowAll()]
    ))

    await client(UpdateNotifySettingsRequest(
        peer=InputNotifyPeer(all=True),
        settings=InputPeerNotifySettings(
            silent=True,
            mute_until=2 ** 31 - 1,
            show_previews=False
        )
    ))

    with open('bio.txt', 'r', encoding='utf-8') as f:
        bios = [line.strip() for line in f.readlines() if line.strip()]
    new_about = random.choice(bios)
    await client(UpdateProfileRequest(about=new_about))  # Устанавливаем новое описание
    print(f"Описание профиля успешно изменено на: {new_about}")

    print("Настройки приватности успешно изменены!")

async def subscribe(client):
    with open('folders.txt', 'r') as file:
        links = file.read().splitlines()

        # Очищаем существующие папки перед подпиской
    # await clear_folders(client)

    for folder_hash in links:
        try:
            # Проверяем валидность инвайт-ссылки папки
            response = await client(CheckChatlistInviteRequest(slug=folder_hash))
            chat_peers = response.peers

            # Присоединяемся к папке
            await client(JoinChatlistInviteRequest(slug=folder_hash, peers=chat_peers))
            print(f"Успешно присоединились к папке с хешем: {folder_hash}")
            await clear_folders(client)
        except ChannelsTooMuchError:
            print(f"Превышен лимит на количество каналов или папок. Хеш: {folder_hash}")
        except BadRequestError:
            print(f"Неверный хеш папки или достигнут лимит папок. Хеш: {folder_hash}")
        except Exception as e:
            print(f"Ошибка при подписке на папку {folder_hash}: {e}")

async def get_subscribed_channels(client):
    dialogs = await client.get_dialogs()
    channels = [dialog for dialog in dialogs if isinstance(dialog.entity, Channel)]
    channel_links = []

    for channel in channels:
        if channel.entity.username:
            link = f"https://t.me/{channel.entity.username}"
            channel_links.append(link)
            print(f"Название: {channel.name}, ID: {channel.id}, Username: {channel.entity.username}, Ссылка: {link}")
    return channel_links

async def clear_folders(client):
    try:
        response = await client(GetDialogFiltersRequest())
        for folder in response.filters:
            try:
                await client(UpdateDialogFilterRequest(id=folder.id, filter=None))
            except AttributeError:
                continue
        print("Все папки успешно удалены.")
    except Exception as e:
        print(f"Ошибка при удалении папок: {e}")

def read_ids():
    with open("id.txt", "r", encoding="utf-8") as file:
        return set(line.strip() for line in file if line.strip())

def write_id(id):
    with open("id.txt", "a", encoding="utf-8") as file:
        file.write(f"{id}\n")

def clear_id_file():
    with open('id.txt', 'w', encoding='utf-8') as file:
        pass

async def main():
    clear_id_file()
    while True:
        try:
            print('Покупка...')
            response = market.category.telegram.get(pmax=50, password='no', spam='no', order_by='price_to_up', **{"country[]": ["KZ"], "origin[]": ["fishing"]})
            print(response)
            items = response.json()['items']
            existing_ids = read_ids()
            for i in range(len(items)):
                item = items[i]
                price = item['price']
                print(item)
                print(item['title'], f'\nprice: {item['price']}, {item['telegram_country']}')
                id = item['item_id']
                if str(id) in existing_ids:
                    print(f"ID {id} уже был, пропускаем...")
                    continue
                write_id(id)
                print(market.purchasing.check(id))
                response = market.purchasing.check(id)
                print(response.json()['status'])

                await asyncio.sleep(10)  # Заменяем time.sleep() на await asyncio.sleep()
                if response.json()['status'] == 'ok':
                    response = market.purchasing.confirm(id)
                    await asyncio.sleep(3)
                    if 'errors' in response.json():
                        error_message = response.json()['errors'][0]
                        if "You do not have enough money to buy this product. Add credit" in error_message:
                            print(f"Ошибка: {error_message}. Программа завершает работу.")
                            return 0 # Выходим из функции
                        else:
                            print(f"Ошибка при покупке аккаунта: {error_message}")
                            continue
                    await asyncio.sleep(5)

                    await authorization(price,0)

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            await asyncio.sleep(30)
x = int(input('Стандартное выполнение программы - введите 1\nИспользовать определенный аккаунт - введите 0\n'))
if x == 1:
    asyncio.run(main())
if x == 0:
    n = int(input('Введите номер нужного аккаунта\n(0 - последний купленный\n1-предпоследний и т.д.)\n'))
    asyncio.run(authorization('10',n))