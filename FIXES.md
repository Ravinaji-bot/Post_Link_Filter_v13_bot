# Fix report

## Bugs fixed
| File | Problem | Fix |
|---|---|---|
| `database/users_chats_db.py` | `get_notcopy_user()` returned an `InsertOneResult` for new users, so verification code crashed (`.get`/`[...]` on it) | returns the real document |
| `utils.py` `get_cap()` | `TEMPLATE.format(query=..., **locals())` raised `TypeError` (duplicate `query`) and `{message}` was never supplied, so IMDb result captions failed | explicit `message`, `remaining_seconds`, etc. passed instead of `**locals()` |
| `utils.py` `get_posterx()` | TMDB plot is a string; `plot[0]` returned only the first letter | handled str / list correctly |
| `utils.py` | dead, broken code block (undefined `text`) left after `get_landscape_thumb()` | removed |
| `utils.py` | `get_size()` could `IndexError` on huge values; `list_to_str()` added trailing commas; `humanbytes()` could `KeyError` | fixed |
| `plugins/route.py` | handlers returned `None` on `AttributeError` / connection reset (aiohttp 500 "missing return"); `/watch` crashed on paths with no digits; range end was not clamped per RFC 7233 | proper 404 / 499 responses, range clamped |
| `dreamxbotz/util/file_properties.py` | message without media -> `AttributeError` | raises `FIleNotFound` |
| `dreamxbotz/util/render_template.py` | every download page view re-downloaded the file from its own stream URL just to read its size | removed (Telegram already provides the size) |
| `dreamxbotz/util/custom_dl.py` | cache-cleaner task had no reference (can be garbage collected) | reference kept |
| `plugins/pmfilter.py` | sync IMDb search inside `ai_spell_check` blocked the event loop | `asyncio.to_thread` |
| `database/ia_filterdb.py` | DB-size cache was bypassed once DB > 10 MB (a `dbstats` call per saved file); `dreamxbotz_get_series` returned `[]` instead of `{}` on error | cache threshold 400 MB; returns `{}` |
| `bot.py` | startup crashed if the bot could not post to `LOG_CHANNEL` | logged as a warning |
| `info.py` | missing `API_HASH` / `BOT_TOKEN` / `DATABASE_URI` gave confusing errors later | clear early error |
| `requirements.txt` | `aiohttp` is imported directly but not listed | added |

## Security fixes
* Hard-coded **TMDB bearer token** (`Imdbposter.py`) and **ImgBB API key** (`telegraph.py`) removed -> env vars `TMDB_BEARER_TOKEN`, `IMGBB_API_KEY` (documented in `.env.example` / README). **Those two leaked keys should be revoked/rotated.**
* TLS verification was disabled for TMDB requests (`ssl=False`) -> removed.
* `/system` (server info) was available to everyone -> admins only.
* `/img` upload: file handle is closed and the temp file is always deleted.

## Things to know (not changed)
* `plugins/monkey_patch.py` patches internal Kurigram APIs; `kurigram` is unpinned in `requirements.txt`, so a future Kurigram release can break it. Pin the version that works for you.
* `fonts/Poppins-Bold.ttf` (poster watermark font) is now included in the project (Poppins is licensed under the SIL Open Font License).
* `Procfile` defines both `web` and `worker` running the same bot; only scale one of them on Heroku.

## Update: file delivery format
* Languages now come in **one quote box on one line**: `🔊 #Hindi #English #Tamil` (`get_languages_html` in `utils.py`).
* A second quote box with the **VLC Player** note is added under it for video files.
* Under every delivered file the bot replies `⚠️ Deleting in 50s, save quickly…` and edits it every 10 seconds (50, 40, 30, 20, 10), then deletes the file and the notice becomes "successfully deleted". Works for single files, fallback files and "Send All". Time is set with `FILE_DELETE_TIME` (default 50).

## Update: PM search order
* When a user searches in the bot PM: **1)** the poster-style post card (poster + title / audio / genres / quality + download links, `dreamxbotz/util/postcard.py`) comes first, **2)** the normal old result (buttons / result card) comes below it. Switch with `PM_POST_FIRST` (default `True`).
* The post card is deleted together with the old result when auto-delete runs.

## Update: post archive
* The post is deleted 3 minutes (180s) after it is sent. Exactly **30 seconds before that (at 2:30)** a copy (poster + caption + buttons) is saved to the private channel set in **`RESULT_ARCHIVE_CHANNEL`** (bot must be admin there). The deletion time never changes, even if saving fails. `POST_DATABASE_CHANNEL` was removed.
* Also applies to the post shown first in PM search (saved 30s before it is deleted with the result, when auto-delete is on).
* Code: `archive_post`, `wait_then_archive`, `archive_and_delete_post` in `dreamxbotz/util/postcard.py`.

## Update: /bulkpost for old files (2.5K videos)
* `/bulkpost scan` reads every saved file, `/bulkpost start` creates **one post per movie with ALL its qualities** (480p, 720p, 1080p, 2160p ...) and sends it, newest year first, to the private channel in **`RESULT_ARCHIVE_CHANNEL`**. The records are kept in their own `bulk_posts` collection, so the live auto-posts in `MOVIE_UPDATE_CHANNEL` are never touched. A movie is never posted twice.
* Files of one movie that differ only by a missing year (`RRR 1080p` + `RRR 2022 720p`) are merged into one post when there is exactly one matching year.
* **Bug fixed - quality was `N/A` for every file without a caption** (`get_qualities()` returned the truthy string "N/A", so the file name was never read). Old files usually have no caption, so every download line would have said "Unknown". Quality is now read from the file name first, the caption fills what is missing; names are normalised (`WEB-DL`, `BluRay`, `HEVC`, `4K`).
* Header "Quality" line shows resolutions when no source (WEB-DL/BluRay) is known; two files of the same resolution are told apart by source/language.
* `send_movie_update()` / `update_movie_message()` accept `chat_id` and `coll` (default = old behaviour) - used by /bulkpost.
* Poster: every image (portrait poster, backdrop, square, tiny, ultra-wide, PNG/RGBA) comes out exactly **2560x1440 landscape**.

## You must set these environment variables (the keys were removed from the code)
* `TMDB_API_KEY` **or** `TMDB_BEARER_TOKEN` - without one of them poster / movie lookups find nothing.
* `IMGBB_API_KEY` - only needed for the `/img` upload command.

## Extra fixes in v3
| File | Problem | Fix |
|---|---|---|
| `plugins/commands.py` (`allfiles_` delivery) | If one file of a group post had been deleted from the DB, `files_[0]` raised `IndexError` and the whole delivery stopped | missing files are skipped; "No such file" shown if none are left |
| `requirements.txt` | `aiohttp` listed twice | duplicate removed |

## /start auto-delete (v5)
* `/start` (home screen, private chat): the user's `/start` message is deleted after **3 s**, the bot's home message (photo + buttons) after **5 min**.
* Changeable via env vars `START_CMD_DELETE_TIME` (default 3) and `START_HOME_DELETE_TIME` (default 300). Deep links (`/start file_...`, verification, referral) are not affected.

## Update: only 6 qualities in every post (movies and web series)
* A post now lists **only** these qualities, in this order, each **at most once**: `480p HEVC`, `480p`, `720p HEVC`, `720p`, `1080p HEVC`, `1080p`. Applies to live auto-posts and `/bulkpost`.
* If several files fall in the same quality, one is shown: the one with more audio languages, then the bigger file. For web series this is decided per episode.
* `x265` / `H265` / `H.265` count as HEVC.
* Other qualities (360p, 2160p/4K, files with no quality in the name) are not listed. If a title has none of the six, its files are listed as they are so the post is never empty.
* Header lines (Audio / OTT / Quality) are built only from the files that are actually shown.
* Web-series links are now one file per episode (no more in-memory group links that stop working after a restart).

## Merge note (v6 + autopost)
This package = v6 + the `/autopost` upload (plugins/autopost.py, bot.py resume hook, env vars, README) on top of the newer upload (post-card, countdown delete, 6-quality posts, archive channel, VLC note) **+** the earlier fixes:
* `fonts/Poppins-Bold.ttf` included, `requirements.txt` aiohttp duplicate removed.
* `/start` auto-delete (user's `/start` 3 s, bot home 5 min).
* "No such file" guard / skip-missing-file fix in `allfiles_` delivery.
* Restart-proof `allfiles_` links (saved in MongoDB `getall_links`) re-added, because the newer upload had dropped them.

## New feature: `/autopost` (plugins/autopost.py)
* Reads all saved files (both databases), groups them like the channel auto-post does
  (`extract_media_info`), and sends every movie / series season as one collection to the
  movie channel / series channel, with a sticker after each collection.
* Files inside a collection are ordered: season pack, then episodes, then lowest quality first.
* Same caption as the bot gives to users (language boxes included), optional poster cover with
  the watermark + `1080p HEVC` / `S01E01-04` labels (one TMDB lookup per collection, not per file).
* Queue + progress in MongoDB (`autopost_queue`), stop/start/restart safe, FloodWait handled,
  duplicates and audio files skipped, clear message if the bot is not admin in a channel.
* `bot.py` starts `resume_autopost()` so a running job continues after a redeploy.
* `/autopost` review fixes: `<s>` in the help text was read as an HTML strikethrough tag, error texts are HTML-escaped, and the cover image stream is rewound before every send attempt (FloodWait retry / fallback).

## New feature: `/ccopy` (plugins/ccopy.py)
* Scans a source private channel (message ids, like `/index`), groups its videos into collections (movie / series season), keeps only the six allowed qualities (same picking rule as the posts) and copies them to a destination private channel with `copy_message` (no "Forwarded from" tag). A sticker is sent below every finished collection.
* Queue + progress in MongoDB (`ccopy_queue`), stop / restart safe, FloodWait handled, `bot.py` starts `resume_ccopy()`.
* Commands: `/ccopy from | to | sticker | test | scan | start [n] | stop | status | delay | caption on|off | retry | clear confirm`. The sticker falls back to the `/autopost` sticker if none is set for `/ccopy`.
* `/ccopy mode card`: posts ONE post card per collection (poster + the max-6-quality download links, built by the same code as the PM search card) to the destination channel, sticker below it. The picked files are indexed in the bot database so the links work. `/ccopy mode files` (default) copies the videos instead.
* `/ccopy sticker`: change the collection-end sticker any time - send `/ccopy sticker` and then any sticker (detected automatically for 2 min), or reply to a sticker with it; `/ccopy sticker show` previews the current one, `/ccopy sticker off` removes it. Falls back to the `/autopost` sticker when none is set.

## New: posting time window + `/postrange`
* `/autopost schedule 10:00 22:00` (India time, overnight allowed, `off` = any time): jobs only send inside
  the window and wait/continue by themselves outside it (`plugins/autopost.py`).
* `/postrange <from> <to> <start> <end> [delay]` (`plugins/postrange.py`): copies all posts whose number is
  between start and end into another channel. Skips deleted/service numbers, stops by itself after ~1000
  empty numbers in a row, respects the time window, saves progress in MongoDB and resumes after a restart
  (`bot.py` starts `resume_postrange()`).

## Merge note (autopost_v2 + v6 + ccopy)
* Combined: the `autopost_v2` upload (`/autopost schedule` time window, `/postrange`) with the v6 package (6-quality posts, post-card, `/ccopy`, `/start` auto-delete, fonts, restart-proof links, autopost review fixes).
* `/ccopy` now respects the same daily time window (`/autopost schedule 10:00 22:00`) for files, post cards and the sticker; `/ccopy status` shows it.
* `bot.py` starts `resume_autopost()`, `resume_ccopy()` and `resume_postrange()`.
* `/postrange` review fixes: the usage text used `<start> <end> ...` placeholders, which Telegram's HTML parser swallows (the help showed no values) - now `[start] [end] ...`; error texts are HTML-escaped.


## Group protection (`plugins/antispam.py`, settings in `info.py`)
* Bots added by users are banned; links (http/https, www., t.me, hidden/text links, link buttons), @mentions and forwarded messages from non-admins are deleted at once (also on edit). Admins, bot owners, anonymous admins, other bots and the linked channel's auto-forward are exempt; allow-list via `ANTISPAM_ALLOWED`; per-group `/antispam on|off|status`. Runs in its own handler groups (-41 / -40) before the normal plugins.
* Tested with 19 message types (links, hidden links, mentions, forwards, captions, emoji before a link, allowed items, `/cmd@bot`, e-mail style text) and the exemption / bot-ban rules.

## v7 - full code review (this package)
Checked: syntax of all 70+ .py files, undefined names, intra-project imports, `db.*` methods, un-awaited coroutines, `script.X.format()` placeholders.
| File | Problem | Fix |
|---|---|---|
| `info.py` | Default `AUTH_CHANNELS` / `AUTH_REQ_CHANNELS` = `"-100"` was turned into the fake channel id `-100`, so every `/start` and every search tried to check a channel that does not exist (error logs + extra API calls, also saved into new group settings as `fsub`) | only real channel ids (`<= -1000`) are kept; unset = empty list |
| `bot.py` | background tasks (`check_expired_premium`, `keep_alive`, `ping_server`, `resume_autopost`, `resume_ccopy`, `resume_postrange`) had no reference and could be garbage collected mid-run | kept in a set via `_spawn()` |
| `info.py` | `ULTRA_FAST_MODE` default argument was `True` while the env default is `"False"` (inconsistent) | default now `False` |

Not changed (works, only noted): `database/refer.py` uses the synchronous `pymongo` client inside async handlers (short blocking calls); `Procfile` has `web` and `worker` running the same bot, scale only one.


## v8 - separate command sets: users / admins / owner
* New env `OWNER_ID` (`info.py`, `OWNER_IDS`). Empty = first id of `ADMINS` is the owner. Owners are added to `ADMINS` automatically, so they can use admin commands too.
* Owner-only (filter changed from `ADMINS` to `OWNER_IDS`): `/system /logs /restart /maintenance /commands /broadcast /grp_broadcast /send /add_premium /remove_premium /get_premium /premium_users /add_redeem /trial_reset /leave /disable /enable /deletefiles /deleteall /clean_groups /resetallgroup /clear_junk /junk_group /delreq` and the maintenance on/off buttons.
* Help lists: `/help` (everyone, user commands only), `/admin_cmd` (admins), `/owner_cmd` (owner). `Script.py`: `USER_CMD`, `ADMIN_CMD` (no owner commands any more), `OWNER_CMD`.
* Telegram "/" menu is now per role (`dreamxbotz/util/bot_commands.py`, set at every start and by `/commands`): default scope = user commands only; group admins = + group commands; each admin / owner gets their own menu in PM (they must have started the bot once).
* A user typing an admin/owner command gets no reply at all, so nothing leaks.

## v9 - final review (static checks)
Checked: syntax of every .py file (compileall), undefined names, intra-project imports, `script.*` and `db.*` references, un-awaited coroutines, command menus vs handler filters (user / admin / owner), hard-coded secrets, env vars vs `.env.example` / `app.json`.
| File | Problem | Fix |
|---|---|---|
| `.env.example` | Inline comments after values (`ANTISPAM=True   # ...`). Docker `--env-file` and some hosts do NOT strip them, so `ANTISPAM_ALLOWED` would have become the comment text and the switches silently fell back to defaults | every comment moved to its own line |
| package | `__pycache__` folders must not be shipped | removed |

No other code errors found. Still true (not changed): `kurigram` is unpinned (pin the version that works for you), `database/refer.py` uses the sync `pymongo` client, `Procfile` has `web` and `worker` running the same bot (scale only one).

## Update: 10bit qualities in private-channel posts
* Private-channel posts (`/bulkpost` -> RESULT_ARCHIVE_CHANNEL, and `/ccopy` files + card mode) now allow **9 qualities**: the old six (480p HEVC, 480p, 720p HEVC, 720p, 1080p HEVC, 1080p) **plus 480p 10bit, 720p 10bit, 1080p 10bit**. Order: 480p HEVC, 480p, 480p 10bit, 720p ..., 1080p ....
* A file with `10bit` / `10-bit` / `10 bit` / `Hi10P` in its name or caption goes to its 10bit slot (even if it is also x265). Same pick rule: one file per quality, more audio languages then bigger size; per episode for series.
* Live channel auto-post (MOVIE_UPDATE_CHANNEL) and the PM search card are unchanged (still the six).
* `/autopost` is unchanged: it sends every file, so 10bit files already come.
* `merge_qualities()` now adds a `10bit` token to the quality string. `tenbit=True` parameter added to `build_post_caption`, `send_movie_update`, `update_movie_message`, `_pick_per_slot`, `_quality_slot`, `send_search_postcard`.
* /ccopy: run `/ccopy scan` again so the new 10bit files are picked (old queue keeps its old picks).

## Update: edit the file caption from inside the bot (no repo edit)
* New `plugins/file_caption.py`. Admin commands: `/filecaption` (show), `/setfilecaption <text>` (or reply to a message), `/resetfilecaption`.
* Placeholders: `{file_name}` `{file_size}` `{file_caption}`. Telegram formatting (bold / link / quote) is kept (saved as HTML). Invalid or >1024-char captions are rejected with a preview shown on success.
* Stored in `bot_settings` (key `file_caption_override`), so it survives restarts/redeploys. When set it overrides the group `caption` setting and `CUSTOM_FILE_CAPTION`; when empty everything works as before.
* Applied to all 4 delivery paths in `plugins/commands.py` and to autopost (`AUTOPOST_CAPTION` env still has priority there).
* Safety: `_deliver_file` never lets a long caption break delivery - if caption + language/VLC boxes exceed Telegram's 1024 limit the boxes are skipped, and if it is still too long the plain file name is used. `/setfilecaption` rejects captions over ~850 characters.

## Streaming fixes (v13)
| File | Problem | Fix |
|---|---|---|
| `dreamxbotz/util/custom_dl.py` | `yield_file` swallowed `TimeoutError`/`AttributeError` silently -> player got a truncated file with a fixed Content-Length and no log | error is logged and re-raised, `CancelledError` passes through, `work_loads` can never go negative |
| `plugins/route.py` | plain `200` responses also carried a `Content-Range` header (only valid for `206`) | sent only for range requests |
| `plugins/route.py` | message id taken from the first digits found anywhere in the path (wrong id for names like `Movie.2024`) | `_parse_path()` takes the leading id first |
| `plugins/route.py` | an extra client that is not admin in `BIN_CHANNEL` made the whole request fail with 500 | falls back to the main bot (client 0) |
| `plugins/route.py` | file with size 0/unknown produced an invalid range | returns 404 |

Checked: range/seek slicing (first/middle/last chunk, single chunk, 1 byte, exact 1 MB multiples) gives byte-identical output in 2100 random tests.
Needs a live test with your BIN_CHANNEL: open `/watch/<id>/<name>?hash=<hash>`, seek forward/back, and download with a resume-capable downloader.
