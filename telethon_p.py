import asyncio
import logging
import pprint
import re
import sys
from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins

api_id = 22635068
api_hash = '215ea3f96f9db89c1da1d68ca612c8f5'
phone = '+447355739673'


forward_to_username = 'MaestroProBot'
bot_id = 6006866508

buy_cost = {
    "2030160217": 0.05,
    "2197950476": 0.001,
    "2215059530": 0.002,
    "default": 0.003
}

cash_data = {}

logging.basicConfig(
    filename='telethon_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

client = TelegramClient('session_name', api_id, api_hash)
sys.stdout.reconfigure(encoding='utf-8')


# Helper to get chat and sender details
async def get_chat_and_sender(event):
    chat = await event.get_chat()
    sender = await event.get_sender()
    return chat, sender


async def process_channel_message(event, sender):
    message_text = event.message.text or ""
    cleaned_message_text = clean_text(message_text)
    # print(f"Channel message text: {cleaned_message_text}")
    await handle_keywords_and_forward(message_text, sender)


def clean_text(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'[\*_]{1,2}', '', text)
    return text


async def handle_keywords_and_forward(message_text, sender):
    forward_text = None
    message_text = re.sub(r'\*\*(.*?)\*\*', lambda m: m.group(1).replace('\n', ' '), message_text, flags=re.DOTALL)

    # ['CA', 'COMPLETED', 'WEBSITE']
    for keyword in ['COMPLETED']:
        match = re.search(rf'\b{keyword}\b:?\s*(?:\n)?\s*(.+)', message_text, re.IGNORECASE | re.DOTALL)
        if match:
            forward_text = match.group(1).strip().split()[0]
            # print(f"Keyword '{keyword}' found. Text to forward: {forward_text}")
            break

    if forward_text:
        forward_text = re.sub(r'`', '', forward_text)
        global cash_data
        forward_to = await client.get_entity(forward_to_username)
        cash_data[forward_text] = {'tg_id': sender.id,
                                   'message_id': 0,
                                   'sine_opshin': False,
                                   'enable_button': False,
                                   'buy_set': False}
        await client.send_message(forward_to, f"{forward_text}")
        # await client.send_message(forward_to, f"{forward_text}\n#tg_id:{sender.id}")

        await asyncio.sleep(1)
    else:
        print(f"No actionable keywords found in message from {sender.id}.")


async def wait_for_buttons(entity, buttons_list, min_buttons):
    async for message in client.iter_messages(entity, limit=3):
        if hasattr(message, 'reply_markup') and message.reply_markup:
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    buttons_list.append(button.text)
                    if button.text == '❌ Snipe Disabled' or button.text == '✅ Snipe Enabled':
                        return message
            if len(buttons_list) >= min_buttons:
                return message
            await asyncio.sleep(0.001)
        await asyncio.sleep(0.001)
    return None


async def wait_for_reply_and_send_amount(entity, amount):
    async for reply_message in client.iter_messages(entity, limit=5):
        if reply_message.text and "Reply" in reply_message.text:
            await client.send_message(entity, amount, reply_to=reply_message.id)
            print(f"Sent buy amount: {amount}")
            break
        await asyncio.sleep(0.001)


@client.on(events.NewMessage(from_users=bot_id))
async def handle_message_new_out(event):
    global cash_data
    first_button = False
    snipe_now_button = False
    if hasattr(event.message, 'reply_markup') and event.message.reply_markup:
        for row in event.message.reply_markup.rows:
            for button in row.buttons:
                try:
                    if button.text == '⚙ Snipe Options':
                        first_button = True
                        break
                    elif button.text in '🎯 Snipe Now':
                        snipe_now_button = True
                except AttributeError:
                    pass
            await asyncio.sleep(0.001)
        await asyncio.sleep(0.001)
    elif "✅ Snipe amount set to" in event.message.text:
        # Search for the pattern in the text
        match = re.search(r'for\s+`([A-Za-z0-9]+)`', event.message.text)
        # Extract and print the address if a match is found
        if match:
            crypto_address = match.group(1)
            crypto_address = re.sub(r'`', '', crypto_address)
            cash_data.pop(crypto_address)
        else:
            print("No address found")
    if first_button:
        pattern_1 = r'\[CA\]\(https://solscan\.io/token/([A-Za-z0-9]+)\): `([A-Za-z0-9]+)`'
        match_1 = re.search(pattern_1, event.message.text)
        first_ca = match_1.group(1)
        first_ca = re.sub(r'`', '', first_ca)

        if snipe_now_button:
            cash_data[first_ca]['sine_opshin'] = True
            await event.message.click(5)
        else:
            cash_data[first_ca]['sine_opshin'] = True
            await event.message.click(4)
    else:
        pass


@client.on(events.MessageEdited(from_users=bot_id, incoming=True))
async def handle_message_edit(event):
    global cash_data
    forward_to = await client.get_entity(forward_to_username)
    button_enable = False
    there_is_button = False
    if hasattr(event.message, 'reply_markup') and event.message.reply_markup:
        for row in event.message.reply_markup.rows:
            for button in row.buttons:
                try:
                    if button.text == '✅ Snipe Enabled':
                        there_is_button = True
                        button_enable = True
                        break
                    elif button.text == '❌ Snipe Disabled':
                        there_is_button = True
                        break
                except AttributeError:
                    pass
            await asyncio.sleep(0.001)
        await asyncio.sleep(0.001)
    if there_is_button:
        pattern_1 = r'\[CA\]\(https://solscan\.io/token/([A-Za-z0-9]+)\): `([A-Za-z0-9]+)`'
        match_1 = re.search(pattern_1, event.message.text)
        first_ca = match_1.group(1)
        first_ca = re.sub(r'`', '', first_ca)
        pprint.pprint(cash_data)
        buy_set_status = cash_data[f'{first_ca}']
        buy_see = buy_set_status['buy_set']
        clicked_disable_button = cash_data[first_ca]['enable_button']
        if button_enable and not buy_see:
            cost_amount = buy_cost.get('default')
            await event.message.click(7)
            try:
                cosy_detect = cash_data[first_ca]
                cosy_detect = cosy_detect['tg_id']
                cost_amount = buy_cost.get(f"{cosy_detect}")
                if cost_amount is None:
                    cost_amount = buy_cost.get('default')
            except:
                pass
            cash_data[first_ca]['buy_set'] = True
            await wait_for_reply_and_send_amount(forward_to, f'{cost_amount}')

        elif not clicked_disable_button:
            cash_data[first_ca]['enable_button'] = True
            await event.message.click(5)


    else:
        pass


@client.on(events.NewMessage(from_users=bot_id, pattern=r"❌ This token has launched already\."))
async def handle_message_send_none(event):
    global cash_data
    forward_to = await client.get_entity(forward_to_username)
    second_menu_buttons = []
    msg_with_second_menu = await wait_for_buttons(forward_to, second_menu_buttons, 4)

    if msg_with_second_menu:

        pattern_1 = r'\[CA\]\(https://solscan\.io/token/([A-Za-z0-9]+)\): `([A-Za-z0-9]+)`'
        match_1 = re.search(pattern_1, msg_with_second_menu.text)
        first_ca = match_1.group(1)
        first_ca = re.sub(r'`', '', first_ca)
        if first_ca:
            cost_amount = buy_cost.get('default')
            try:
                cosy_detect = cash_data[first_ca]
                cosy_detect = cosy_detect['tg_id']
                cost_amount = buy_cost.get(f"{cosy_detect}")
                if cost_amount is None:
                    cost_amount = buy_cost.get('default')
            except:
                pass
            buy_set_status = cash_data[first_ca]['buy_set']
            if buy_set_status is False:
                await msg_with_second_menu.click(7)  # Click the buy button
                cash_data[first_ca]['buy_set'] = True
                await wait_for_reply_and_send_amount(forward_to, f'{cost_amount}')
            else:
                pass




# Define event handler for incoming messages
@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    chat, sender = await get_chat_and_sender(event)
    chat_data = chat.to_dict() if hasattr(chat, 'to_dict') else None

    # Check if the chat is a broadcast
    if getattr(chat, 'broadcast', False):
        await process_channel_message(event, sender)

    # Check if the chat is a megagroup (supergroup)
    elif getattr(chat, 'megagroup', False):
        sender_id = sender.id
        admins = {admin.id for admin in await client.get_participants(chat, filter=ChannelParticipantsAdmins)}

        if sender_id in admins:
            # print(f"Message from admin: - {event.message.text}")
            await process_channel_message(event, sender)
        elif getattr(sender, 'left', False):
            # print(f"Message from admin with 'left': - {event.message.text}")
            await process_channel_message(event, sender)
        else:
            pass
            # print(f"Message from user: - {event.message.text}")

    # Check if chat data indicates a chat group
    elif chat_data and chat_data.get('_') == 'Chat':
        group_id = f"-100{chat_data.get('id')}"
        group = await client.get_entity(group_id)
        sender_id = sender.id
        admins = {admin.id for admin in await client.get_participants(group, filter=ChannelParticipantsAdmins)}

        if sender_id in admins:
            # print(f"Message from admin: - {event.message.text}")
            await process_channel_message(event, sender)
        elif getattr(sender, 'left', False):
            # print(f"Message from admin with 'left': - {event.message.text}")
            await process_channel_message(event, sender)
        else:
            pass
            # print(f"Message from user: - {event.message.text}")


async def main():
    print("Starting client...")
    await client.start(phone)
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("Stopping client...")
    finally:
        await client.stop()


asyncio.run(main())
