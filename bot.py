import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from aiohttp import web
import asyncio

# 1. إعداد نظام تتبع الأحداث (Logging) الاحترافي
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DiscordBuilder')

# 2. تحميل المتغيرات البيئية (Security Best Practice)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    logger.error("Critical: DISCORD_TOKEN not found in .env file.")
    exit(1)

# 3. إعداد الصلاحيات (Intents)
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True  # صلاحية قراءة الأعضاء (مهمة للترحيب وتوزيع الرتب)

bot = commands.Bot(command_prefix='!', intents=intents)

# ==========================================
# كود سيرفر الويب الوهمي لمنع Render من إيقاف البوت
# ==========================================
async def handle(request):
    return web.Response(text="Bot is running 24/7!")

app = web.Application()
app.router.add_get('/', handle)

async def start_web_server():
    runner = web.AppRunner(app)
    await runner.setup()
    # Render بيستخدم بورت 10000 افتراضياً للخدمات المجانية
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    logger.info("Dummy web server started on port 10000")
# ==========================================

# 4. هيكل البيانات (Configuration Structure) المحدث
ROLES_CONFIG = [
    {"name": "👑・Pit Boss", "color": discord.Color.red(), "hoist": True, "permissions": discord.Permissions(administrator=True)},
    {"name": "🚨・Race Steward", "color": discord.Color.orange(), "hoist": True, "permissions": discord.Permissions(manage_messages=True, kick_members=True)},
    {"name": "🔴・Content Creator", "color": discord.Color.purple(), "hoist": True, "permissions": discord.Permissions.none()},
    {"name": "🏁・Sim Racer", "color": discord.Color.dark_blue(), "hoist": True, "permissions": discord.Permissions.none()},
    {"name": "🌵・Horizon Driver", "color": discord.Color.gold(), "hoist": True, "permissions": discord.Permissions.none()},
    {"name": "🏎️・LMU Pilot", "color": discord.Color.light_grey(), "hoist": True, "permissions": discord.Permissions.none()}, # الرتبة الجديدة
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
    "⏱️ | LE MANS ULTIMATE": [ # القسم الجديد
        {"name": "🏁・lmu-general", "type": "text"},
        {"name": "⚙️・lmu-setups", "type": "text"}
    ],
    "🏆 | COMPETITIVE RACING": [ # القسم الجديد
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
        {"name": "🏎️ | LMU Grid", "type": "voice"}, # روم LMU
        {"name": "🏆 | Race Control", "type": "voice"}, # روم البطولات
        {"name": "🔴 | Streaming...", "type": "voice"}
    ]
}

EMOJI_TO_ROLE = {
    "🏁": "🏁・Sim Racer",
    "🌵": "🌵・Horizon Driver",
    "🏎️": "🏎️・LMU Pilot", # الإيموجي الجديد
    "🛞": "🛞・Wheel User",
    "🕹️": "🕹️・Controller User"
}

# ----------------- الأحداث الأساسية (Events) -----------------

@bot.event
async def on_ready():
    # تشغيل سيرفر الويب الوهمي بالتوازي مع البوت
    bot.loop.create_task(start_web_server())
    logger.info(f'System Online: Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info('Awaiting deployment commands...')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
        
    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    
    if channel.name != "🏷️・get-roles":
        return
        
    role_name = EMOJI_TO_ROLE.get(str(payload.emoji))
    if role_name:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
            if member:
                await member.add_roles(role)
                logger.info(f"Assigned {role_name} to {member.display_name}")

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return
        
    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    
    if channel.name != "🏷️・get-roles":
        return
        
    role_name = EMOJI_TO_ROLE.get(str(payload.emoji))
    if role_name:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
            if member:
                await member.remove_roles(role)
                logger.info(f"Removed {role_name} from {member.display_name}")

@bot.event
async def on_member_join(member):
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

# ----------------- الأوامر (Commands) -----------------

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


@bot.command(name='test_welcome')
@commands.has_permissions(administrator=True)
async def simulate_welcome(ctx):
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


bot.run(TOKEN)
