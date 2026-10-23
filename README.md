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

!set_channel

    Description: Sets the current text channel as the designated study-tracking channel where the bot will send its daily pings and updates.

!start_tracking

    Description: Starts or restarts the background task that sends out the daily study-hours prompt at the configured time.

!stop_tracking

    Description: Stops the automated daily ping background task.

!clear_all

    Description: Permanently deletes all records from both the daily study spreadsheet and the monthly leaderboard (requires an interactive confirmation reaction).

!clear_daily

    Description: Deletes only the daily study entries while keeping the monthly leaderboard files intact (requires confirmation).

!clear_monthly

    Description: Deletes only the monthly leaderboard summaries while keeping daily study entries intact (requires confirmation).

!delete_user <@member>

    Description: Permanently removes all daily entries and monthly records belonging to a specific mentioned user (requires confirmation).

!alltime_summary

    Description: Calculates and displays a ranked all-time leaderboard showing total study hours accumulated by every participant across all dates.

!month_summary

    Description: Generates, saves, and displays the monthly leaderboard standings for the current month.

!debug_csv

    Description: Displays a raw text preview of the contents inside the daily study CSV data file for troubleshooting.

## Contributing


