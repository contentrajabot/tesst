# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import asyncio
import time
import math
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated,
    UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
)
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import API_ID, API_HASH, ERROR_MESSAGE, LOGIN_SYSTEM, STRING_SESSION, CHANNEL_ID, WAITING_TIME
from database.db import db
from TechVJ.strings import HELP_TXT
from bot import TechVJUser

# ---------------------------
# Progress Bar (20s edit)
# ---------------------------

PROGRESS_EDIT_INTERVAL = 20  # seconds


def humanbytes(size: int) -> str:
    if not size:
        return "0 B"
    power = 2 ** 10
    n = 0
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size)
    while size >= power and n < len(units) - 1:
        size /= power
        n += 1
    return f"{size:.2f} {units[n]}"


def _make_bar(percent: float) -> str:
    filled = int(percent // 10)  # 0..10
    return "█" * filled + "░" * (10 - filled)


async def _edit_progress(client: Client, chat_id: int, msg_id: int, text: str):
    try:
        await client.edit_message_text(chat_id, msg_id, text)
    except Exception:
        pass


def progress_cb(current: int, total: int, client: Client, chat_id: int, msg_id: int,
                start_time: float, status: str, state: dict):
    """
    Pyrogram progress callback (sync function).
    We schedule async message edits, throttled to once every 20 seconds.
    """
    now = time.time()
    last = state.get("last_edit", 0)

    # throttle edits
    if (now - last) < PROGRESS_EDIT_INTERVAL and current != total:
        return

    state["last_edit"] = now

    if total == 0:
        percent = 0.0
    else:
        percent = (current / total) * 100

    elapsed = now - start_time
    speed = (current / elapsed) if elapsed > 0 else 0.0
    eta = ((total - current) / speed) if speed > 0 else 0.0

    bar = _make_bar(percent)

    text = (
        f"**{status}**\n\n"
        f"`[{bar}]` **{percent:.1f}%**\n"
        f"**Done:** {humanbytes(current)} / {humanbytes(total)}\n"
        f"**Speed:** {humanbytes(int(speed))}/s\n"
        f"**ETA:** {math.ceil(eta)}s"
    )

    asyncio.get_event_loop().create_task(_edit_progress(client, chat_id, msg_id, text))


# ---------------------------
# Batch Temp
# ---------------------------
class batch_temp(object):
    IS_BATCH = {}


# start command
@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)

    buttons = [[
        InlineKeyboardButton("❣️ Developer", url="https://t.me/kingvj01")
    ], [
        InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/vj_bot_disscussion'),
        InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/vj_bots')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await client.send_message(
        chat_id=message.chat.id,
        text=f"<b>👋 Hi {message.from_user.mention}, I am Save Restricted Content Bot, I can send you restricted content by its post link.\n\nFor downloading restricted content /login first.\n\nKnow how to use bot by - /help</b>",
        reply_markup=reply_markup,
        reply_to_message_id=message.id
    )
    return


# help command
@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(
        chat_id=message.chat.id,
        text=f"{HELP_TXT}"
    )


# cancel command
@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await client.send_message(
        chat_id=message.chat.id,
        text="**Batch Successfully Cancelled.**"
    )


@Client.on_message(filters.text & filters.private)
async def save(client: Client, message: Message):
    # Joining chat
    if ("https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text) and LOGIN_SYSTEM == False:
        if TechVJUser is None:
            await client.send_message(message.chat.id, "String Session is not Set", reply_to_message_id=message.id)
            return
        try:
            try:
                await TechVJUser.join_chat(message.text)
            except Exception as e:
                await client.send_message(message.chat.id, f"Error : {e}", reply_to_message_id=message.id)
                return
            await client.send_message(message.chat.id, "Chat Joined", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            await client.send_message(message.chat.id, "Chat already Joined", reply_to_message_id=message.id)
        except InviteHashExpired:
            await client.send_message(message.chat.id, "Invalid Link", reply_to_message_id=message.id)
        return

    if "https://t.me/" in message.text:
        if batch_temp.IS_BATCH.get(message.from_user.id) == False:
            return await message.reply_text("**One Task Is Already Processing. Wait For Complete It. If You Want To Cancel This Task Then Use - /cancel**")

        datas = message.text.split("/")
        temp = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        try:
            toID = int(temp[1].strip())
        except:
            toID = fromID

        if LOGIN_SYSTEM == True:
            user_data = await db.get_session(message.from_user.id)
            if user_data is None:
                await message.reply("**For Downloading Restricted Content You Have To /login First.**")
                return
            api_id = int(await db.get_api_id(message.from_user.id))
            api_hash = await db.get_api_hash(message.from_user.id)
            try:
                acc = Client("saverestricted", session_string=user_data, api_hash=api_hash, api_id=api_id)
                await acc.connect()
            except:
                return await message.reply("**Your Login Session Expired. So /logout First Then Login Again By - /login**")
        else:
            if TechVJUser is None:
                await client.send_message(message.chat.id, f"**String Session is not Set**", reply_to_message_id=message.id)
                return
            acc = TechVJUser

        batch_temp.IS_BATCH[message.from_user.id] = False

        for msgid in range(fromID, toID + 1):
            if batch_temp.IS_BATCH.get(message.from_user.id):
                break

            # private
            if "https://t.me/c/" in message.text:
                chatid = int("-100" + datas[4])
                try:
                    await handle_private(client, acc, message, chatid, msgid)
                except Exception as e:
                    if ERROR_MESSAGE == True:
                        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

            # bot
            elif "https://t.me/b/" in message.text:
                username = datas[4]
                try:
                    await handle_private(client, acc, message, username, msgid)
                except Exception as e:
                    if ERROR_MESSAGE == True:
                        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

            # public
            else:
                username = datas[3]
                try:
                    msg = await client.get_messages(username, msgid)
                except UsernameNotOccupied:
                    await client.send_message(message.chat.id, "The username is not occupied by anyone", reply_to_message_id=message.id)
                    return

                try:
                    await client.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
                except:
                    try:
                        await handle_private(client, acc, message, username, msgid)
                    except Exception as e:
                        if ERROR_MESSAGE == True:
                            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

            # ✅ Flood wait protection (now controlled by config WAITING_TIME=25)
            await asyncio.sleep(WAITING_TIME)

        if LOGIN_SYSTEM == True:
            try:
                await acc.disconnect()
            except:
                pass

        batch_temp.IS_BATCH[message.from_user.id] = True


# handle private
async def handle_private(client: Client, acc, message: Message, chatid, msgid: int):
    msg: Message = await acc.get_messages(chatid, msgid)
    if msg.empty:
        return

    msg_type = get_message_type(msg)
    if not msg_type:
        return

    if CHANNEL_ID:
        try:
            chat = int(CHANNEL_ID)
        except:
            chat = message.chat.id
    else:
        chat = message.chat.id

    if batch_temp.IS_BATCH.get(message.from_user.id):
        return

    if "Text" == msg_type:
        try:
            await client.send_message(
                chat, msg.text,
                entities=msg.entities,
                reply_to_message_id=message.id,
                parse_mode=enums.ParseMode.HTML
            )
            return
        except Exception as e:
            if ERROR_MESSAGE == True:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            return

    # ✅ One status message for both download + upload
    smsg = await client.send_message(message.chat.id, "**Starting...**", reply_to_message_id=message.id)

    # -------------------
    # DOWNLOAD with bar
    # -------------------
    d_state = {"last_edit": 0}
    d_start = time.time()

    try:
        file_path = await acc.download_media(
            msg,
            progress=progress_cb,
            progress_args=(client, message.chat.id, smsg.id, d_start, "📥 Downloading", d_state)
        )
        # final download update
        await smsg.edit_text("✅ Download completed. Now uploading...")
    except Exception as e:
        if ERROR_MESSAGE == True:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        try:
            await smsg.delete()
        except:
            pass
        return

    if batch_temp.IS_BATCH.get(message.from_user.id):
        return

    # caption
    caption = msg.caption if msg.caption else None

    # -------------------
    # UPLOAD with bar
    # -------------------
    u_state = {"last_edit": 0}
    u_start = time.time()

    try:
        if "Document" == msg_type:
            try:
                ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
            except:
                ph_path = None

            await client.send_document(
                chat,
                file_path,
                thumb=ph_path,
                caption=caption,
                reply_to_message_id=message.id,
                parse_mode=enums.ParseMode.HTML,
                progress=progress_cb,
                progress_args=(client, message.chat.id, smsg.id, u_start, "📤 Uploading", u_state)
            )
            if ph_path is not None and os.path.exists(ph_path):
                os.remove(ph_path)

        elif "Video" == msg_type:
            try:
                ph_path = await acc.download_media(msg.video.thumbs[0].file_id)
            except:
                ph_path = None

            await client.send_video(
                chat,
                file_path,
                duration=msg.video.duration,
                width=msg.video.width,
                height=msg.video.height,
                thumb=ph_path,
                caption=caption,
                reply_to_message_id=message.id,
                parse_mode=enums.ParseMode.HTML,
                progress=progress_cb,
                progress_args=(client, message.chat.id, smsg.id, u_start, "📤 Uploading", u_state)
            )
            if ph_path is not None and os.path.exists(ph_path):
                os.remove(ph_path)

        elif "Animation" == msg_type:
            await client.send_animation(chat, file_path, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

        elif "Sticker" == msg_type:
            await client.send_sticker(chat, file_path, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

        elif "Voice" == msg_type:
            await client.send_voice(
                chat,
                file_path,
                caption=caption,
                caption_entities=msg.caption_entities,
                reply_to_message_id=message.id,
                parse_mode=enums.ParseMode.HTML,
                progress=progress_cb,
                progress_args=(client, message.chat.id, smsg.id, u_start, "📤 Uploading", u_state)
            )

        elif "Audio" == msg_type:
            try:
                ph_path = await acc.download_media(msg.audio.thumbs[0].file_id)
            except:
                ph_path = None

            await client.send_audio(
                chat,
                file_path,
                thumb=ph_path,
                caption=caption,
                reply_to_message_id=message.id,
                parse_mode=enums.ParseMode.HTML,
                progress=progress_cb,
                progress_args=(client, message.chat.id, smsg.id, u_start, "📤 Uploading", u_state)
            )
            if ph_path is not None and os.path.exists(ph_path):
                os.remove(ph_path)

        elif "Photo" == msg_type:
            await client.send_photo(chat, file_path, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

        await smsg.edit_text("✅ Upload completed!")
    except Exception as e:
        if ERROR_MESSAGE == True:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

    # cleanup
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass

    try:
    await asyncio.sleep(5)  # user can read final msg
    await client.delete_messages(message.chat.id, [smsg.id])
    except:pass


 
# get the type of message
def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    try:
        msg.document.file_id
        return "Document"
    except:
        pass

    try:
        msg.video.file_id
        return "Video"
    except:
        pass

    try:
        msg.animation.file_id
        return "Animation"
    except:
        pass

    try:
        msg.sticker.file_id
        return "Sticker"
    except:
        pass

    try:
        msg.voice.file_id
        return "Voice"
    except:
        pass

    try:
        msg.audio.file_id
        return "Audio"
    except:
        pass

    try:
        msg.photo.file_id
        return "Photo"
    except:
        pass

    try:
        msg.text
        return "Text"
    except:
        pass
