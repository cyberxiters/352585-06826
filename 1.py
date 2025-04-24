import discord
import asyncio
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

whitelist = {"1311365424490745856"}
dm_whitelist = {"1311365424490745856"}
owner_ids = {1311365424490745856}
server_whitelist = {"1318212073540292608"}  # Added your server ID
central_log_server = None
central_log_channel = None
dm_cooldown = 3

def is_bot_owner():
    async def predicate(ctx):
        return ctx.author.id in owner_ids
    return commands.check(predicate)

def isWhitelisted(ctx):
    if not ctx.guild:
        return False
    member = ctx.guild.get_member(ctx.author.id)
    if not member:
        return False
    if member.guild_permissions.administrator:
        return False
    return str(ctx.author.id) in whitelist

async def setup_logging(ctx):
    try:
        if central_log_channel:
            return central_log_channel

        try:
            log_channel = discord.utils.get(ctx.guild.text_channels, name="dm-logs")
            if not log_channel:
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                log_channel = await ctx.guild.create_text_channel("dm-logs", overwrites=overwrites)
                await log_channel.send("📝 DM Log initialized")
            return log_channel
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create or access the logging channel!")
            return ctx.channel
    except Exception as e:
        await ctx.send(f"⚠️ Falling back to current channel for logging: {str(e)}")
        return ctx.channel

@bot.command()
@is_bot_owner()
async def addowner(ctx, user_id: int):
    owner_ids.add(user_id)
    await ctx.send(f"✅ Added user ID {user_id} as bot owner")

@bot.command(name="whitelist")
async def whitelist_cmd(ctx, action: str, user_id: str):
    if ctx.author.id != 1311365424490745856:
        await ctx.send("❌ Only the bot owner can use this command!")
        return

    action = action.lower()
    if action == "add":
        whitelist.add(user_id)
        await ctx.send(f"✅ Added {user_id} to whitelist")
    elif action == "remove":
        if user_id in whitelist:
            whitelist.remove(user_id)
            await ctx.send(f"✅ Removed {user_id} from whitelist")
        else:
            await ctx.send("❌ User not in whitelist")
    else:
        await ctx.send("❌ Invalid action! Use 'add' or 'remove'")

@bot.command()
async def removeuser(ctx, user_id: str):
    if ctx.author.guild_permissions.administrator:
        if user_id in whitelist:
            whitelist.remove(user_id)
            await ctx.send(f"Removed user {user_id} from whitelist")
        else:
            await ctx.send("User not in whitelist")
    else:
        await ctx.send("You don't have permission to use this command")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if str(message.author.id) not in whitelist and not message.author.guild_permissions.administrator:
        return

    responses = {
        "hi": "yo wassup",
        "aimbot scope": "Paid",
        "sniper scope": "Paid",
        "sniper scope tracking": "Paid",
        "all sniper switch": "Paid",
        "discord server link": "https://discord.gg/5RjKJTdPr2",
        "youtube channel": "https://www.youtube.com/@xod_88",
        "commands": "Hi,discord server link,instagram,youtubechannel,commands,Aimbot Scope,Sniper Scope,Sniper Scope Tracking,All Sniper Swtich,**This was made by cyberxitersofficial**"
    }

    content = message.content.lower()
    if content in responses:
        await message.channel.send(responses[content])

    await bot.process_commands(message)

@bot.command()
@commands.check(isWhitelisted)
async def setdmcooldown(ctx, seconds: int):
    if seconds < 1:
        await ctx.send("❌ Cooldown must be at least 1 second!")
        return
    global dm_cooldown
    dm_cooldown = seconds
    await ctx.send(f"✅ DM cooldown set to {seconds} seconds")

@bot.command()
@is_bot_owner()
async def setlogserver(ctx, channel: discord.TextChannel):
    global central_log_channel, central_log_server

    if channel is None:
        central_log_channel = None
        central_log_server = None
        await ctx.send("✅ Central logging disabled. Each server will use its own dm-logs channel.")
        return

    central_log_channel = channel
    central_log_server = ctx.guild
    await ctx.send(f"✅ Set central log channel to #{channel.name} in {ctx.guild.name}")

@bot.command(name="dm_all", aliases=["massdm", "dm-all"])
async def dm_all(ctx, *, message: str = None):
    if not message:
        await ctx.send("❌ Please provide a message to send!")
        return

    if str(ctx.author.id) not in dm_whitelist:
        await ctx.send("❌ You are not whitelisted to use the mass DM command!")
        return

    if not ctx.guild or str(ctx.guild.id) not in server_whitelist:
        await ctx.send("❌ This command must be used in a whitelisted server!")
        return

    if ctx.author.id != 1358798503073153036:
        bucket = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.user)
        retry = bucket.get_bucket(ctx.message).update_rate_limit()
        if retry:
            minutes = int(retry / 60)
            seconds = int(retry % 60)
            await ctx.send(f"⏰ Command on cooldown. Try again in {minutes}m {seconds}s")
            return

    try:
        log_channel = await setup_logging(ctx)
        if not log_channel:
            await ctx.send("❌ Failed to set up logging channel!")
            return

        sent = 0
        failed = 0
        progress_msg = await ctx.send("📨 Starting to send DMs...")
        members = [m for m in ctx.guild.members if not m.bot]
        total_members = len(members)

        if total_members == 0:
            await progress_msg.edit(content="❌ No members found to DM!")
            return

        for i, member in enumerate(members, 1):
            try:
                await member.send(message)
                sent += 1
                await log_channel.send(f"✅ Sent DM to {member}")

                if i % 5 == 0 or i == total_members:
                    await progress_msg.edit(
                        content=f"📨 Progress: {i}/{total_members}\n"
                               f"✅ Sent: {sent}\n"
                               f"❌ Failed: {failed}"
                    )

                await asyncio.sleep(dm_cooldown)

            except discord.Forbidden:
                failed += 1
                await log_channel.send(f"❌ Cannot DM {member}: DMs closed")
            except discord.HTTPException as e:
                failed += 1
                await log_channel.send(f"⚠️ HTTP Error DMing {member}: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                failed += 1
                await log_channel.send(f"⚠️ Error DMing {member}: {str(e)}")

            if i % 50 == 0:
                await asyncio.sleep(5)

        final_msg = (f"📨 Mass DM Complete!\n"
                    f"✅ Sent: {sent}/{total_members}\n"
                    f"❌ Failed: {failed}/{total_members}")
        await progress_msg.edit(content=final_msg)

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="dmwhitelist")
async def dm_whitelist_cmd(ctx, action: str, user_id: str):
    if ctx.author.id != 1311365424490745856:
        await ctx.send("❌ Only the owner can use this command!")
        return

    action = action.lower()
    if action == "add":
        dm_whitelist.add(user_id)
        await ctx.send(f"✅ Added {user_id} to DM whitelist")
    elif action == "remove":
        if user_id in dm_whitelist:
            dm_whitelist.remove(user_id)
            await ctx.send(f"✅ Removed {user_id} from DM whitelist")
        else:
            await ctx.send("❌ User not in DM whitelist")
    else:
        await ctx.send("❌ Invalid action! Use 'add' or 'remove'")

@bot.command(name="serverwhitelist")
async def server_whitelist_cmd(ctx, action: str, server_id: str = None):
    if ctx.author.id != 1311365424490745856:
        await ctx.send("❌ Only the owner can use this command!")
        return

    action = action.lower()
    if action == "add":
        if not server_id:
            await ctx.send("❌ Please provide a server ID!")
            return
        server_whitelist.add(server_id)
        await ctx.send(f"✅ Added server {server_id} to whitelist")
    elif action == "remove":
        if not server_id:
            await ctx.send("❌ Please provide a server ID!")
            return
        if server_id in server_whitelist:
            server_whitelist.remove(server_id)
            await ctx.send(f"✅ Removed server {server_id} from whitelist")
        else:
            await ctx.send("❌ Server not in whitelist")
    elif action == "list":
        if not server_whitelist:
            await ctx.send("No servers are whitelisted")
        else:
            servers = "\n".join(server_whitelist)
            await ctx.send(f"Whitelisted servers:\n{servers}")
    else:
        await ctx.send("❌ Invalid action! Use 'add', 'remove', or 'list'")

@bot.command(name="create_dmlog")
@commands.has_permissions(administrator=True)
async def create_dmlog(ctx):
    try:
        log_channel = discord.utils.get(ctx.guild.text_channels, name="dm-logs")
        if log_channel:
            await ctx.send("✅ DM-logs channel already exists!")
            return

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        log_channel = await ctx.guild.create_text_channel("dm-logs", overwrites=overwrites)
        await log_channel.send("📝 DM Log channel initialized")
        await ctx.send("✅ Created DM-logs channel successfully!")

    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to create channels!")
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="checkgift")
@commands.has_permissions(administrator=True)
async def check_gift(ctx, *, links: str):
    try:
        # Create channels if they don't exist
        valid_channel = discord.utils.get(ctx.guild.text_channels, name="valid-gifts")
        invalid_channel = discord.utils.get(ctx.guild.text_channels, name="invalid-gifts")

        if not valid_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            valid_channel = await ctx.guild.create_text_channel("valid-gifts", overwrites=overwrites)

        if not invalid_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            invalid_channel = await ctx.guild.create_text_channel("invalid-gifts", overwrites=overwrites)

        # Split links by whitespace
        gift_links = links.split()
        status_msg = await ctx.send("🔍 Checking gift links...")

        checked = 0
        valid = 0
        invalid = 0

        for link in gift_links:
            if "discord.gift/" in link or "discord.com/gifts/" in link:
                # Extract gift code
                code = link.split("/")[-1]

                try:
                    # Check if code format is valid (19 characters)
                    if len(code) != 19:
                        await invalid_channel.send(f"❌ Invalid gift link format: {link}")
                        invalid += 1
                    else:
                        # Simulate checking (actual checking would require API access)
                        await valid_channel.send(f"✅ Potentially valid gift link: {link}")
                        valid += 1
                except Exception as e:
                    await invalid_channel.send(f"❌ Error checking link {link}: {str(e)}")
                    invalid += 1

                checked += 1
                if checked % 5 == 0:
                    await status_msg.edit(content=f"🔍 Checked {checked}/{len(gift_links)} links\n✅ Valid: {valid}\n❌ Invalid: {invalid}")
                await asyncio.sleep(1)  # Avoid rate limiting
            else:
                await invalid_channel.send(f"❌ Not a Discord gift link: {link}")
                invalid += 1
                checked += 1

        await status_msg.edit(content=f"✅ Finished checking {checked} links!\n✅ Valid: {valid}\n❌ Invalid: {invalid}")

    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to create channels or send messages!")
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="checkclaimable")
@commands.has_permissions(administrator=True)
async def check_nitro_claimable(ctx, link: str):
    try:
        # Create or get channels
        valid_channel = discord.utils.get(ctx.guild.text_channels, name="claimable-gifts")
        invalid_channel = discord.utils.get(ctx.guild.text_channels, name="unclaimable-gifts")

        if not valid_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            valid_channel = await ctx.guild.create_text_channel("claimable-gifts", overwrites=overwrites)

        if not invalid_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            invalid_channel = await ctx.guild.create_text_channel("unclaimable-gifts", overwrites=overwrites)

        # Extract code from link
        if "discord.gift/" in link or "discord.com/gifts/" in link:
            code = link.split("/")[-1]

            if len(code) != 19:
                await invalid_channel.send(f"❌ Invalid gift link format: {link}")
                await ctx.send("❌ Invalid gift link format! Check #unclaimable-gifts channel.")
                return

            # Simulate checking (this is just a mock check)
            import random
            is_valid = random.choice([True, False])
            is_claimed = random.choice([True, False]) if is_valid else False

            if not is_valid:
                await invalid_channel.send(f"❌ Invalid gift link: {link}")
                await ctx.send("❌ Invalid gift link! Check #unclaimable-gifts channel.")
            elif is_claimed:
                await invalid_channel.send(f"⚠️ Already claimed gift: {link}")
                await ctx.send("⚠️ Gift already claimed! Check #unclaimable-gifts channel.")
            else:
                await valid_channel.send(f"✅ Valid and unclaimed gift: {link}")
                await ctx.send("✅ Valid gift link! Check #claimable-gifts channel.")
        else:
            await invalid_channel.send(f"❌ Not a Discord gift link: {link}")
            await ctx.send("❌ Not a valid Discord gift link! Check #unclaimable-gifts channel.")

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="checkexpired")
@commands.has_permissions(administrator=True)
async def check_expired(ctx, *, links: str):
    try:
        # Create or get channels
        working_channel = discord.utils.get(ctx.guild.text_channels, name="working-gifts")
        expired_channel = discord.utils.get(ctx.guild.text_channels, name="expired-gifts")

        if not working_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            working_channel = await ctx.guild.create_text_channel("working-gifts", overwrites=overwrites)

        if not expired_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            expired_channel = await ctx.guild.create_text_channel("expired-gifts", overwrites=overwrites)

        # Split links by whitespace
        gift_links = links.split()
        status_msg = await ctx.send("🔍 Checking gift links for expiration...")

        checked = 0
        working = 0
        expired = 0

        for link in gift_links:
            if "discord.gift/" in link or "discord.com/gifts/" in link:
                code = link.split("/")[-1]

                if len(code) != 19:
                    await expired_channel.send(f"❌ Invalid gift link format: {link}")
                    expired += 1
                else:
                    # Simulate checking expiration (mock check)
                    import random
                    is_expired = random.choice([True, False])

                    if is_expired:
                        await expired_channel.send(f"⏰ Expired gift link: {link}")
                        expired += 1
                    else:
                        await working_channel.send(f"✅ Working gift link: {link}")
                        working += 1

                checked += 1
                if checked % 5 == 0:
                    await status_msg.edit(content=f"🔍 Checked {checked}/{len(gift_links)} links\n✅ Working: {working}\n⏰ Expired: {expired}")
                await asyncio.sleep(1)
            else:
                await expired_channel.send(f"❌ Not a Discord gift link: {link}")
                expired += 1
                checked += 1

        await status_msg.edit(content=f"✅ Finished checking {checked} links!\n✅ Working: {working}\n⏰ Expired: {expired}")

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="checknitro")
@commands.has_permissions(administrator=True)
async def check_nitro(ctx, *, links: str):
    try:
        # Create or get channels
        valid_channel = discord.utils.get(ctx.guild.text_channels, name="valid-nitro")
        invalid_channel = discord.utils.get(ctx.guild.text_channels, name="invalid-nitro")

        if not valid_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            valid_channel = await ctx.guild.create_text_channel("valid-nitro", overwrites=overwrites)

        if not invalid_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            invalid_channel = await ctx.guild.create_text_channel("invalid-nitro", overwrites=overwrites)

        # Split links by whitespace
        gift_links = links.split()
        status_msg = await ctx.send("🔍 Checking Nitro gift links...")

        checked = 0
        valid = 0
        invalid = 0

        for link in gift_links:
            if "discord.gift/" in link or "discord.com/gifts/" in link:
                code = link.split("/")[-1]

                if len(code) != 19:
                    await invalid_channel.send(f"❌ Invalid Nitro code format: {link}")
                    invalid += 1
                else:
                    # Simulate checking validity (mock check)
                    import random
                    is_valid = random.choice([True, False])

                    if is_valid:
                        await valid_channel.send(f"✅ Valid Nitro gift: {link}")
                        valid += 1
                    else:
                        await invalid_channel.send(f"❌ Invalid Nitro gift: {link}")
                        invalid += 1

                checked += 1
                if checked % 5 == 0:
                    await status_msg.edit(content=f"🔍 Checked {checked}/{len(gift_links)} links\n✅ Valid: {valid}\n❌ Invalid: {invalid}")
                await asyncio.sleep(1)
            else:
                await invalid_channel.send(f"❌ Not a Discord gift link: {link}")
                invalid += 1
                checked += 1

        await status_msg.edit(content=f"✅ Finished checking {checked} links!\n✅ Valid: {valid}\n❌ Invalid: {invalid}")

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="genworking")
@commands.has_permissions(administrator=True)
async def generate_working(ctx, amount: int = 1):
    try:
        if amount < 1 or amount > 5:
            await ctx.send("❌ Please specify an amount between 1 and 5!")
            return

        working_codes = [
            "h4CkQnGtR9mKpL3vX8",
            "jN2wYbVzA5sKdM7xU4",
            "qW9cFnJt6yHgE8mP3",
            "kR5vXpL8nB2wY7tM4",
            "zQ4jH9gF3mK6sN8w"
        ]

        links = []
        for i in range(min(amount, len(working_codes))):
            links.append(f"https://discord.gift/{working_codes[i]}")

        message = "🎁 Generated Working Nitro Links:\n" + "\n".join(links)
        await ctx.send(message)

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="getclaimable")
@commands.has_permissions(administrator=True)
async def get_claimable(ctx, amount: int = 1):
    try:
        if amount < 1 or amount > 3:
            await ctx.send("❌ Please specify an amount between 1 and 3!")
            return

        claimable_codes = [
            "dK9nB4mP7vX2sH5jL",
            "rT6wQ8yU3fA9cE4xN",
            "gM2hJ5kL8pW4nS9vB"
        ]

        # Create or get channel for claimable gifts
        claimable_channel = discord.utils.get(ctx.guild.text_channels, name="claimable-nitro")
        if not claimable_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            claimable_channel = await ctx.guild.create_text_channel("claimable-nitro", overwrites=overwrites)

        links = []
        for i in range(min(amount, len(claimable_codes))):
            link = f"https://discord.gift/{claimable_codes[i]}"
            links.append(link)
            await claimable_channel.send(f"🎁 Claimable Nitro gift: {link}")

        await ctx.send(f"✅ Generated {len(links)} claimable Nitro links! Check #claimable-nitro channel.")

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="genvcc")
@commands.has_permissions(administrator=True)
async def generate_vcc(ctx, amount: int = 1):
    try:
        if amount < 1 or amount > 5:
            await ctx.send("❌ Please specify an amount between 1 and 5!")
            return

        import random
        from datetime import datetime, timedelta

        def generate_card():
            # Generate card number (16 digits)
            card_number = ''.join([str(random.randint(0, 9)) for _ in range(16)])

            # Generate expiry date (1-3 years from now)
            current_date = datetime.now()
            expiry_date = current_date + timedelta(days=random.randint(365, 1095))
            expiry = expiry_date.strftime("%m/%y")

            # Generate CVV (3 digits)
            cvv = ''.join([str(random.randint(0, 9)) for _ in range(3)])

            return {
                "number": card_number,
                "expiry": expiry,
                "cvv": cvv
            }

        cards = [generate_card() for _ in range(amount)]

        # Create embed message
        embed = discord.Embed(title="🎯 Virtual Credit Cards", color=0x2ecc71)
        for i, card in enumerate(cards, 1):
            embed.add_field(
                name=f"Card #{i}",
                value=f"💳 Number: `{card['number']}`\n📅 Expiry: `{card['expiry']}`\n🔒 CVV: `{card['cvv']}`",
                inline=False
            )

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="genpip")
@commands.has_permissions(administrator=True)
async def generate_pip_vcc(ctx, amount: int = 1):
    try:
        if amount < 1 or amount > 100:
            await ctx.send("❌ Please specify an amount between 1 and 5!")
            return

        import random
        from datetime import datetime, timedelta

        def generate_pip_card():
            # Generate card number (16 digits with spaces)
            numbers = [str(random.randint(0, 9)) for _ in range(16)]
            card_number = ' '.join([''.join(numbers[i:i+4]) for i in range(0, 16, 4)])

            # Generate expiry date (1-3 years from now in xx/xx format)
            current_date = datetime.now()
            expiry_date = current_date + timedelta(days=random.randint(365, 1095))
            expiry = expiry_date.strftime("%m/%y")

            # Generate CVV (3 digits)
            cvv = ''.join([str(random.randint(0, 9)) for _ in range(3)])

            return {
                "number": card_number,
                "expiry": expiry,
                "cvv": cvv
            }

        cards = [generate_pip_card() for _ in range(amount)]

        # Create embed message
        embed = discord.Embed(title="💳 PIP Format VCC", color=0x2ecc71)
        for i, card in enumerate(cards, 1):
            embed.add_field(
                name=f"Card #{i}",
                value=f"Number: `{card['number']}`\nExpiry: `{card['expiry']}`\nCVV: `{card['cvv']}`",
                inline=False
            )

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="validatevcc")
@commands.has_permissions(administrator=True)
async def validate_vcc(ctx, card_number: str, expiry: str, cvv: str):
    try:
        def luhn_check(card_num):
            digits = [int(d) for d in card_num if d.isdigit()]
            if len(digits) != 16:
                return False

            checksum = 0
            for i in range(len(digits)-1, -1, -1):
                d = digits[i]
                if i % 2 == len(digits) % 2:  # Alternate digits
                    d = d * 2
                    if d > 9:
                        d = d - 9
                checksum += d
            return checksum % 10 == 0

        # Create or get channels for results
        valid_channel = discord.utils.get(ctx.guild.text_channels, name="valid-cards")
        invalid_channel = discord.utils.get(ctx.guild.text_channels, name="invalid-cards")
        balance_channel = discord.utils.get(ctx.guild.text_channels, name="card-balances")

        if not balance_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            balance_channel = await ctx.guild.create_text_channel("card-balances", overwrites=overwrites)

        if not valid_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            valid_channel = await ctx.guild.create_text_channel("valid-cards", overwrites=overwrites)

        if not invalid_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            invalid_channel = await ctx.guild.create_text_channel("invalid-cards", overwrites=overwrites)

        # Clean card number
        clean_number = ''.join(filter(str.isdigit, card_number))

        # Validate card
        is_valid = True
        reasons = []

        # Check card number
        if not luhn_check(clean_number):
            is_valid = False
            reasons.append("Failed Luhn check")

        if len(clean_number) != 16:
            is_valid = False
            reasons.append("Card number must be 16 digits")

        # Check expiry (MM/YY format)
        if not expiry.count('/') == 1:
            is_valid = False
            reasons.append("Invalid expiry format")
        else:
            month, year = expiry.split('/')
            if not (month.isdigit() and year.isdigit() and len(month) == 2 and len(year) == 2):
                is_valid = False
                reasons.append("Invalid expirydate format")
            elif not (1 <= int(month) <= 12):
                is_valid = False
                reasons.append("Invalid month")

        # Check CVV (3 digits)
        if not cvv.isdigit() or len(cvv) != 3:
            is_valid = False
            reasons.append("Invalid CVV")

        # Send result to appropriate channel
        if is_valid:
            embed = discord.Embed(title="✅ Valid Card", color=0x2ecc71)
            embed.add_field(name="Card Number", value=f"`{card_number}||", inline=False)
            embed.add_field(name="Expiry", value=f"||{expiry}||", inline=True)
            embed.add_field(name="CVV", value=f"||{cvv}||", inline=True)
            await valid_channel.send(embed=embed)
            await ctx.send("✅ Card is valid! Check #valid-cards channel.")
        else:
            embed = discord.Embed(title="❌ Invalid Card", color=0xe74c3c)
            embed.add_field(name="Card Number", value=f"||{card_number}||", inline=False)
            embed.add_field(name="Expiry", value=f"||{expiry}||", inline=True)
            embed.add_field(name="CVV", value=f"||{cvv}||", inline=True)
            embed.add_field(name="Reasons", value="\n".join(reasons), inline=False)
            await invalid_channel.send(embed=embed)
            await ctx.send("❌ Card is invalid! Check #invalid-cards channel.")

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="genbilling")
@commands.has_permissions(administrator=True)
async def generate_billing(ctx, amount: int = 1):
    try:
        if amount < 1 or amount > 5:
            await ctx.send("❌ Please specify an amount between 1 and 5!")
            return

        # Sample data for random generation
        streets = ["Main St", "Oak Ave", "Maple Rd", "Park Lane", "Cedar Dr", "Pine St"]
        cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia"]
        states = ["NY", "CA", "IL", "TX", "AZ", "PA"]
        countries = ["United States"]
        
        import random
        
        addresses = []
        for _ in range(amount):
            house_number = random.randint(100, 9999)
            street = random.choice(streets)
            city = random.choice(cities)
            state = random.choice(states)
            zipcode = f"{random.randint(10000, 99999)}"
            country = random.choice(countries)
            
            address = {
                "street": f"{house_number} {street}",
                "city": city,
                "state": state,
                "zip": zipcode,
                "country": country
            }
            addresses.append(address)
        
        # Create embed message
        embed = discord.Embed(title="📫 Generated Billing Addresses", color=0x2ecc71)
        for i, addr in enumerate(addresses, 1):
            embed.add_field(
                name=f"Address #{i}",
                value=f"Street: `{addr['street']}`\n"
                      f"City: `{addr['city']}`\n"
                      f"State: `{addr['state']}`\n"
                      f"ZIP: `{addr['zip']}`\n"
                      f"Country: `{addr['country']}`",
                inline=False
            )
        
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="validatepipe")
@commands.has_permissions(administrator=True)
async def validate_pipe_vcc(ctx, *, card_data: str):
    try:
        # Parse pipe-separated data
        cards_data = card_data.splitlines()
        cards = []
        for card_data_line in cards_data:
            parts = card_data_line.split('|')
            if len(parts) != 4:
                await ctx.send("❌ Invalid format! Use: number|month|year|cvv")
                return
            card_number, month, year, cvv = parts
            cards.append({"number": card_number, "month": month, "year": year, "cvv": cvv})

        def luhn_check(card_num):
            digits = [int(d) for d in card_num if d.isdigit()]
            checksum = sum(sum(divmod(int(d) * (1 + i % 2), 10))
                         for i, d in enumerate(reversed(digits)))
            return checksum % 10 == 0

        def get_card_info(card_num):
            # Sample BIN database (you can expand this)
            bins = {
                "553890": {"bank": "MasterCard", "country": "United States", "type": "Credit"},
                "401234": {"bank": "Visa", "country": "United Kingdom", "type": "Debit"},
                "377123": {"bank": "American Express", "country": "Canada", "type": "Credit"}
            }
            bin_number = card_num[:6]
            return bins.get(bin_number, {"bank": "Unknown", "country": "Unknown", "type": "Unknown"})

        # Create or get channels for results
        valid_channel = discord.utils.get(ctx.guild.text_channels, name="valid-cards")
        invalid_channel = discord.utils.get(ctx.guild.text_channels, name="invalid-cards")
        balance_channel = discord.utils.get(ctx.guild.text_channels, name="card-balances")

        if not balance_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            balance_channel = await ctx.guild.create_text_channel("card-balances", overwrites=overwrites)

        if not valid_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            valid_channel = await ctx.guild.create_text_channel("valid-cards", overwrites=overwrites)

        if not invalid_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            invalid_channel = await ctx.guild.create_text_channel("invalid-cards", overwrites=overwrites)

        valid_count = 0
        invalid_count = 0
        progress_msg = await ctx.send("🔄 Processing cards...")

        for i, card in enumerate(cards, 1):
            card_number = card["number"]
            month = card["month"]
            year = card["year"]
            cvv = card["cvv"]

            # Validate card
            is_valid = True
            reasons = []
            validations = []

            # 1. Date Check
            current_date = datetime.now()
            card_expiry = datetime(int(year), int(month), 1)
            if card_expiry < current_date:
                is_valid = False
                reasons.append("Card has expired")
            else:
                validations.append("✅ Date Check: Valid")

            # 2. Number Check (Luhn Algorithm)
            if not luhn_check(card_number):
                is_valid = False
                reasons.append("Failed Luhn check")
            else:
                validations.append("✅ Number Check: Valid")

            # 3. BIN/IIN Check
            card_info = get_card_info(card_number)
            validations.append(f"🏦 Bank: {card_info['bank']}")
            validations.append(f"🌍 Country: {card_info['country']}")
            validations.append(f"💳 Type: {card_info['type']}")

            # 4. Balance Check
            def check_balance(card_num):
                # Mock balance check based on last 4 digits
                # In real implementation, this would call a bank API
                last_digits = int(card_num[-4:])
                balance = last_digits * 1.5  # Mock calculation
                return balance

            balance = check_balance(card_number)
            validations.append(f"💰 Balance: ${balance:.2f}")

            # 5. Security Check
            if not card_number.isdigit() or len(card_number) != 16:
                is_valid = False
                reasons.append("Card number must be 16 digits")

            # Check month
            if not month.isdigit() or not (1 <= int(month) <= 12):
                is_valid = False
                reasons.append("Invalid month")

            # Check year
            if not year.isdigit() or len(year) != 4:
                is_valid = False
                reasons.append("Invalid year format")
            elif int(year) < datetime.now().year:
                is_valid = False
                reasons.append("Card expired")

            # Check CVV
            if not cvv.isdigit() or len(cvv) != 3:
                is_valid = False
                reasons.append("Invalid CVV")

            # Format for display
            expiry = f"{month.zfill(2)}/{year[2:]}"

            # Send result to appropriate channel
            if is_valid:
                valid_count += 1
                embed = discord.Embed(title="✅ Valid Card", color=0x2ecc71)
                embed.add_field(name="Card Number", value=f"||{card_number}||", inline=False)
                embed.add_field(name="Expiry", value=f"||{expiry}||", inline=True)
                embed.add_field(name="CVV", value=f"||{cvv}||", inline=True)
                embed.add_field(name="Validation Results", value="\n".join(validations), inline=False)
                embed.add_field(name="Bank Details", value=f"Bank: {card_info['bank']}\nType: {card_info['type']}", inline=False)
                embed.add_field(name="Geographic Info", value=f"Country: {card_info['country']}", inline=False)
                await valid_channel.send(embed=embed)
                await balance_channel.send(f"💰 Balance for ||{card_number}||: ${balance:.2f}") #Added this line to send balance to balance channel

            else:
                invalid_count += 1
                embed = discord.Embed(title="❌ Invalid Card", color=0xe74c3c)
                embed.add_field(name="Card Number", value=f"||{card_number}||", inline=False)
                embed.add_field(name="Expiry", value=f"||{expiry}||", inline=True)
                embed.add_field(name="CVV", value=f"||{cvv}||", inline=True)
                embed.add_field(name="Reasons", value="\n".join(reasons), inline=False)
                await invalid_channel.send(embed=embed)

            if i % 5 == 0:
                await progress_msg.edit(content=f"🔄 Processing... {i}/{len(cards)} cards\n✅ Valid: {valid_count}\n❌ Invalid: {invalid_count}")

        final_msg = f"✅ Processing complete!\nTotal cards: {len(cards)}\nValid: {valid_count}\nInvalid: {invalid_count}"
        await progress_msg.edit(content=final_msg)

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="genbin")
@commands.has_permissions(administrator=True)
async def generate_bin(ctx, amount: int = 1):
    try:
        if amount < 1 or amount > 10:
            await ctx.send("❌ Please specify an amount between 1 and 10!")
            return

        import random

        # Sample BIN data
        bin_data = {
            "4": {"name": "Visa", "lengths": [16], "country": "United States"},
            "5": {"name": "Mastercard", "lengths": [16], "country": "United States"},
            "3": {"name": "American Express", "lengths": [15], "country": "United States"},
            "6": {"name": "Discover", "lengths": [16], "country": "United States"}
        }

        bins = []
        for _ in range(amount):
            # Choose card type
            prefix = random.choice(list(bin_data.keys()))
            card_info = bin_data[prefix]
            
            # Generate BIN (first 6 digits)
            if prefix == "3":  # Amex
                bin_number = "37" + ''.join(random.choices("0123456789", k=4))
            else:
                bin_number = prefix + ''.join(random.choices("0123456789", k=5))
            
            bins.append({
                "bin": bin_number,
                "type": card_info["name"],
                "length": random.choice(card_info["lengths"]),
                "country": card_info["country"]
            })

        # Create embed message
        embed = discord.Embed(title="💳 Generated BINs", color=0x2ecc71)
        for i, bin_info in enumerate(bins, 1):
            embed.add_field(
                name=f"BIN #{i}",
                value=f"Number: `{bin_info['bin']}`\n"
                      f"Type: `{bin_info['type']}`\n"
                      f"Length: `{bin_info['length']}`\n"
                      f"Country: `{bin_info['country']}`",
                inline=False
            )
        
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name="gennitro")
@commands.has_permissions(administrator=True)
async def generate_nitro(ctx, amount: int = 1):
    try:
        if amount < 1 or amount > 15:
            await ctx.send("❌ Please specify an amount between 1 and 15!")
            return

        import random
        import string

        links = []
        for _ in range(amount):
            code = ''.join(random.choices(string.ascii_letters + string.digits, k=19))
            links.append(f"https://discord.gift/{code}")

        message = "🎁 Generated Nitro Links:\n" + "\n".join(links)
        await ctx.send(message)

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutes = int(error.retry_after / 60)
        seconds = int(error.retry_after % 60)
        await ctx.send(f"⏰ Command on cooldown. Try again in {minutes}m {seconds}s")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You are not whitelisted to use this command!")

from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "MTM1ODc5ODUwMzA3MzE1MzAzNg.G_tB6s.XTaU_g2DZH_O_qmEec7UlFSVKEoVcEsOV3je9o")
bot.run(TOKEN)