import asyncio
import pprint
import re
import sys
from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins

api_id = 22635068
api_hash = '215ea3f96f9db89c1da1d68ca612c8f5'
phone = '+447355739673'

forward_to_username = 'MaestroSniperBot'

client = TelegramClient('session_name1', api_id, api_hash)
sys.stdout.reconfigure(encoding='utf-8')


# Helper to get chat and sender details
async def get_chat_and_sender(event):
    chat = await event.get_chat()
    sender = await event.get_sender()
    return chat, sender


# Define event handler for incoming messages
@client.on(events.NewMessage())
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
            print(f"Message from admin: - {event.message.text}")
            await process_channel_message(event, sender)
        elif getattr(sender, 'left', False):
            print(f"Message from admin with 'left': - {event.message.text}")
            await process_channel_message(event, sender)
        else:
            print(f"Message from user: - {event.message.text}")

    # Check if chat data indicates a chat group
    elif chat_data and chat_data.get('_') == 'Chat':
        group_id = f"-100{chat_data.get('id')}"
        group = await client.get_entity(group_id)
        sender_id = sender.id
        admins = {admin.id for admin in await client.get_participants(group, filter=ChannelParticipantsAdmins)}

        if sender_id in admins:
            print(f"Message from admin: - {event.message.text}")
            await process_channel_message(event, sender)
        elif getattr(sender, 'left', False):
            print(f"Message from admin with 'left': - {event.message.text}")
            await process_channel_message(event, sender)
        else:
            print(f"Message from user: - {event.message.text}")


async def process_channel_message(event, sender):
    message_text = event.message.text or ""
    cleaned_message_text = clean_text(message_text)
    print(f"Channel message text: {cleaned_message_text}")
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

    for keyword in ['CA', 'COMPLETED', 'WEBSITE']:
        match = re.search(rf'\b{keyword}\b:?\s*(?:\n)?\s*(.+)', message_text, re.IGNORECASE | re.DOTALL)
        if match:
            forward_text = match.group(1).strip().split()[0]
            print(f"Keyword '{keyword}' found. Text to forward: {forward_text}")
            break

    if forward_text:
        forward_to = await client.get_entity(forward_to_username)
        await client.send_message(forward_to, forward_text)
        print(f"Forwarded message from: {forward_text}")
        await asyncio.sleep(2)
    else:
        print(f"No actionable keywords found in message from {sender.id}.")




async def wait_for_buttons(entity, buttons_list, min_buttons):
    async for message in client.iter_messages(entity, limit=5):
        if hasattr(message, 'reply_markup') and message.reply_markup:
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    buttons_list.append(button.text)
            if len(buttons_list) >= min_buttons:
                return message
    return None


async def wait_for_reply_and_send_amount(entity, amount):
    async for reply_message in client.iter_messages(entity, limit=5):
        if reply_message.text and "Reply" in reply_message.text:
            await client.send_message(entity, amount, reply_to=reply_message.id)
            print(f"Sent buy amount: {amount}")
            break


@client.on(events.NewMessage(from_users=5486942816))
async def handle_message_new(event):
    if event.message.reply_markup:
        try:
            for row in event.message.reply_markup.rows:
                for button in row.buttons:
                    if button.text == "⚙ Snipe Options":
                        await event.message.click(4)
                        print(f"{button.text}")
                        break
                    elif button.text == '🎯 Snipe Now':
                        await event.message.click(5)
                        print(f"{button.text}")
                        break
                    if button.text == "❌ Snipe Disabled":
                        await event.message.click(5)
                        print(f"{button.text}")
                        await asyncio.sleep(1)
                    if button.text == "✏️ Buy Amount":
                        await event.message.click(7)
                        print(f"{button.text}")
        except AttributeError:
            pass


@client.on(events.MessageEdited(from_users=5486942816))
async def handle_message_edit(event):
    if event.message.reply_markup:
        button_clicked = False
        snipe_button = False
        for row in event.message.reply_markup.rows:
            for button in row.buttons:
                if button.text == "❌ Snipe Disabled" and not button_clicked:
                    snipe_button = True
                else:
                    if button.text == "✏️ Buy Amount" and snipe_button is True:
                        await event.message.click(5)
                        print(f"{button.text}")
                        button_clicked = True
                        break
                    else:
                        break
            if button_clicked:
                break



@client.on(events.NewMessage(from_users=5486942816))
async def handle_message_send(event):
    forward_to = await client.get_entity(forward_to_username)
    second_menu_buttons = []
    if "❌ This token has launched already." in event.message.text:
        msg_with_second_menu = await wait_for_buttons(forward_to, second_menu_buttons, 4)
        if msg_with_second_menu:
            await msg_with_second_menu.click(7)  # Click the buy button
            print(f"Clicked button: {second_menu_buttons[7]}")
            await wait_for_reply_and_send_amount(forward_to, '0.001')


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
