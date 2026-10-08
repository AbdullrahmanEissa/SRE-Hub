import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from aiohttp import web
import asyncio
import json
import random
import time
import traceback

# 1. إعداد نظام تتبع الأحداث (Logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DiscordBuilder')

# 2. تحميل المتغيرات البيئية
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    logger.error("Critical: DISCORD_TOKEN not found in .env file.")
    exit(1)

# 3. إعداد الصلاحيات (Intents)
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ==========================================
# كود سيرفر الويب الوهمي لمنع Render من إيقاف البوت
# ==========================================
async def handle(request):
    return web.Response(text="SRE Bot is running 24/7!")

app = web.Application()
app.router.add_get('/', handle)

async def start_web_server():
    try:
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 10000)
        await site.start()
        logger.info("Dummy web server started on port 10000")
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
# ==========================================

# ==========================================
# نظام المستويات ونقاط الخبرة (Leveling & XP System)
# ==========================================
DATA_FILE = "users_xp.json"
COOLDOWNS = {} # ذاكرة مؤقتة لمنع السبام

LEVEL_REWARDS = {
    10: "🔥・Veteran Driver",
    20: "🏆・Track Legend"
}

def load_xp_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading XP data: {e}")
            return {}
    return {}

def save_xp_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving XP data: {e}")

def get_level(xp):
    return int(0.1 * (xp ** 0.5))
# ==========================================

# 4. هيكل البيانات (Configuration Structure)
ROLES_CONFIG = [
    {"name": "👑・Pit Boss", "color": discord.Color.red(), "hoist": True, "permissions": discord.Permissions(administrator=True)},
    {"name": "🚨・Race Steward", "color": discord.Color.orange(), "hoist": True, "permissions": discord.Permissions(manage_messages=True, kick_members=True)},
    {"name": "🔴・Content Creator", "color": discord.Color.purple(), "hoist": True, "permissions": discord.Permissions.none()},
    {"name": "🏆・Track Legend", "color": discord.Color.gold(), "hoist": True, "permissions": discord.Permissions.none()},
    {"name": "🔥・Veteran Driver", "color": discord.Color.dark_orange(), "hoist": True, "permissions": discord.Permissions.none()},
    {"name": "🏁・Sim Racer", "color": discord.Color.dark_blue(), "hoist": True, "permissions": discord.Permissions.none()},
    {"name": "🌵・Horizon Driver", "color": discord.Color.gold(), "hoist": True, "permissions": discord.Permissions.none()},
    {"name": "🏎️・LMU Pilot", "color": discord.Color.light_grey(), "hoist": True, "permissions": discord.Permissions.none()},
    {"name": "🛞・Wheel User", "color": discord.Color.green(), "hoist": True, "permissions": discord.Permissions.none()},
    {"name": "🕹️・Controller User", "color": discord.Color.teal(), "hoist": True, "permissions": discord.Permissions.none()}
]

CHANNELS_CONFIG = {
    "🏁 | STARTING GRID": [
        {"name": "📜・rules", "type": "text"},
        {"name": "📢・announcements", "type": "text"},
        {"name": "🏷️・get-roles", "type": "text"}
    ],
    "🏎️ | THE PADDOCK": [
        {"name": "💬・general-chat", "type": "text"},
        {"name": "📸・media-clips", "type": "text"},
        {"name": "🔧・irl-cars", "type": "text"},
        {"name": "🔴・live-streams", "type": "text"}
    ],
    "🛞 | ASSETTO CORSA": [
        {"name": "🚥・ac-general", "type": "text"},
        {"name": "📁・mods-and-wdt", "type": "text"},
        {"name": "🌐・servers-ip", "type": "text"},
        {"name": "⏱️・lap-times", "type": "text"}
    ],
    "🌵 | FORZA HORIZON": [
        {"name": "🏜️・fh-general", "type": "text"},
        {"name": "⚙️・car-tunes", "type": "text"},
        {"name": "🚗・convoys-lfg", "type": "text"}
    ],
    "⏱️ | LE MANS ULTIMATE": [
        {"name": "🏁・lmu-general", "type": "text"},
        {"name": "⚙️・lmu-setups", "type": "text"}
    ],
    "🏆 | COMPETITIVE RACING": [
        {"name": "📢・league-news", "type": "text"},
        {"name": "🏆・standings", "type": "text"},
        {"name": "💬・league-chat", "type": "text"},
        {"name": "🚨・stewards-office", "type": "text"}
    ],
    "🕹️ | THE GARAGE": [
        {"name": "⚙️・wheel-settings", "type": "text"},
        {"name": "💻・pc-setups", "type": "text"}
    ],
    "🎙️ | PIT LANE": [
        {"name": "🔊 | Paddock Lounge", "type": "voice"},
        {"name": "🚗 | AC Drift Matsuri", "type": "voice"},
        {"name": "🌵 | FH Convoy", "type": "voice"},
        {"name": "🏎️ | LMU Grid", "type": "voice"},
        {"name": "🏆 | Race Control", "type": "voice"},
        {"name": "🔴 | Streaming...", "type": "voice"}
    ]
}

EMOJI_TO_ROLE = {
    "🏁": "🏁・Sim Racer",
    "🌵": "🌵・Horizon Driver",
    "🏎️": "🏎️・LMU Pilot",
    "🛞": "🛞・Wheel User",
    "🕹️": "🕹️・Controller User"
}

# ----------------- صائد الأخطاء الشامل (Global Error Handler) -----------------
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # تجاهل الأوامر غير الموجودة بصمت لتجنب إزعاج الشات
        pass
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **عذراً، لا تمتلك الصلاحيات الإدارية الكافية لاستخدام هذا الأمر.**")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ **يبدو أنك نسيت كتابة بعض البيانات المطلوبة مع الأمر.**")
    else:
        logger.error(f"Unhandled Command Error: {error}")
        traceback.print_exception(type(error), error, error.__traceback__)
        await ctx.send("⚠️ **حدث خطأ داخلي أثناء تنفيذ الأمر. تم تسجيل الخطأ في السجلات لمراجعته.**")

# ----------------- الأحداث الأساسية (Events) -----------------
@bot.event
async def on_ready():
    bot.loop.create_task(start_web_server())
    logger.info(f'System Online: Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info('Awaiting deployment commands...')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    try:
        user_id = str(message.author.id)
        current_time = time.time()
        
        if user_id not in COOLDOWNS or (current_time - COOLDOWNS[user_id]) > 60:
            xp_data = load_xp_data()
            
            old_xp = xp_data.get(user_id, 0)
            old_level = get_level(old_xp)
            
            earned_xp = random.randint(15, 25)
            new_xp = old_xp + earned_xp
            new_level = get_level(new_xp)
            
            xp_data[user_id] = new_xp
            save_xp_data(xp_data)
            COOLDOWNS[user_id] = current_time

            if new_level > old_level:
                await message.channel.send(f"🎉 عاش يا {message.author.mention}! وصلت للمستوى **{new_level}** 🏎️💨")
                
                if new_level in LEVEL_REWARDS:
                    role_name = LEVEL_REWARDS[new_level]
                    role = discord.utils.get(message.guild.roles, name=role_name)
                    if role:
                        await message.author.add_roles(role)
                        await message.channel.send(f"🏆 مبروك! تم ترقيتك لرتبة **{role.name}**")
    except Exception as e:
        logger.error(f"Error in on_message XP handling: {e}")

    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
        
    try:
        guild = bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        
        if channel and channel.name == "🏷️・get-roles":
            role_name = EMOJI_TO_ROLE.get(str(payload.emoji))
            if role_name:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
                    if member:
                        await member.add_roles(role)
                        logger.info(f"Assigned {role_name} to {member.display_name}")
    except Exception as e:
        logger.error(f"Error in reaction_add: {e}")

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return
        
    try:
        guild = bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        
        if channel and channel.name == "🏷️・get-roles":
            role_name = EMOJI_TO_ROLE.get(str(payload.emoji))
            if role_name:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
                    if member:
                        await member.remove_roles(role)
                        logger.info(f"Removed {role_name} from {member.display_name}")
    except Exception as e:
        logger.error(f"Error in reaction_remove: {e}")

@bot.event
async def on_member_join(member):
    try:
        general_channel = discord.utils.get(member.guild.text_channels, name="💬・general-chat")
        roles_channel = discord.utils.get(member.guild.text_channels, name="🏷️・get-roles")
        rules_channel = discord.utils.get(member.guild.text_channels, name="📜・rules")
        
        roles_mention = roles_channel.mention if roles_channel else "🏷️・get-roles"
        rules_mention = rules_channel.mention if rules_channel else "📜・rules"
        
        if general_channel:
            embed = discord.Embed(
                title="🏎️ متسابق جديد وصل الـ Paddock!",
                description=(
                    f"أهلاً بك يا {member.mention} في سيرفر **Sim Racing Egypt Hub**!\n\n"
                    f"**خطوتك الأولى قبل الانطلاق:**\n"
                    f"📍 توجه إلى روم {roles_mention} لاختيار ألعابك وأداة التحكم الخاصة بك.\n"
                    f"📍 ألقِ نظرة سريعة على {rules_mention}.\n\n"
                    f"جاهزين لنرى أرقامك على التراك! 🚦"
                ),
                color=discord.Color.red()
            )
            
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            else:
                embed.set_thumbnail(url=member.default_avatar.url)
                
            await general_channel.send(embed=embed)
            logger.info(f"Welcomed new member: {member.display_name}")
    except Exception as e:
        logger.error(f"Error in on_member_join: {e}")

# ----------------- الأوامر (Commands) -----------------
@bot.command(name='rank')
async def check_rank(ctx):
    try:
        user_id = str(ctx.author.id)
        xp_data = load_xp_data()
        
        current_xp = xp_data.get(user_id, 0)
        current_level = get_level(current_xp)
        
        next_level = current_level + 1
        xp_needed_for_next = (next_level / 0.1) ** 2
        xp_remaining = int(xp_needed_for_next - current_xp)
        
        embed = discord.Embed(title=f"📊 إحصائيات المتسابق: {ctx.author.display_name}", color=discord.Color.blue())
        embed.add_field(name="المستوى الحالي", value=f"**{current_level}** 🏅", inline=True)
        embed.add_field(name="نقاط الخبرة (XP)", value=f"**{current_xp}** ⚡", inline=True)
        embed.add_field(name="للوصول للمستوى القادم", value=f"تحتاج **{xp_remaining}** نقطة", inline=False)
        
        if ctx.author.avatar:
            embed.set_thumbnail(url=ctx.author.avatar.url)
            
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Error in rank command: {e}")
        await ctx.send("⚠️ **حدث خطأ أثناء جلب بيانات المستويات.**")

@bot.command(name='build_hub')
@commands.has_permissions(administrator=True)
async def build_server(ctx):
    guild = ctx.guild
    await ctx.send("🚀 **بدأ تشغيل سكريبت البناء (Deployment Script)... الرجاء الانتظار.**")
    logger.info(f"Initiating server build for guild: {guild.name}")

    try:
        await ctx.send("⚙️ **جاري بناء هيكل الرتب والصلاحيات...**")
        for role_data in reversed(ROLES_CONFIG): 
            if not discord.utils.get(guild.roles, name=role_data["name"]):
                await guild.create_role(
                    name=role_data["name"],
                    color=role_data["color"],
                    hoist=role_data["hoist"],
                    permissions=role_data["permissions"],
                    reason="Automated Server Architecture Setup"
                )
                logger.info(f'Created Role: {role_data["name"]}')

        await ctx.send("📂 **جاري هندسة الأقسام والقنوات...**")
        for cat_name, channels in CHANNELS_CONFIG.items():
            category = discord.utils.get(guild.categories, name=cat_name)
            if not category:
                category = await guild.create_category(name=cat_name, reason="Automated Server Architecture Setup")
                logger.info(f'Created Category: {cat_name}')

            for ch in channels:
                if ch["type"] == "text":
                    if not discord.utils.get(guild.text_channels, name=ch["name"]):
                        await guild.create_text_channel(name=ch["name"], category=category)
                elif ch["type"] == "voice":
                    if not discord.utils.get(guild.voice_channels, name=ch["name"]):
                        await guild.create_voice_channel(name=ch["name"], category=category)

        await ctx.send("✅ **تم الانتهاء من هندسة السيرفر بنجاح!** الهيكل بالكامل يعمل الآن.")
        logger.info("Deployment completed successfully.")
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        await ctx.send(f"❌ **حدث خطأ أثناء التنفيذ:** `{e}`")

@bot.command(name='send_roles')
@commands.has_permissions(administrator=True)
async def send_roles_message(ctx):
    try:
        channel = discord.utils.get(ctx.guild.text_channels, name="🏷️・get-roles")
        if not channel:
            await ctx.send("❌ لم أتمكن من العثور على قناة `🏷️・get-roles`.")
            return

        embed = discord.Embed(
            title="🏁 مرحباً بك في Paddock الخاص بـ Sim Racing Egypt Hub!",
            description=(
                "عشان نقدر نتعرف عليك أكتر ونخصص تجربتك، يرجى اختيار الألعاب وأدوات التحكم من الإيموجيز تحت:\n\n"
                "**🎮 الألعاب المفضلة:**\n"
                "🏁 ➔ Assetto Corsa (Sim Racer)\n"
                "🌵 ➔ Forza Horizon (Horizon Driver)\n"
                "🏎️ ➔ Le Mans Ultimate (LMU Pilot)\n\n"
                "**⚙️ أداة التحكم:**\n"
                "🛞 ➔ بيلعب بدركسون (Wheel User)\n"
                "🕹️ ➔ بيلعب بدراع (Controller User)"
            ),
            color=discord.Color.red()
        )
        embed.set_footer(text="اضغط على الإيموجي للحصول على الرتبة، واضغط مرة أخرى لإزالتها.")
        
        msg = await channel.send(embed=embed)
        for emoji in EMOJI_TO_ROLE.keys():
            await msg.add_reaction(emoji)
            
        await ctx.send(f"✅ تم إرسال رسالة الرتب بنجاح في {channel.mention}")
        logger.info("Roles message sent successfully.")
    except Exception as e:
        logger.error(f"Error in send_roles command: {e}")

@bot.command(name='send_rules')
@commands.has_permissions(administrator=True)
async def send_rules_message(ctx):
    try:
        channel = discord.utils.get(ctx.guild.text_channels, name="📜・rules")
        if not channel:
            await ctx.send("❌ لم أتمكن من العثور على قناة `📜・rules`.")
            return

        embed = discord.Embed(
            title="📜 قوانين وإرشادات Sim Racing Egypt Hub",
            description=(
                "مرحباً بك في مجتمعنا! يرجى قراءة القواعد والالتزام بها لضمان بيئة تنافسية وممتعة للجميع:\n\n"
                "**⚠️ القواعد الأساسية:**\n"
                "1️⃣ **الاحترام المتبادل:** يمنع منعاً باتاً الإساءة أو التجاوز في حق أي عضو.\n"
                "2️⃣ **الروح الرياضية:** الالتزام التام بقواعد السباقات النظيفة (Clean Racing) وتقبل قرارات الحكام.\n"
                "3️⃣ **التنظيم:** يرجى استخدام كل روم للغرض المخصص لها لتسهيل التواصل.\n"
                "4️⃣ **الروابط:** يمنع نشر إعلانات أو روابط ديسكورد أخرى بدون إذن مسبق من الإدارة.\n\n"
                "**🤖 أوامر البوت المتاحة للأعضاء:**\n"
                "`!rank` ➔ استخدم هذا الأمر في الشات العام لمعرفة مستواك، نقاط خبرتك (XP)، وكم يتبقى لك للترقية للمستوى القادم."
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text="👑 إدارة السيرفر تتمنى لكم سباقات ممتعة!")
        
        await channel.send(embed=embed)
        await ctx.send(f"✅ تم إرسال رسالة القوانين بنجاح في {channel.mention}")
        logger.info("Rules message sent successfully.")
    except Exception as e:
        logger.error(f"Error in send_rules command: {e}")

@bot.command(name='test_welcome')
@commands.has_permissions(administrator=True)
async def simulate_welcome(ctx):
    try:
        member = ctx.author
        roles_channel = discord.utils.get(ctx.guild.text_channels, name="🏷️・get-roles")
        rules_channel = discord.utils.get(ctx.guild.text_channels, name="📜・rules")
        
        roles_mention = roles_channel.mention if roles_channel else "🏷️・get-roles"
        rules_mention = rules_channel.mention if rules_channel else "📜・rules"
        
        embed = discord.Embed(
            title="🏎️ متسابق جديد وصل الـ Paddock!",
            description=(
                f"أهلاً بك يا {member.mention} في سيرفر **Sim Racing Egypt Hub**!\n\n"
                f"**خطوتك الأولى قبل الانطلاق:**\n"
                f"📍 توجه إلى روم {roles_mention} لاختيار ألعابك وأداة التحكم الخاصة بك.\n"
                f"📍 ألقِ نظرة سريعة على {rules_mention}.\n\n"
                f"جاهزين لنرى أرقامك على التراك! 🚦"
            ),
            color=discord.Color.red()
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        else:
            embed.set_thumbnail(url=member.default_avatar.url)
            
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Error in test_welcome command: {e}")

bot.run(TOKEN)
