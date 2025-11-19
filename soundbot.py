import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import asyncio
from flask import Flask, request, render_template
from threading import Thread

# Carregar variáveis do .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Caminho exato do FFmpeg
FFMPEG_PATH = "E:/SoundBot/ffmpeg/bin/ffmpeg.exe"

MUSIC_FOLDER = "music"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

queue = []
playing = False
last_guild = None


# ------ FUNÇÃO PRA TOCAR MÚSICA ------
async def play_next(guild):
    global playing, queue

    if len(queue) == 0:
        playing = False
        return

    playing = True
    filename = queue.pop(0)
    path = os.path.join(MUSIC_FOLDER, filename)

    vc = guild.voice_client

    def after_play(err):
        fut = asyncio.run_coroutine_threadsafe(play_next(guild), bot.loop)
        try:
            fut.result()
        except:
            pass

    vc.play(
        discord.FFmpegPCMAudio(
            path,
            executable=FFMPEG_PATH
        ),
        after=after_play
    )

    text_channel = guild.text_channels[0]
    await text_channel.send(f"🎶 Tocando agora: **{filename}**")


# ------ EVENT READY ------
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot online como: {bot.user}")


# ------ COMANDO /join ------
@tree.command(name="join", description="Bot entra no canal de voz")
async def join_cmd(interaction: discord.Interaction):
    global last_guild

    if interaction.user.voice is None:
        return await interaction.response.send_message("Tu não tá em um canal de voz.")

    channel = interaction.user.voice.channel
    await channel.connect()
    last_guild = interaction.guild

    await interaction.response.send_message("Entrei aí 😎")


# ------ COMANDO /play ------
@tree.command(name="play", description="Tocar música local")
@app_commands.describe(nome="Nome exato do arquivo na pasta /music")
async def play_cmd(interaction: discord.Interaction, nome: str):
    global playing, last_guild

    arquivos = os.listdir(MUSIC_FOLDER)

    if nome not in arquivos:
        return await interaction.response.send_message(
            "Não achei essa música 😭\nUsa `/list` pra ver as disponíveis."
        )

    queue.append(nome)
    await interaction.response.send_message(f"Adicionada à fila: **{nome}**")

    last_guild = interaction.guild

    if not playing:
        await play_next(interaction.guild)


# ------ COMANDO /list ------
@tree.command(name="list", description="Listar músicas locais")
async def list_cmd(interaction: discord.Interaction):
    arquivos = os.listdir(MUSIC_FOLDER)
    if len(arquivos) == 0:
        return await interaction.response.send_message("Não tem nada na pasta.")

    lista = "\n".join(arquivos)
    await interaction.response.send_message(f"🎵 Músicas:\n```\n{lista}\n```")


# ------ COMANDO /skip ------
@tree.command(name="skip", description="Pular música atual")
async def skip_cmd(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc is None or not vc.is_playing():
        return await interaction.response.send_message("Nada tocando agora.")

    vc.stop()
    await interaction.response.send_message("Pulei ⏭")

    await play_next(interaction.guild)


# ------ COMANDO /stop ------
@tree.command(name="stop", description="Parar tudo")
async def stop_cmd(interaction: discord.Interaction):
    global queue, playing

    vc = interaction.guild.voice_client
    if vc:
        vc.stop()

    queue = []
    playing = False

    await interaction.response.send_message("Parei tudo 🛑")


# ------ COMANDO /leave ------
@tree.command(name="leave", description="Bot sai do canal")
async def leave_cmd(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()

    await interaction.response.send_message("Saí do canal 👋")


# ==============================
#       FLASK WEB PANEL
# ==============================

app = Flask(__name__, template_folder="templates")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/play")
def api_play():
    global last_guild

    nome = request.args.get("nome")
    if not nome:
        return "Faltou o nome da música."

    if not last_guild:
        return "O bot não está em um canal."

    queue.append(nome)
    asyncio.run_coroutine_threadsafe(play_next(last_guild), bot.loop)

    return f"Tocando {nome}"


@app.route("/skip")
def api_skip():
    global last_guild

    if not last_guild:
        return "O bot não está em um canal."

    vc = last_guild.voice_client
    if not vc:
        return "O bot não está conectado."

    vc.stop()
    return "Pulou!"


@app.route("/list")
def api_list():
    arquivos = os.listdir(MUSIC_FOLDER)
    return "<br>".join(arquivos)


# Rodar Flask e Bot ao mesmo tempo
def run_flask():
    app.run(host="0.0.0.0", port=5000)


Thread(target=run_flask).start()


# ----------- RUN BOT --------------
bot.run(TOKEN)
