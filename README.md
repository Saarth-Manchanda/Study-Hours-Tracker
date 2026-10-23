# Study-Hours-Tracker
A Python Discord bot that tracks study hours for members of a server. It sends daily reminders, builds a leaderboard, saves data to CSV, and includes admin commands.

## Top.gg

Vote for the bot or view its listing on Top.gg:

**[Top.gg listing](YOUR_TOP_GG_LINK_HERE)**
*link coming soon

[![Top.gg](https://top.gg/api/widget/YOUR_BOT_ID.svg)](YOUR_TOP_GG_LINK_HERE)

## Features

- **Study hour tracking**: members log their study time, and totals are saved per user.
- **Daily pings**: reminders sent to the server on a daily schedule.
- **Leaderboard**: ranks members by study time.
- **CSV persistence**: study data is stored in CSV files.
- **Admin commands**: tools for server admins to manage data and settings.

## Setup

### Prerequisites

- Python 3.10 or newer
- A Discord bot token from the [Discord Developer Portal](https://discord.com/developers/applications)

### Installation

```bash
git clone https://github.com/Saarth-Manchanda/study-tracker-bot.git
cd study-tracker-bot
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
DISCORD_BOT_TOKEN=your_bot_token_here
```

### Running the bot

```bash
python bot.py
```

## Deployment

The bot is deployed on [Railway](https://railway.app/) and connected to this GitHub repository.

## Commands

<!-- Add your command list here, e.g. -->
| Command | Description |
|---------|-------------|
| `!command` | Description of what it does |

## Contributing

Issues and pull requests are welcome.

## License

<!-- Add a license, e.g. MIT -->
