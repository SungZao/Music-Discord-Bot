import os
import discord
from discord.ext import commands
from discord import app_commands

import asyncio
from flask import Flask, request, send_from_directory
from threading import Thread
import logging

# silencia logs do werkzeug
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


# Primeiro tenta variável de ambiente, senão usa fallback
TOKEN = "TOKEN_DO_SEU_BOT"

# ====================
# OUTRAS CONFIGS
# ====================
FFMPEG_PATH = "E:/SoundBot/ffmpeg/bin/ffmpeg.exe"
MUSIC_FOLDER = "music"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

queue = []
playing = False
current_volume = 0.6
current_seek = 0
last_guild = None


# ============================
# FUNÇÃO DE FADE
# ============================
async def fade_volume(vc, start, end, duration=0.8):
    steps = 20
    step_time = duration / steps
    diff = (end - start) / steps

    volume = start
    for _ in range(steps):
        volume += diff
        try:
            if vc and vc.source:
                vc.source.volume = max(0, min(volume, 1))
        except Exception:
            pass
        await asyncio.sleep(step_time)


# ============================
# FUNÇÃO PRINCIPAL -> TOCAR
# ============================
async def play_next(guild, seek_pos=0):
    global queue, playing, current_volume, current_seek

    if not queue:
        playing = False
        return

    filename = queue[0]
    path = os.path.join(MUSIC_FOLDER, filename)

    vc = guild.voice_client
    if vc is None:
        playing = False
        return

    playing = True
    current_seek = seek_pos

    ffmpeg_options = {
        "before_options": f"-ss {seek_pos}",
        "options": "-vn"
    }

    audio = discord.FFmpegPCMAudio(
        path,
        executable=FFMPEG_PATH,
        **ffmpeg_options
    )

    audio = discord.PCMVolumeTransformer(audio, volume=0)

    def after_play(err):
        try:
            tocada = queue.pop(0)
            queue.append(tocada)
            fut = asyncio.run_coroutine_threadsafe(play_next(guild), bot.loop)
            fut.result()
        except Exception:
            pass

    vc.play(audio, after=after_play)

    # fade-in
    try:
        await fade_volume(vc, 0, current_volume, 0.8)
    except Exception:
        pass

    try:
        channel = guild.text_channels[0]
        await channel.send(f"🎶 Tocando agora: **{filename}**")
    except Exception:
        pass


# ============================
# EVENTO READY
# ============================
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot online: {bot.user}")


# ============================
# COMANDOS
# ============================
@tree.command(name="join")
async def join_cmd(interaction: discord.Interaction):
    global last_guild

    if interaction.user.voice is None:
        return await interaction.response.send_message("Tu não tá num canal de voz. Entra em um canal primeiro.")

    channel = interaction.user.voice.channel
    await channel.connect()

    last_guild = interaction.guild
    await interaction.response.send_message("Entrei 😎")


@tree.command(name="play")
async def play_cmd(interaction: discord.Interaction, nome: str):
    global last_guild, playing

    arquivos = os.listdir(MUSIC_FOLDER)

    if nome not in arquivos:
        return await interaction.response.send_message("Não achei essa música 😭")

    queue.append(nome)
    last_guild = interaction.guild

    await interaction.response.send_message(f"Adicionei **{nome}** na fila")

    if not playing:
        await play_next(interaction.guild)


@tree.command(name="list")
async def list_cmd(interaction: discord.Interaction):
    arquivos = os.listdir(MUSIC_FOLDER)
    lista = "\n".join(arquivos)
    await interaction.response.send_message(f"```\n{lista}\n```")


@tree.command(name="skip")
async def skip_cmd(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        try:
            await fade_volume(vc, vc.source.volume, 0, 0.5)
        except Exception:
            pass
        vc.stop()
    await interaction.response.send_message("Pulei ⏭")


@tree.command(name="stop")
async def stop_cmd(interaction: discord.Interaction):
    global queue, playing

    vc = interaction.guild.voice_client
    if vc:
        try:
            await fade_volume(vc, vc.source.volume, 0, 0.5)
        except Exception:
            pass
        vc.stop()

    queue = []
    playing = False

    await interaction.response.send_message("Pareeeei 🛑")


@tree.command(name="leave")
async def leave_cmd(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
    await interaction.response.send_message("Saí 👋")


# ============================
# PAINEL WEB
# ============================
app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/list")
def api_list():
    try:
        return "<br>".join(os.listdir(MUSIC_FOLDER))
    except Exception:
        return "Erro ao listar músicas"


@app.route("/play")
def api_play():
    global last_guild, playing

    nome = request.args.get("nome")
    if not nome:
        return "Nome inválido"

    queue.clear()
    queue.append(nome)

    if last_guild and last_guild.voice_client:
        vc = last_guild.voice_client

        if vc.is_playing():
            try:
                asyncio.run_coroutine_threadsafe(
                    fade_volume(vc, vc.source.volume, 0, 0.6),
                    bot.loop
                ).result()
            except Exception:
                pass
            vc.stop()

        fut = asyncio.run_coroutine_threadsafe(play_next(last_guild), bot.loop)
        fut.result()

    return "ok"


@app.route("/skip")
def api_skip():
    if last_guild and last_guild.voice_client:
        try:
            asyncio.run_coroutine_threadsafe(
                fade_volume(last_guild.voice_client, current_volume, 0, 0.5),
                bot.loop
            ).result()
        except Exception:
            pass
        last_guild.voice_client.stop()
    return "ok"


@app.route("/stop")
def api_stop():
    global queue, playing
    if last_guild and last_guild.voice_client:
        try:
            asyncio.run_coroutine_threadsafe(
                fade_volume(last_guild.voice_client, current_volume, 0, 0.5),
                bot.loop
            ).result()
        except Exception:
            pass
        last_guild.voice_client.stop()
    queue = []
    playing = False
    return "ok"


@app.route("/volume")
def api_volume():
    global current_volume, last_guild

    try:
        v = float(request.args.get("v", 50)) / 100
    except Exception:
        v = current_volume

    current_volume = v

    vc = last_guild.voice_client
    if vc and getattr(vc, "source", None):
        try:
            vc.source.volume = v
        except Exception:
            pass

    return "ok"


@app.route("/seek")
def api_seek():
    global current_seek

    try:
        pos = int(request.args.get("p", 0))
    except Exception:
        pos = 0
    current_seek = pos

    if last_guild and last_guild.voice_client:
        last_guild.voice_client.stop()
        fut = asyncio.run_coroutine_threadsafe(play_next(last_guild, pos), bot.loop)
        fut.result()

    return "ok"


# ============================
# RODAR FLASK
# ============================
def start_flask():
    # <<< COLOQUE_SEU_IP_AQUI no GitHub antes de rodar
    host = "SEU_IP_AQUI"
    port = 5000
    print(f"Painel Web rodando em http://{host}:{port}")
    app.run(host=host, port=port)


Thread(target=start_flask, daemon=True).start()
bot.run(TOKEN)
