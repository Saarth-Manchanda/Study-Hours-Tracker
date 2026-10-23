import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import csv
import os
from collections import defaultdict
import pytz
import math

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
CHANNEL_ID = 1533796111352074372  # Your study-tracking channel
TIMEZONE = pytz.timezone('Asia/Kolkata')  # Delhi timezone
DAILY_TIME = time(15, 25)  # Daily ping at 3 PM

# Data storage
DATA_DIR = os.environ.get('DATA_DIR', '.')  # falls back to local dir if not set
DATA_FILE = os.path.join(DATA_DIR, 'study_hours.csv')
LEADERBOARD_FILE = os.path.join(DATA_DIR, 'monthly_leaderboard.csv')
PING_STATE_FILE = os.path.join(DATA_DIR, 'last_ping.txt')
CHANNEL_STATE_FILE = os.path.join(DATA_DIR, 'last_channel.txt')

def load_channel_id():
    if os.path.exists(CHANNEL_STATE_FILE):
        with open(CHANNEL_STATE_FILE, 'r') as f:
            content = f.read().strip()
            if content:
                return int(content)
    return None

def save_channel_id(channel_id):
    with open(CHANNEL_STATE_FILE, 'w') as f:
        f.write(str(channel_id))

def load_last_ping_id():
    if os.path.exists(PING_STATE_FILE):
        with open(PING_STATE_FILE, 'r') as f:
            content = f.read().strip()
            if content:
                return int(content)
    return None

def save_last_ping_id(message_id):
    with open(PING_STATE_FILE, 'w') as f:
        f.write(str(message_id))

# Tracks the message ID of the most recent daily ping, so only replies to
# THAT message are treated as study-hour submissions.
last_ping_message_id = None

# Initialize CSV files if they don't exist
def init_files():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'UserID', 'Username', 'Hours', 'Rank'])

    if not os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Month', 'UserID', 'Username', 'Total_Hours', 'Rank'])

def has_already_logged_today(user_id):
    """Check if this user already submitted hours today. """
    today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Date'] == today and row['UserID'] == str(user_id):
                    return True
    return False

def save_daily_data(user_id, username, hours):
    """Save daily study hours to CSV"""
    today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
    with open(DATA_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([today, user_id, username, hours, ''])

def get_today_data():
    """Get today's entries from CSV"""
    today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
    today_entries = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Date'] == today:
                    today_entries.append({
                        'user_id': row['UserID'],
                        'username': row['Username'],
                        'hours': float(row['Hours'])
                    })
    return today_entries

def calculate_daily_standings():
    """Calculate today's standings"""
    today_data = get_today_data()
    if not today_data:
        return None
    return sorted(today_data, key=lambda x: x['hours'], reverse=True)

@bot.event
async def on_ready():
    global last_ping_message_id, CHANNEL_ID
    print(f'{bot.user} has connected to Discord!')
    init_files()
    saved_channel = load_channel_id()          # ADDED
    if saved_channel:                           # ADDED
        CHANNEL_ID = saved_channel               # ADDED
    last_ping_message_id = load_last_ping_id()   # ADD THIS
    if last_ping_message_id:                      # ADD THIS
        print(f'Restored last ping message ID: {last_ping_message_id}')  # ADD THIS
    if not send_daily_ping.is_running():
        send_daily_ping.start()

@bot.command(name='set_channel')
@commands.has_permissions(administrator=True)
async def set_channel(ctx):
    """Set the channel where the bot will send pings"""
    global CHANNEL_ID
    CHANNEL_ID = ctx.channel.id
    save_channel_id(CHANNEL_ID)
    await ctx.send(f'✅ Channel set to {ctx.channel.mention}')

@bot.command(name='start_tracking')
@commands.has_permissions(administrator=True)
async def start_tracking(ctx):
    """Start the daily tracking"""
    if not send_daily_ping.is_running():
        send_daily_ping.start()
    await ctx.send('✅ Daily tracking started!')

@bot.command(name='stop_tracking')
@commands.has_permissions(administrator=True)
async def stop_tracking(ctx):
    """Stop the daily tracking"""
    send_daily_ping.stop()
    await ctx.send('⏹️ Daily tracking stopped!')

@tasks.loop(time=DAILY_TIME)
async def send_daily_ping():
    """Send daily ping at specified time"""
    global last_ping_message_id

    if CHANNEL_ID is None:
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        return

    embed = discord.Embed(
        title="📚 Daily Study Tracking",
        description="How many hours did you study YESTERDAY?\nReply with just the number (e.g., `3` or `2.5`)",
        color=discord.Color.blue(),
        timestamp=datetime.now(TIMEZONE)
    )

    # Send @everyone as the message content, with the embed attached
    sent_message = await channel.send(content="@everyone", embed=embed)

    # Remember this message so only replies to THIS ping count as submissions
    last_ping_message_id = sent_message.id
    save_last_ping_id(sent_message.id)   # ADD THIS

@bot.event
async def on_message(message):
    """Listen for study hour responses"""
    if message.author.bot:
        return

    # Only treat this as a study-hours submission if it's a reply to the
    # bot's most recent daily ping message (not just any reply to anything).
    if message.reference is not None and last_ping_message_id is not None \
            and message.reference.message_id == last_ping_message_id:
        try:
            hours = float(message.content.strip())

            if math.isnan(hours) or hours < 0 or hours > 12:
                await message.add_reaction('⚠️')
                await message.reply(
                    "That doesn't look right — enter hours between 0 and 12.",
                    mention_author=False
                )
            elif has_already_logged_today(message.author.id):
                await message.add_reaction('⚠️')
                await message.reply(
                    "You've already logged your hours for today!",
                    mention_author=False
                )
            else:
                save_daily_data(message.author.id, message.author.name, hours)
                await message.add_reaction('✅')
                await update_and_show_standings(message.channel)

        except ValueError:
            await message.add_reaction('❌')

    await bot.process_commands(message)

async def update_and_show_standings(channel):
    """Show current day's standings"""
    standings = calculate_daily_standings()
    if not standings:
        return

    embed = discord.Embed(
        title="🏆 Today's Study Standings",
        color=discord.Color.gold(),
        timestamp=datetime.now(TIMEZONE)
    )
    for idx, entry in enumerate(standings, 1):
        medal = '🥇' if idx == 1 else '🥈' if idx == 2 else '🥉' if idx == 3 else f'{idx}.'
        embed.add_field(name=f"{medal} {entry['username']}", value=f"{entry['hours']} hours", inline=False)

    await channel.send(embed=embed)

# ---------------- DELETE / CLEAR COMMANDS ----------------

async def confirm_action(ctx, title, description, color=discord.Color.red()):
    """Shared confirmation prompt. Returns True if confirmed, False otherwise."""
    embed = discord.Embed(title=title, description=description, color=color)
    msg = await ctx.send(embed=embed)
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')

    def check(reaction, user):
        return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in ['✅', '❌']

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        return str(reaction.emoji) == '✅'
    except asyncio.TimeoutError:
        await ctx.send('❌ Timeout (30 seconds). No changes made.')
        return False

@bot.command(name='clear_all')
@commands.has_permissions(administrator=True)
async def clear_all(ctx):
    """Delete ALL records — daily entries AND monthly leaderboards"""
    confirmed = await confirm_action(
        ctx,
        "⚠️ DELETE ALL RECORDS?",
        "This permanently deletes **every** daily entry and monthly leaderboard.\nThis **cannot be undone**.\n\nReact ✅ to confirm or ❌ to cancel."
    )
    if confirmed:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        if os.path.exists(LEADERBOARD_FILE):
            os.remove(LEADERBOARD_FILE)
        init_files()
        await ctx.send('🗑️ ✅ All records deleted. Both spreadsheets reset to empty.')
    else:
        await ctx.send('❌ Cancelled. No changes made.')

@bot.command(name='clear_daily')
@commands.has_permissions(administrator=True)
async def clear_daily(ctx):
    """Delete only daily records (keeps monthly leaderboards)"""
    confirmed = await confirm_action(
        ctx,
        "⚠️ Delete daily records?",
        "This deletes all daily entries but keeps monthly summaries.\n\nReact ✅ to confirm or ❌ to cancel.",
        discord.Color.orange()
    )
    if confirmed:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        with open(DATA_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'UserID', 'Username', 'Hours', 'Rank'])
        await ctx.send('🗑️ ✅ Daily records deleted. Monthly summaries kept.')
    else:
        await ctx.send('❌ Cancelled. No changes made.')

@bot.command(name='clear_monthly')
@commands.has_permissions(administrator=True)
async def clear_monthly(ctx):
    """Delete only monthly leaderboard records (keeps daily entries)"""
    confirmed = await confirm_action(
        ctx,
        "⚠️ Delete monthly records?",
        "This deletes all monthly leaderboard entries but keeps daily data.\n\nReact ✅ to confirm or ❌ to cancel.",
        discord.Color.orange()
    )
    if confirmed:
        if os.path.exists(LEADERBOARD_FILE):
            os.remove(LEADERBOARD_FILE)
        with open(LEADERBOARD_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Month', 'UserID', 'Username', 'Total_Hours', 'Rank'])
        await ctx.send('🗑️ ✅ Monthly records deleted. Daily entries kept.')
    else:
        await ctx.send('❌ Cancelled. No changes made.')

@bot.command(name='delete_user')
@commands.has_permissions(administrator=True)
async def delete_user(ctx, member: discord.Member):
    """Delete all records (daily + monthly) for one specific user"""
    confirmed = await confirm_action(
        ctx,
        f"⚠️ Delete all records for {member.display_name}?",
        f"This removes every daily and monthly entry belonging to {member.mention}.\n\nReact ✅ to confirm or ❌ to cancel.",
        discord.Color.orange()
    )
    if not confirmed:
        await ctx.send('❌ Cancelled. No changes made.')
        return

    user_id = str(member.id)

    for filepath, fieldname in [(DATA_FILE, 'UserID'), (LEADERBOARD_FILE, 'UserID')]:
        if not os.path.exists(filepath):
            continue
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = [row for row in reader if row[fieldname] != user_id]
            fieldnames = reader.fieldnames
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    await ctx.send(f'🗑️ ✅ All records for {member.mention} deleted.')

# ---------------- MONTHLY SUMMARY ----------------
@bot.command(name='alltime_summary')
@commands.has_permissions(administrator=True)
async def alltime_summary(ctx):
    """Generate and display all-time leaderboard"""
    # Read all entries across all time
    alltime_entries = {}

    if not os.path.exists(DATA_FILE):
        await ctx.send("❌ No data file found yet. Submit some study hours first!")
        return

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['UserID'] and row['Hours']:  # Skip empty rows
                    try:
                        user_id = row['UserID']
                        hours = float(row['Hours'])
                        if user_id in alltime_entries:
                            alltime_entries[user_id][1] += hours
                        else:
                            alltime_entries[user_id] = [row['Username'], hours]
                    except ValueError:
                        continue  # Skip rows with invalid hours

    if not alltime_entries:
        await ctx.send("📊 No study hours recorded yet. Start submitting to build the leaderboard!")
        return

    # Convert to list and sort
    alltime_standings = [(uid, data[0], data[1]) for uid, data in alltime_entries.items()]
    alltime_standings.sort(key=lambda x: x[2], reverse=True)
    embed = discord.Embed(
        title="🏆 All-Time Leaderboard",
        color=discord.Color.purple(),
        timestamp=datetime.now(TIMEZONE)
    )
    guild = ctx.guild
    for idx, (uid, username, hours) in enumerate(alltime_standings, 1):
        medal = '🥇' if idx == 1 else '🥈' if idx == 2 else '🥉' if idx == 3 else f'{idx}.'
        member = guild.get_member(int(uid))
        display_name = member.mention if member else username
        embed.add_field(name=f"{medal} {display_name}", value=f"**{hours:.1f}** total hours", inline=False)

    await ctx.send(embed=embed)


@bot.command(name='debug_csv')
@commands.has_permissions(administrator=True)
async def debug_csv(ctx):
    """Check what's in the CSV file"""
    if not os.path.exists(DATA_FILE):
        await ctx.send("No CSV file exists yet")
        return
    
    with open(DATA_FILE, 'r') as f:
        content = f.read()
    
    # Show first 1000 characters
    preview = content[:1000] if len(content) > 1000 else content
    await ctx.send(f"```\n{preview}\n```")
@bot.command(name='month_summary')
@commands.has_permissions(administrator=True)
async def month_summary(ctx):
    """Generate and display monthly leaderboard"""
    today = datetime.now(TIMEZONE)
    month_str = today.strftime('%Y-%m')

    month_entries = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Date'].startswith(month_str):
                    uid = row['UserID']
                    hours = float(row['Hours'])
                    if uid in month_entries:
                        month_entries[uid][1] += hours
                    else:
                        month_entries[uid] = [row['Username'], hours]

    monthly_standings = [(uid, data[0], data[1]) for uid, data in month_entries.items()]
    monthly_standings.sort(key=lambda x: x[2], reverse=True)

    existing_rows = []
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            existing_rows = [row for row in reader if not row['Month'].startswith(month_str)]

    with open(LEADERBOARD_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Month', 'UserID', 'Username', 'Total_Hours', 'Rank'])
        for row in existing_rows:
            writer.writerow([row['Month'], row['UserID'], row['Username'], row['Total_Hours'], row['Rank']])
        for idx, (uid, username, hours) in enumerate(monthly_standings, 1):
            writer.writerow([month_str, uid, username, hours, idx])
    embed = discord.Embed(
        title=f"🎖️ Monthly Leaderboard - {month_str}",
        color=discord.Color.purple(),
        timestamp=datetime.now(TIMEZONE)
    )
    guild = ctx.guild
    for idx, (uid, username, hours) in enumerate(monthly_standings, 1):
        medal = '🥇' if idx == 1 else '🥈' if idx == 2 else '🥉' if idx == 3 else f'{idx}.'
        member = guild.get_member(int(uid))
        display_name = member.mention if member else username
        embed.add_field(name=f"{medal} {display_name}", value=f"**{hours:.1f}** total hours", inline=False)

    await ctx.send(embed=embed)

if __name__ == '__main__':
    bot.run(os.environ['DISCORD_BOT_TOKEN'])
