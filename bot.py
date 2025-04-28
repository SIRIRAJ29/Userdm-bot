from telethon import TelegramClient, events, functions
import os

# --- CONFIGURATION ---
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_name = os.environ.get("SESSION_NAME", "antipm_session")

approved_users = set()
warning_count = {}

# --- BOT START ---
client = TelegramClient(session_name, api_id, api_hash)

async def get_target_user(event):
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        return reply_msg.sender_id
    else:
        args = event.text.split()
        if len(args) > 1:
            target = args[1]
            if target.isdigit():
                return int(target)
            else:
                user = await client.get_entity(target)
                return user.id
        else:
            await event.respond("Reply to a user or provide username/user_id!")
            return None

@client.on(events.NewMessage(incoming=True))
async def on_message(event):
    sender = await event.get_sender()
    sender_id = sender.id

    if event.is_private and not sender.bot:
        if sender_id in approved_users:
            return

        if sender_id not in warning_count:
            warning_count[sender_id] = 0

        warning_count[sender_id] += 1

        if warning_count[sender_id] <= 3:
            await event.respond(f"Hello! You are not approved yet.\nPlease wait until I approve you. Warning ({warning_count[sender_id]}/3)")
        else:
            await event.respond("You have sent too many messages without approval. You are now blocked.")
            await client(functions.contacts.BlockRequest(id=sender_id))
            warning_count.pop(sender_id, None)

@client.on(events.NewMessage(pattern='/approve'))
async def approve(event):
    target_id = await get_target_user(event)
    if target_id:
        approved_users.add(target_id)
        warning_count.pop(target_id, None)
        await event.respond(f"User {target_id} is now approved!")

@client.on(events.NewMessage(pattern='/disapproval'))
async def disapprove(event):
    target_id = await get_target_user(event)
    if target_id:
        approved_users.discard(target_id)
        warning_count[target_id] = 0
        await event.respond(f"User {target_id} is now disapproved!")

@client.on(events.NewMessage(pattern='/unblock'))
async def unblock(event):
    target_id = await get_target_user(event)
    if target_id:
        try:
            await client(functions.contacts.UnblockRequest(id=target_id))
            approved_users.add(target_id)
            warning_count.pop(target_id, None)
            await event.respond(f"User {target_id} has been unblocked and approved!")
        except Exception as e:
            await event.respond(f"Failed to unblock: {e}")

@client.on(events.NewMessage(pattern='/listapproved'))
async def listapproved(event):
    if not approved_users:
        await event.respond("No users are currently approved.")
    else:
        approved_list = '\n'.join([f"{user}" for user in approved_users])
        await event.respond(f"Approved users:\n{approved_list}")

@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    help_text = """
Anti-PM Bot Commands:

/approve - Approve user. (Reply karo ya @username/userid do)
/disapproval - Disapprove user. (Reply karo ya @username/userid do)
/unblock - Unblock aur auto-approve user. (Reply karo ya @username/userid do)
/listapproved - List all approved users.
/help - Show this help.

System:
- Approved users = No warning, free DM.
- Disapproved users = 3 warnings + Block.
- Unblocked users = Auto approved.
"""
    await event.respond(help_text)

print("Anti-PM Bot is Running...")
client.start()
client.run_until_disconnected()
