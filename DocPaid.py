import discord
from discord.ext import commands
from discord import ui
import docker
import sqlite3
import random
import string
import datetime
import asyncio
import logging
import psutil
import os

# ================= [ 🚀 BN-HOST CONFIGURATION ] =================
TOKEN = "YOUR_BOT_TOKEN_HERE" 
ADMIN_IDS = [1545006484574830713] 
PREFIX = "?" 

BRAND = "Bn-Host"
DEV = "Developed by Pythonboyz"
VPS_COST = 2
RAM_SPOOF = "64g" # Virtual RAM
DISK_LIMIT = "16G" # Host Disk matching

# ANSI CYBER COLORS
G = "\u001b[1;32m" # Green
R = "\u001b[1;31m" # Red
C = "\u001b[1;36m" # Cyan
Y = "\u001b[1;33m" # Yellow
W = "\u001b[1;37m" # White
B = "\u001b[1;34m" # Blue
RE = "\u001b[0m"   # Reset

logging.basicConfig(level=logging.INFO)

# ================= [ 🏦 DATABASE ] =================
class DataCore:
    def __init__(self):
        self.conn = sqlite3.connect('bn_cloud_v11.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users 
            (user_id TEXT PRIMARY KEY, coins INTEGER DEFAULT 0, invites INTEGER DEFAULT 0)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS vps 
            (vps_id TEXT PRIMARY KEY, container_id TEXT, owner_id TEXT, os TEXT, pwd TEXT)''')
        self.conn.commit()

    def get_user(self, uid):
        self.cursor.execute("SELECT coins, invites FROM users WHERE user_id = ?", (str(uid),))
        res = self.cursor.fetchone()
        if not res:
            self.cursor.execute("INSERT INTO users VALUES (?, 0, 0)", (str(uid),))
            self.conn.commit()
            return 0, 0
        return res

db = DataCore()

# ================= [ 🎮 DASHBOARD INTERFACE ] =================

class VMPanel(ui.View):
    def __init__(self, vps_id, cid, bot):
        super().__init__(timeout=None)
        self.vps_id, self.cid, self.bot = vps_id, cid, bot

    @ui.button(label="REBOOT", style=discord.ButtonStyle.blurple, emoji="🔄")
    async def reboot(self, interaction: discord.Interaction, button: ui.Button):
        try:
            container = self.bot.docker.containers.get(self.cid)
            container.restart()
            await interaction.response.send_message(f"🌀 `{self.vps_id}` Kernel Restarted.", ephemeral=True)
        except Exception as e: await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    @ui.button(label="SHUTDOWN", style=discord.ButtonStyle.danger, emoji="🔌")
    async def stop(self, interaction: discord.Interaction, button: ui.Button):
        try:
            container = self.bot.docker.containers.get(self.cid)
            container.stop()
            await interaction.response.send_message(f"🔌 `{self.vps_id}` Powered Off.", ephemeral=True)
        except Exception as e: await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

# ================= [ ⚡ GOD-LEVEL DEPLOY ENGINE ] =================

class CloudEngine(commands.Cog):
    def __init__(self, bot): self.bot = bot

    async def deploy_hacker_anim(self, interaction, vps_id, image):
        await interaction.response.defer(ephemeral=True)
        pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
        
        # --- ALAG LEVEL KA ANIMATION ---
        status = await interaction.followup.send(f"```ansi\n{R}[!] SYSTEM: INITIATING BN-HOST DEPLOYMENT PROTOCOL...{RE}\n```")
        await asyncio.sleep(1)

        frames = [
            (f"{C}Establishing Encrypted Satellite Uplink...{RE}", 15),
            (f"{Y}Bypassing KVM RAM Restrictions...{RE}", 30),
            (f"{G}RAM SPOOFED: 64.00 GB ALLOCATED{RE}", 45),
            (f"{C}Allocating 16GB High-Speed SSD Storage...{RE}", 60),
            (f"{Y}Injecting Pythonboyz Security Rootkit...{RE}", 80),
            (f"{G}VIRTUALIZATION COMPLETE. SYSTEM IS LIVE.{RE}", 100)
        ]

        for text, pct in frames:
            bar = "█" * (pct // 5) + "░" * (20 - (pct // 5))
            term = (
                f"```ansi\n"
                f"{B}╔══════════════════════════════════════════╗{RE}\n"
                f"   {G}{BRAND} NODE-PROVISIONING: {vps_id}{RE}\n"
                f"   {W}{DEV}{RE}\n"
                f"{B}╚══════════════════════════════════════════╝{RE}\n\n"
                f" {G}> {text}{RE}\n"
                f" {W}[{G}{bar}{W}] {pct}%{RE}\n"
                f"```"
            )
            await status.edit(content=term); await asyncio.sleep(1.2)

        try:
            # Docker Deployment with 64GB RAM & 16GB Disk Access
            container = self.bot.docker.containers.run(
                image, detach=True, privileged=True, mem_limit=RAM_SPOOF,
                name=f"BN_{vps_id}", hostname=f"bn-host-{vps_id.lower()}",
                command="tail -f /dev/null", restart_policy={"Name": "always"}
            )
            
            # Setup SSH & Environment
            setup = f"apt-get update && apt-get install -y openssh-server tmate && echo 'root:{pwd}' | chpasswd && service ssh start"
            container.exec_run(["/bin/bash", "-c", setup])
            
            # Charge Coins (Skip for Admins)
            if interaction.user.id not in ADMIN_IDS:
                db.cursor.execute("UPDATE users SET coins = coins - 2 WHERE user_id = ?", (str(interaction.user.id),))
            
            db.cursor.execute("INSERT INTO vps VALUES (?,?,?,?,?)", (vps_id, container.id, str(interaction.user.id), image, pwd))
            db.conn.commit()

            embed = discord.Embed(title="🛡️ INSTANCE DEPLOYED SUCCESSFULLY", color=0x00ffcc)
            embed.set_author(name=f"{BRAND} Cloud")
            embed.description = f"Instance **{vps_id}** is now broadcasting."
            embed.add_field(name="💾 RAM", value="`64 GB (Virtual)` Icon: 🧠", inline=True)
            embed.add_field(name="💿 DISK", value="`16 GB SSD` Icon: 💽", inline=True)
            embed.add_field(name="🔑 ACCESS", value=f"User: `root` \nPass: ||`{pwd}`||", inline=False)
            embed.set_footer(text=f"{DEV} | Check DMs for details.")
            
            await status.edit(content=None, embed=embed)
            await interaction.user.send(f"🎉 **Your God-Level VPS is Ready!**", embed=embed)

        except Exception as e:
            await status.edit(content=f"❌ **FATAL ERROR:** {e}")

# ================= [ 🤖 BOT SYSTEM CORE ] =================

class BnHostGod(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        self.docker = docker.from_env()
        self.invite_map = {}

    async def on_ready(self):
        for g in self.guilds: self.invite_map[g.id] = await g.invites()
        await self.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.competing, name="64GB Hyper-Nodes"))
        print(f"✅ {BRAND} v11.0 Online | {DEV}")

bot = BnHostGod()

@bot.command()
async def help(ctx):
    # HELP BOOT SEQUENCE
    m = await ctx.send(f"```ansi\n{C}[*] CONNECTING TO BN-HOST CLUSTERS...{RE}\n```")
    await asyncio.sleep(0.8)
    
    logs = [
        f"{G}[OK] Virtual Disk Bridge Linked.{RE}",
        f"{C}[*] Accessing Developed by Pythonboyz API...{RE}",
        f"{Y}[!] Initializing God-Level UI...{RE}",
        f"{G}[SUCCESS] Welcome to the Mainframe.{RE}"
    ]
    
    curr = ""
    for log in logs:
        curr += f"\n{log}"
        term = f"```ansi\n{W}--- SYSTEM BOOT ---{RE}{curr}\n```"
        await m.edit(content=term); await asyncio.sleep(0.6)

    embed = discord.Embed(title=f"👑 {BRAND} CLOUD DASHBOARD", color=0x2b2d31)
    embed.description = (
        f"**{DEV}**\n\n"
        f"• `{PREFIX}deploy` - Provision 64GB/16GB VPS\n"
        f"• `{PREFIX}balance` - Check Credits\n"
        f"• `{PREFIX}manage [ID]` - Control Panel\n"
        f"• `{PREFIX}invite` - Earn Coins"
    )
    embed.add_field(name="💰 PRICING", value="1 Invite = 1 Coin | 1 VPS = 2