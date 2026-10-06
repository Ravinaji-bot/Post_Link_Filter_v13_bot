"""
Edit the caption of every delivered video/file DIRECTLY FROM THE BOT - no repo
edit, no redeploy.

Admin commands:
    /filecaption               - shows the caption currently in use
    /setfilecaption <text>     - sets a new caption (or reply to a message with it)
    /resetfilecaption          - goes back to the default (CUSTOM_FILE_CAPTION / Script.py)

Placeholders you can use in the caption:
    {file_name}     cleaned file name
    {file_size}     size, e.g. 1.4 GB
    {file_caption}  the file's original caption (may be empty)

You can type the caption with Telegram's own formatting (bold, italic, links,
quote) - it is saved as HTML. The value is stored in the existing
`bot_settings` collection, so it survives restarts and applies to:
  * files delivered in PM (single file, Send All, fallback)
  * files sent by the group settings path
  * autopost captions (unless AUTOPOST_CAPTION env is set)
"""
import html
import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from info import ADMINS, CUSTOM_FILE_CAPTION
from database.users_chats_db import db
from utils import temp

logger = logging.getLogger(__name__)

_DB_KEY = "file_caption_override"
_CACHE = {"loaded": False, "value": ""}
_SAMPLE = {"file_name": "Movie Name 2024 1080p WEB-DL", "file_size": "1.4 GB", "file_caption": "sample"}


def _bot_id():
    return temp.ME if isinstance(temp.ME, int) else getattr(temp.ME, "id", temp.ME)


async def get_file_caption(default=None):
    """Returns the admin-set caption template, or `default` when none is set."""
    if not _CACHE["loaded"]:
        try:
            _CACHE["value"] = await db.get_bot_setting(_bot_id(), _DB_KEY, "") or ""
            _CACHE["loaded"] = True
        except Exception as e:
            logger.warning(f"file caption load failed: {e}")
            return default
    return _CACHE["value"] or default


def peek_file_caption(default=None):
    """Sync version for non-async code (uses the cache; filled after first delivery / command)."""
    return _CACHE["value"] or default


async def _save(value: str):
    await db.update_bot_setting(_bot_id(), _DB_KEY, value)
    _CACHE["value"] = value
    _CACHE["loaded"] = True


@Client.on_message(filters.command("filecaption") & filters.user(ADMINS))
async def show_file_caption(bot: Client, message: Message):
    current = await get_file_caption()
    shown = current or CUSTOM_FILE_CAPTION or ""
    source = "✅ Custom (set from bot)" if current else "Default (info.py / Script.py)"
    await message.reply_text(
        f"<b>📝 File caption</b> — {source}\n\n"
        f"<code>{html.escape(shown)}</code>\n\n"
        "<b>Change:</b> <code>/setfilecaption your caption</code>\n"
        "(or reply to a message with <code>/setfilecaption</code>)\n"
        "<b>Placeholders:</b> <code>{file_name}</code> <code>{file_size}</code> <code>{file_caption}</code>\n"
        "<b>Reset:</b> <code>/resetfilecaption</code>",
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(filters.command("setfilecaption") & filters.user(ADMINS))
async def set_file_caption(bot: Client, message: Message):
    new = None
    if message.reply_to_message and (message.reply_to_message.text or message.reply_to_message.caption):
        r = message.reply_to_message
        new = (r.text.html if r.text else r.caption.html)
    elif len(message.command) > 1:
        parts = message.text.html.split(None, 1)
        new = parts[1] if len(parts) > 1 else None
    if not new or not new.strip():
        return await message.reply_text(
            "Usage: <code>/setfilecaption your caption</code>\n"
            "Example:\n<code>/setfilecaption {file_name}\n\n⚡ Join @YourChannel</code>\n\n"
            "Placeholders: <code>{file_name}</code> <code>{file_size}</code> <code>{file_caption}</code>",
            parse_mode=enums.ParseMode.HTML,
        )
    new = new.strip()
    try:
        preview = new.format(**_SAMPLE)
    except Exception as e:
        return await message.reply_text(
            f"❌ Caption invalid: <code>{type(e).__name__}: {e}</code>\n"
            "Only use <code>{file_name}</code> <code>{file_size}</code> <code>{file_caption}</code> inside { }.",
            parse_mode=enums.ParseMode.HTML,
        )
    if len(preview) > 850:   # leaves room for the language / VLC boxes added on delivery
        return await message.reply_text(
            "❌ Caption too long (max ~850 characters, because the language / VLC boxes are added under it). Please shorten it."
        )
    await _save(new)
    await message.reply_text(
        "✅ <b>File caption updated.</b> All new files will use it.\n\n<b>Preview:</b>\n\n" + preview,
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(filters.command("resetfilecaption") & filters.user(ADMINS))
async def reset_file_caption(bot: Client, message: Message):
    await _save("")
    await message.reply_text("✅ File caption reset to default.")
