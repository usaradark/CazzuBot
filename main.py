import discord
from discord.ext import commands

import traceback

# Add bot here: https://discordapp.com/oauth2/authorize?client_id=427583823912501248&scope=bot

def get_prefix(bot, msg):
    pre = ['d!']  
    return pre

description = '''Bot is in very early development for the Friends server.'''
bot = commands.Bot(command_prefix=get_prefix, description=description, self_bot = False, owner_id = 92664421553307648, case_insensitive=True)

# Core -------------------
@bot.event
async def on_ready():
    print('Bot has initialized...')
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('-------------------------')    
    print('READY!')
    print('-------------------------')
    
extensions = ['cogs.member', 'cogs.admin', 'cogs.dev', 'cogs.automations']

if __name__ == '__main__':
    for ext in extensions:
        try:
            bot.load_extension(ext)
        except:
            print('Failed to load extension: {}'.format(ext))
            traceback.print_exc()
            
    with open('super', 'r') as readfile:
        state = readfile.read()
        if state == 'True':
            bot.super = True
        else:
            bot.super = False

bot.run('NDI3NTgzODIzOTEyNTAxMjQ4.DZmp-g.cbCEz6WIXca5QRjeDV1hqqPKYR4', reconnect=True)
