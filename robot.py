import os

import discord
from discord.ext import commands

token = os.getenv("DISCORD__BOT_TOKEN") 

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
@commands.has_permissions(administrator=True)
async def synccommands(ctx):
    await bot.tree.sync()
    await ctx.send("同步完成")

@bot.hybrid_command()
async def ping(ctx):
    """機器人在嗎?"""
    await ctx.send("Pong!")

@bot.hybrid_command()
async def add(ctx, a:int, b:int):
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
        await interaction.response.edit_message(content="不玩了", view=None)

@bot.hybrid_command()
async def play(ctx):
    await ctx.send("選擇你要出什麼吧",view=PlayView())



bot.run(token)