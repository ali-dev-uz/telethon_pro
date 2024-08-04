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


forward_to_username = 'MaestroSniperBot'
buy_cost = 0.001

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


@client.on(events.NewMessage(from_users=5486942816, incoming=True))
async def handle_message_new(event):
    if event.message.text in "Snipe amount set to":
        pass
    elif event.message.text in "❌ Buy":
        pass
    elif event.message.text in "⚡️Snipe activated":
        pass
    else:
        if event.message.reply_markup:
            try:
                for row in event.message.reply_markup.rows:
                    for button in row.buttons:
                        if button.text == "⚙ Snipe Options":
                            await event.message.click(4)
                            # print(f"{button.text}")
                            break
                        elif button.text in '🎯 Snipe Now':
                            await event.message.click(5)
                            # print(f"{button.text}")
                            break
            except AttributeError:
                pass


@client.on(events.MessageEdited(from_users=5486942816, incoming=True))
async def handle_message_edit(event):
    forward_to = await client.get_entity(forward_to_username)

    if event.message.text in "Snipe amount set to":
        pass
    else:
        if event.message.reply_markup:
            button_clicked = False
            snipe_button = False
            enable_on = False
            for row in event.message.reply_markup.rows:
                for button in row.buttons:
                    if button.text == "❌ Snipe Disabled" and not button_clicked:
                        snipe_button = True
                    elif button.text == "✅ Snipe Enabled" and not button_clicked:
                        snipe_button = False
                        enable_on = True
                    else:
                        if button.text == "✏️ Buy Amount" and snipe_button is True:
                            await event.message.click(5)
                            print(f"{button.text}-{buy_cost}")
                            await client.send_message(forward_to, "clicked")
                            button_clicked = True
                            await event.message.click(7)  # Click the buy button
                            # print(f"Clicked button: {second_menu_buttons[7]}")
                            await wait_for_reply_and_send_amount(forward_to, f'{buy_cost}')
                            break

                        elif button.text != f"✏️ Buy Amount: {buy_cost} SOL" and snipe_button is True:
                            await event.message.click(5)
                            await client.send_message(forward_to, "clicked")
                            print(f"{button.text}-{buy_cost}")
                            await event.message.click(7)  # Click the buy button
                            # print(f"Clicked button: {second_menu_buttons[7]}")
                            await wait_for_reply_and_send_amount(forward_to, f'{buy_cost}')
                            button_clicked = True
                            break
                        # elif button.text in "✏️ Buy Amount" and enable_on is True:
                        #     await event.message.click(7)
                        #     print(f"{button.text}-{buy_cost}")
                        #     await wait_for_reply_and_send_amount(forward_to, f'{buy_cost}')
                        #     button_clicked = True
                        #     break
                        else:
                            break
                if button_clicked:
                    break



@client.on(events.NewMessage(from_users=5486942816, pattern=r"❌ This token has launched already\."))
async def handle_message_send(event):
    forward_to = await client.get_entity(forward_to_username)
    second_menu_buttons = []
    if event.message.text in "Snipe amount set to":
        pass
    elif event.message.text in "❌ Buy":
        pass
    elif event.message.text in "⚡️Snipe activated":
        pass
    else:
        if "❌ This token has launched already." in event.message.text:
            msg_with_second_menu = await wait_for_buttons(forward_to, second_menu_buttons, 4)
            if msg_with_second_menu:
                await msg_with_second_menu.click(7)  # Click the buy button
                # print(f"Clicked button: {second_menu_buttons[7]}")
                await wait_for_reply_and_send_amount(forward_to, f'{buy_cost}')



# @client.on(events.NewMessage(outgoing=True, pattern=r"clicked"))
# async def handle_message_send_out(event):
#     forward_to = await client.get_entity(forward_to_username)
#     second_menu_buttons = []
#     logging.error(f"Start", exc_info=True)
#     print("Start")
#     if event.message.text in "Snipe amount set to":
#         pass
#     else:
#         msg_with_second_menu = await wait_for_buttons(forward_to, second_menu_buttons, 4)
#         if msg_with_second_menu:
#             await msg_with_second_menu.click(7)  # Click the buy button
#             logging.error(f"Clicked button: {second_menu_buttons[7]}", exc_info=True)
#             print(f"Clicked button: {second_menu_buttons[7]}")
#             await wait_for_reply_and_send_amount(forward_to, f'{buy_cost}')



#
# @client.on(events.NewMessage(from_users=5486942816, pattern=r"Reply to this message with your desired buy amount (in SOL) when trading is available\."))
# async def handle_message_send(event):
#     forward_to = await client.get_entity(forward_to_username)
#     if event.message.text in "Snipe amount set to":
#         pass
#     elif event.message.text in "❌ Buy":
#         pass
#     elif event.message.text in "⚡️Snipe activated":
#         pass
#     elif event.message.text in "Reply":
#         await wait_for_reply_and_send_amount(forward_to, f'{buy_cost}')
#         await client.send_message(forward_to, f'{buy_cost}', reply_to=event.message.id)
#         print(f"Sent buy amount: {buy_cost}")
#
#     else:
#         pass


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
