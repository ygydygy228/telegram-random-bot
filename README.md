# Telegram Random Member Bot

A small Telegram group bot. Members opt in with `/join`, opt out with `/leave`, and the group can pick one registered member with `/random`.

## Commands

- `/join` — add yourself to the group's participant list
- `/leave` — remove yourself
- `/random` — choose one registered participant and mention them
- `/list` — show registered participants
- `/help` — show help

The bot does not scrape the group's full member list. Each person chooses to join by using `/join`.

## Deploy on Render

1. Create a bot with Telegram's [@BotFather](https://t.me/BotFather) and copy its token.
2. In Render, create a new **Web Service** and connect this repository.
3. Render detects `render.yaml`. Set `BOT_TOKEN` to the token from BotFather.
4. After the first deploy, copy the service's public URL (for example, `https://your-service.onrender.com`) into the `APP_URL` environment variable, without a trailing slash.
5. Deploy again. The app registers its Telegram webhook automatically.
6. Add the bot to your Telegram group and grant permission to send messages.

## Important note about storage

This starter version stores the opt-in list in a local SQLite database (`members.db`). Free hosting filesystems may be temporary, so the list can be lost when the service is restarted or redeployed. For a permanent group list, attach persistent storage or connect a hosted database before relying on it.

Keep `BOT_TOKEN` private. Never put it in source code or commit it to GitHub.
