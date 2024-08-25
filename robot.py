import os
import discord
from discord.ext import commands
import yt_dlp as youtube_dl

token = os.getenv("DISCORD__BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 待播放清單
playing_list = []

@bot.command()
async def helpme(ctx):
    """顯示可用指令"""
    help_text = (
        "指令列表:\n"
        "```"
        "!ping - 機器人在嗎?\n"
        "!add <a> <b> - 把數字相加\n"
        "!game - 猜拳遊戲\n"
        "!join - 加入語音頻道\n"
        "!out - 離開語音頻道\n"
        "!play <url> - 播放指定的音樂或視頻\n"
        "!stop - 停止播放音樂並暫停在當前播放位置\n"
        "!go - 從上次停止的地方繼續播放音樂\n"
        "!skip - 跳過當前播放的音樂\n"
        "!list - 顯示目前待播放清單\n"
        "```"
    )
    await ctx.send(help_text)


@bot.command()
async def ping(ctx):
    """機器人在嗎?"""
    await ctx.send("Pong!")

@bot.command()
async def add(ctx, a: int, b: int):
    """把數字相加"""
    await ctx.send(a + b)

class PlayView(discord.ui.View):
    def get_content(self, label):
        counter = {
            "剪刀": "石頭",
            "石頭": "布",
            "布": "剪刀",
        }
        return f"你出了{label}. 對手出了{counter[label]}. 你輸了"
    
    @discord.ui.button(label="剪刀", style=discord.ButtonStyle.green, emoji="✂")
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=self.get_content(button.label))

    @discord.ui.button(label="石頭", style=discord.ButtonStyle.green, emoji="🪨")
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=self.get_content(button.label))

    @discord.ui.button(label="布", style=discord.ButtonStyle.green, emoji="🧻")
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=self.get_content(button.label))

    @discord.ui.button(label="不玩了", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="真沒骨氣", view=None)

@bot.command()
async def game(ctx):
    await ctx.send("選擇你要出什麼吧", view=PlayView())

@bot.command()
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("你需要先進入一個語音頻道！")
        return
    channel = ctx.author.voice.channel
    await channel.connect()

@bot.command()
async def out(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        await voice_client.disconnect()

@bot.command()
async def stop(ctx):
    """暫停當前音樂並保留播放進度"""
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.pause()  # 暫停音樂播放
        await ctx.send("音樂已暫停，播放進度已保留。")
    else:
        await ctx.send("目前沒有音樂在播放。")


@bot.command()
async def go(ctx):
    """繼續從暫停的音樂位置播放"""
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        if voice.is_paused():
            voice.resume()  # 繼續播放音樂
            await ctx.send("音樂已恢復播放。")
        else:
            await ctx.send("音樂目前沒有被暫停。")
    else:
        await ctx.send("機器人不在任何語音頻道。")


@bot.command()
async def skip(ctx):
    """跳過當前音樂並播放清單中的下一首音樂"""
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.stop()
        if len(playing_list) > 0:
            await ctx.send("跳過當前歌曲，播放下一首音樂。")
            bot.loop.create_task(play_next(ctx))
        else:
            await ctx.send("播放清單已經空了。")
    else:
        await ctx.send("目前沒有音樂在播放。")

@bot.command()
async def list(ctx):
    """顯示目前待播放清單"""
    if len(playing_list) == 0:
        await ctx.send("待播放清單是空的。")
        return

    # 格式化待播放清單
    playlist_details = []
    for index, song in enumerate(playing_list):
        track_title = song.get('title', '未知標題')
        track_length = song.get('length', '未知長度')
        estimated_time = song.get('estimated_time', '未知時間')
        position_in_queue = index + 1
        position_in_upcoming = "Next" if index == 0 else f"{index + 1}"

        details = (
            f"{position_in_queue}:\n"
            f"歌名: {track_title}\n"
            f"總長度: {estimated_time}\n"
            f"時間: {track_length}\n"
            f"Position in upcoming: {position_in_upcoming}\n"
            f"Position in queue: {position_in_queue}\n"
        )
        playlist_details.append(details)

    # 發送待播放清單
    playlist_message = "\n".join(playlist_details)
    await ctx.send(f"```ini\n目前待播放清單:\n{playlist_message}\n```")




async def play_next(ctx):
    """播放清單中的下一首歌曲"""
    if len(playing_list) > 0:
        url = playing_list.pop(0)
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True
        }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            voice.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options), after=lambda e: bot.loop.create_task(play_next(ctx)) if e is None else bot.loop.create_task(ctx.send(f"播放時發生錯誤: {e}")))
            await ctx.send(f"正在播放: {info['title']}")
        except Exception as e:
            await ctx.send(f"發生錯誤: {str(e)}")
    else:
        await ctx.send("點歌阿!!")

@bot.command()
async def play(ctx, url: str):
    if not ctx.author.voice:
        await ctx.send("你需要先進入一個語音頻道！")
        return

    channel = ctx.author.voice.channel
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if not voice:
        voice = await channel.connect()

    if voice.is_playing():
        await ctx.send("目前已有音樂在播放。")
        # 添加歌曲到播放清單時，儲存標題、URL、預估播放時間和長度
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            length = info.get('duration', '未知長度')
            estimated_time = "03:24"  # 這個需要根據你的需求更新
        playing_list.append({
            'title': info['title'],
            'url': url,
            'length': f"{length // 60:02}:{length % 60:02}",
            'estimated_time': estimated_time
        })
        await ctx.send("已將此歌曲加入待播放清單")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            length = info.get('duration', '未知長度')
            estimated_time = "03:24"  # 這個需要根據你的需求更新
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        voice.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options), after=lambda e: bot.loop.create_task(play_next(ctx)) if e is None else bot.loop.create_task(ctx.send(f"播放時發生錯誤: {e}")))
        playing_list.append({
            'title': info['title'],
            'url': url,
            'length': f"{length // 60:02}:{length % 60:02}",
            'estimated_time': estimated_time
        })
        await ctx.send(f"正在播放: {info['title']}")
    except Exception as e:
        await ctx.send(f"發生錯誤: {str(e)}")


bot.run(token)
