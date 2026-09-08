import discord
from discord.ext import commands
from discord import ui
import asyncio, random, string, sqlite3, time, datetime, os, psutil, docker

# ================= [ 💎 CONFIGURATION ] =================
TOKEN = ""
PREFIX = "?"
ADMIN_IDS = [1545006484574830713]
DEV_TAG = "Developed by PythonBoyz"

# VPS GOD-SPECS
VPS_COST = 2
RAM_LIMIT = "64g"
CPU_CORES = 8
DISK_SPACE = "200GB"

# ANSI COLORS
C, Y, G, R, W, RE = "\u001b[0;36m", "\u001b[1;33m", "\u001b[0;32m", "\u001b[0;31m", "\u001b[0;37m", "\u001b[0m"

# ================= [ 🏦 DATABASE ] =================
class DataCore:
    def __init__(self):
        self.conn = sqlite3.connect('bnhost_ultimate.db', check_same_thread=False)
        self.cur = self.conn.cursor()
        self.cur.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, coins INT DEFAULT 0, invs INT DEFAULT 0)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS vps (v_id TEXT, c_id TEXT, owner TEXT, os TEXT, pwd TEXT)')
        self.conn.commit()

    def sync_user(self, uid):
        self.cur.execute("SELECT coins, invs FROM users WHERE id = ?", (str(uid),))
        res = self.cur.fetchone()
        if not res:
            self.cur.execute("INSERT INTO users VALUES (?, 0, 0)", (str(uid),))
            self.conn.commit()
            return 0, 0
        return res

db = DataCore()
try:
    docker_client = docker.from_env()
except:
    docker_client = None

# ================= [ 🛰️ VM MANAGER ] =================
class VMManager(ui.View):
    def __init__(self, v_id, c_id, owner):
        super().__init__(timeout=None)
        self.v_id, self.c_id, self.owner = v_id, c_id, owner

    @ui.button(label="START", style=discord.ButtonStyle.green, emoji="🚀")
    async def boot(self, interaction: discord.Interaction, btn: ui.Button):
        if str(interaction.user.id) != self.owner: return await interaction.response.send_message("❌ Not yours!", ephemeral=True)
        docker_client.containers.get(self.c_id).start()
        await interaction.response.send_message(f"✅ {self.v_id} Started!", ephemeral=True)

    @ui.button(label="STOP", style=discord.ButtonStyle.red, emoji="🛑")
    async def shutdown(self, interaction: discord.Interaction, btn: ui.Button):
        if str(interaction.user.id) != self.owner: return await interaction.response.send_message("❌ Not yours!", ephemeral=True)
        docker_client.containers.get(self.c_id).stop()
        await interaction.response.send_message(f"🛑 {self.v_id} Stopped!", ephemeral=True)

# ================= [ 🚀 DEPLOY SYSTEM ] =================
class OSSelect(ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Ubuntu 22.04", emoji="🐧", value="ubuntu:22.04"),
            discord.SelectOption(label="Debian 12", emoji="🌀", value="debian:12")
        ]
        super().__init__(placeholder="⚡ SELECT OS...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        coins, _ = db.sync_user(user_id)
        if user_id not in ADMIN_IDS and coins < VPS_COST:
            return await interaction.followup.send(f"❌ Need {VPS_COST} coins!", ephemeral=True)

        v_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

        msg = await interaction.followup.send(f"```ansi\n{C}[!] PROVISIONING 64GB NODE: {v_id}...{RE}```")
        await asyncio.sleep(2)

        try:
            container = docker_client.containers.run(
                self.values[0], detach=True, tty=True, privileged=True,
                mem_limit=RAM_LIMIT, name=f"BN_{v_id}", command="tail -f /dev/null"
            )
            setup = f"apt-get update && apt-get install -y openssh-server tmate && echo 'root:{pwd}' | chpasswd && service ssh start"
            container.exec_run(["/bin/bash", "-c", setup])
            
            db.cur.execute("INSERT INTO vps VALUES (?,?,?,?,?)", (v_id, container.id, str(user_id), self.values[0], pwd))
            db.conn.commit()

            emb = discord.Embed(title="🌌 NODE ONLINE", color=0x00ffff)
            emb.add_field(name="ID", value=f"`{v_id}`")
            emb.add_field(name="PASS", value=f"||`{pwd}`||")
            emb.set_footer(text=DEV_TAG)
            await msg.edit(content=None, embed=emb)
        except Exception as e:
            await msg.edit(content=f"❌ Error: {e}")

# ================= [ 👑 BOT CORE ] =================
class BnHostGod(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)

    async def on_ready(self):
        print(f"✅ {self.user} is ONLINE!")

bot = BnHostGod()

@bot.command()
async def deploy(ctx):
    view = ui.View(); view.add_item(OSSelect(bot))
    await ctx.send("⚙️ **VIRTUALIZATION HUB:** Select Architecture", view=view)

@bot.command()
async def balance(ctx):
    coins, invs = db.sync_user(ctx.author.id)
    bal = "∞ (GOD)" if ctx.author.id in ADMIN_IDS else str(coins)
    embed = discord.Embed(title="💳 CLOUD WALLET", color=0x00ffff)
    embed.add_field(name="Balance", value=f"```fix\n{bal}\n```")
    embed.add_field(name="💰 PRICING", value="1 Invite = 1 Coin | 1 VPS = 2 Coins")
    embed.set_footer(text=DEV_TAG)
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="💎 Bn-Host Control", description="`?deploy`, `?balance`, `?manage`, `?help`", color=0x2b2d31)
    embed.set_footer(text=DEV_TAG)
    await ctx.send(embed=embed)

@bot.command()
async def manage(ctx, v_id: str = None):
    if not v_id: return await ctx.send("❌ Usage: `?manage [ID]`")
    data = db.cur.execute("SELECT * FROM vps WHERE v_id = ?", (v_id,)).fetchone()
    if not data: return await ctx.send("❌ Not found.")
    await ctx.send(f"🛰️ **Managing {v_id}**", view=VMManager(data[0], data[1], data[2]))

# Invite tracking
invites = {}
@bot.event
async def on_member_join(member):
    global invites
    try:
        old = invites[member.guild.id]
        new = await member.guild.invites()
        invites[member.guild.id] = new
        for i in old:
            for n in new:
                if i.code == n.code and n.uses > i.uses:
                    db.cur.execute("UPDATE users SET coins = coins + 1, invs = invs + 1 WHERE id = ?", (str(i.inviter.id),))
                    db.conn.commit()
    except: pass

bot.run(TOKEN)))
                    db.conn.commit()
    except: pass

bot.run(TOKEN)