import discord
from discord.ext import commands
import asyncio
import json

# --- Load Configuration ---
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    config = {
        "token": "YOUR_BOT_TOKEN_HERE",
        "owner_id": 0,  # Replace with your Discord User ID
        "dm_cooldown": 5,  # Default cooldown in seconds
        "whitelisted_users": []
    }
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    print("Created config.json. Please fill in your bot token and owner ID.")
    exit()

TOKEN = config['token']
OWNER_ID = config['owner_id']
DM_COOLDOWN = config['dm_cooldown']
WHITELISTED_USERS = set(config['whitelisted_users'])

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Helper Functions ---
async def send_dm(user: discord.User, message: str):
    """Safely sends a DM to the specified user."""
    try:
        await user.send(message)
        return True
    except (discord.Forbidden, discord.HTTPException):
        return False

# --- Events ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="Ready to DM!"))

# --- Commands ---
@bot.command(name="setowner")
async def set_owner(ctx, user_id: int):
    """Sets the bot owner (owner only)."""
    if ctx.author.id == OWNER_ID:
        global OWNER_ID
        OWNER_ID = user_id
        config['owner_id'] = OWNER_ID
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await ctx.send(f"Bot owner has been set to {user_id}.")
    else:
        await ctx.send("You are not the current owner of this bot.")

@bot.command(name="setdmcooldown")
async def set_dm_cooldown(ctx, cooldown: int):
    """Sets the cooldown between each DM in seconds (owner only)."""
    if ctx.author.id == OWNER_ID:
        global DM_COOLDOWN
        DM_COOLDOWN = cooldown
        config['dm_cooldown'] = DM_COOLDOWN
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await ctx.send(f"DM cooldown set to {cooldown} seconds.")
    else:
        await ctx.send("You do not have permission to set the DM cooldown.")

@bot.command(name="whitelist")
async def whitelist_user(ctx, user: discord.User):
    """Whitelists a user to use the massdm command (owner only)."""
    if ctx.author.id == OWNER_ID:
        if user.id not in WHITELISTED_USERS:
            WHITELISTED_USERS.add(user.id)
            config['whitelisted_users'] = list(WHITELISTED_USERS)
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            await ctx.send(f"{user.name} has been whitelisted.")
        else:
            await ctx.send(f"{user.name} is already whitelisted.")
    else:
        await ctx.send("You do not have permission to whitelist users.")

@bot.command(name="unwhitelist")
async def unwhitelist_user(ctx, user: discord.User):
    """Removes a user from the whitelist (owner only)."""
    if ctx.author.id == OWNER_ID:
        if user.id in WHITELISTED_USERS:
            WHITELISTED_USERS.remove(user.id)
            config['whitelisted_users'] = list(WHITELISTED_USERS)
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            await ctx.send(f"{user.name} has been unwhitelisted.")
        else:
            await ctx.send(f"{user.name} is not whitelisted.")
    else:
        await ctx.send("You do not have permission to unwhitelist users.")

@bot.command(name="massdm")
async def mass_dm(ctx, *, message: str):
    """Sends a direct message to all members of the server (whitelisted users only)."""
    if ctx.author.id == OWNER_ID or ctx.author.id in WHITELISTED_USERS:
        sent_count = 0
        failed_count = 0
        for member in ctx.guild.members:
            if member != bot.user:  # Don't DM the bot itself
                success = await send_dm(member, message)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                await asyncio.sleep(DM_COOLDOWN)  # Respect the cooldown
        await ctx.send(f"Successfully sent DM to {sent_count} members. Failed to send to {failed_count} members.")
    else:
        await ctx.send("You are not authorized to use this command.")

@bot.command(name="setactivity")
async def set_activity(ctx, activity_type: str, *, activity_name: str):
    """Sets the bot's activity (owner only).
    Usage: !setactivity <playing|watching|listening> <activity name>
    """
    if ctx.author.id == OWNER_ID:
        activity_type = activity_type.lower()
        if activity_type == "playing":
            activity = discord.Game(name=activity_name)
        elif activity_type == "watching":
            activity = discord.Activity(name=activity_name, type=discord.ActivityType.watching)
        elif activity_type == "listening":
            activity = discord.Activity(name=activity_name, type=discord.ActivityType.listening)
        else:
            await ctx.send("Invalid activity type. Choose from 'playing', 'watching', or 'listening'.")
            return

        await bot.change_presence(activity=activity)
        await ctx.send(f"Bot's activity has been set to {activity_type} {activity_name}.")
    else:
        await ctx.send("You do not have permission to set the bot's activity.")

if __name__ == "__main__":
    bot.run(TOKEN)
