import pprint
import re
import sys

from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins

# Replace these with your own API credentials
api_id = '27417860'
api_hash = 'eeadf449a4147ecb9884c0a283e42cfd'
forward_to_username = 'TravisBills'

# Set up your Telegram client
client = TelegramClient('session_name', api_id, api_hash)
sys.stdout.reconfigure(encoding='utf-8')


# Define event handler for incoming messages
@client.on(events.NewMessage())
async def handle_new_message(event):
    # Print all available information about the event
    chat = await event.get_chat()
    chat_data = None
    try:
        chat_data = chat.to_dict()
    except:
        pass
    if hasattr(chat, 'broadcast') and chat.broadcast:
        sender = await event.get_sender()
        await process_channel_message(event, sender)

    elif hasattr(chat, 'megagroup') and chat.megagroup:
        # Get the sender information
        try:
            sender = await event.get_sender()
            sender_data = sender.to_dict()
            admins = await client.get_participants(chat, filter=ChannelParticipantsAdmins)
            admin_ids = [admin.id for admin in admins]
            if sender:
                if sender.id in admin_ids:
                    pprint.pprint(f"Message from admin 3: - {event.message.text}")
                    await process_channel_message(event, sender)
                else:
                    try:
                        if sender_data.get('left'):
                            await process_channel_message(event, sender)
                            pprint.pprint(f"Message from admin 2: - {event.message.text}")
                    except KeyError:
                        pprint.pprint(f"Message from user: - {event.message.text}")
        except AttributeError as ee:
            sender = await event.get_sender()
            pprint.pprint(f"Message from admin 1: - {event.message.text}")
            await process_channel_message(event, sender)

    elif chat_data and chat_data['_'] == 'Chat':
        # Get the sender information
        try:
            group_id = f"-100{chat_data.get('id')}"
            try:
                group = await client.get_entity(group_id)
                sender = await event.get_sender()
                sender_data = sender.to_dict()
                admins = await client.get_participants(group, filter=ChannelParticipantsAdmins)
                admin_ids = [admin.id for admin in admins]
                pprint.pprint(
                    admin_ids
                )
                if sender:
                    if sender.id in admin_ids:
                        await process_channel_message(event, sender)
                        pprint.pprint(f"Message from admin 3-1: - {event.message.text}")
                    else:
                        try:
                            if sender_data.get('left'):
                                await process_channel_message(event, sender)
                                pprint.pprint(f"Message from admin 2-1: - {event.message.text}")
                        except KeyError:
                            pprint.pprint(f"Message from user: - {event.message.text}")
            except ValueError:
                print("ID ni aniqlab bo'lmadi")

        except AttributeError as ee:
            sender = await event.get_sender()
            pprint.pprint(f"Message from admin 1-1: - {event.message.text}")
            await process_channel_message(event, sender)



async def process_channel_message(event, sender):
    message_text = event.message.text if event.message else ""
    cleaned_message_text = clean_text(message_text)
    print(f"Channel message text: {cleaned_message_text}")
    await handle_keywords_and_forward(message_text, sender)


def clean_text(text):
    # Convert Markdown bold to plain text
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    # Remove hyperlinks
    text = re.sub(r'http[s]?://\S+', '', text)
    # Remove emojis
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    # Remove Markdown links [text](url)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    # Remove any remaining Markdown formatting (*, *)
    text = re.sub(r'[\*_]{1,2}', '', text)
    return text


async def handle_keywords_and_forward(message_text, sender):
    forward_text = None
    # Handle keywords
    message_text = re.sub(r'\*\*(.*?)\*\*', lambda m: m.group(1).replace('\n', ' '), message_text, flags=re.DOTALL)
    for keyword in ['CA', 'COMPLETED', 'WEBSITE']:
        match = re.search(rf'\b{keyword}\b:?\s*(?:\n)?\s*(.+)', message_text, re.IGNORECASE | re.DOTALL)
        if match and match.group(1).strip():
            forward_text = match.group(1).strip().split()[0]
            print(f"Keyword '{keyword}' found. Text to forward: {forward_text}")
            break

    if forward_text:
        forward_to = await client.get_entity(forward_to_username)
        await client.send_message(forward_to, forward_text)
        print(f"Forwarded message from : {forward_text}")



pprint.pprint("Starting client...")
# Run the client
client.start()
client.run_until_disconnected()
