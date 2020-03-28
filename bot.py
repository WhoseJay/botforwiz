# bot.py
import os
import discord
import gspread
import datetime
import re
import traceback
import sys
from pytz import timezone
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
load_dotenv()
whitelist = ['values', 'bot-commands', 'staff-bots']
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('PREFIX')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
#rename to your credentials.json file
credentials = ServiceAccountCredentials.from_json_keyfile_name('quickstart-1550856539051-4db74089a589.json', scope)
def command_prefix(bot, message):
    if message.guild is None:
        return ''
    else:
        return PREFIX
bot = commands.Bot(command_prefix=command_prefix,help_command=None)

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member:discord.User=None, reason =None):
    if member == None or member == ctx.message.author:
        await ctx.channel.send("You cannot kick yourself")
        return
    memberrole = discord.utils.find(lambda m : m.id == member.id, ctx.guild.members)
    if memberrole.roles[0] >= ctx.message.author.roles[0]:
        await ctx.channel.send("Your role is not high enough to kick this member")
        return
    if reason == None:
        reason = "Breaking the rules."
    message = f"You have been kicked from {ctx.guild.name} for {reason}"
    await member.send(message)
    await ctx.guild.kick(member, reason=reason)
    await ctx.channel.send(f"{member} has been kicked!")
@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member:discord.User=None, reason =None):
    if member == None or member == ctx.message.author:
        await ctx.channel.send("You cannot ban yourself")
        return
    memberrole = discord.utils.find(lambda m : m.id == member.id, ctx.guild.members)
    if memberrole.roles[0] >= ctx.message.author.roles[0]:
        ctx.channel.send("Your role is not high enough to ban this member")
        return
    if reason == None:
        reason = "Breaking the rules."
    message = f"You have been banned from {ctx.guild.name} for {reason}"
    await member.send(message)
    await ctx.guild.ban(member, reason=reason)
    await ctx.channel.send(f"{member} has been banned!")
@bot.command(name='prune')
@commands.has_permissions(manage_messages=True)
async def prune(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount+1)
    await ctx.send(f"Deleted {len(deleted)-1} messages")
@bot.command(name='say', pass_context = True)
async def say(ctx, *args):
    mesg = ' '.join(args)
    if ctx.message.guild is not None:
        await ctx.message.delete()
    return await ctx.send(mesg)
@bot.command(name='list')
async def list(ctx):
    gc = gspread.authorize(credentials)
    values = gc.open_by_key(SPREADSHEET_ID)
    worksheet = values.sheet1
    try:
        item_values = worksheet.get_all_values()
    except Exception as e:
        print(str(e.__class__.__name__))
    
    paginator = commands.Paginator(suffix='', prefix='')
    paginator.add_line('__Here is a complete list of the commands:__')
    for row in item_values:
        paginator.add_line(row[1] + ' - ' + row[2])
    for page in paginator.pages:
        await ctx.author.send(page)
    await ctx.send('Sent the value list to your dms')
@bot.command(name='help')
async def help(ctx):
    gc = gspread.authorize(credentials)
    values = gc.open_by_key(SPREADSHEET_ID)
    worksheet = values.sheet1
    try:
        item_values = worksheet.get_all_values()
    except Exception as e:
        print(str(e.__class__.__name__))
    itemlist = ['**'+item+'**' for item in worksheet.col_values(1)]
    paginator = commands.Paginator(suffix='', prefix='')
    paginator.add_line('__Commands:__')
    paginator.add_line('**'+PREFIX+'help** - Displays this help dialogue to your DMS')
    paginator.add_line('**'+PREFIX+'say** - Make the bot say anything')
    paginator.add_line('**'+PREFIX+'[itemname]** - Displays the value of an item (you may also just type the item without the prefix into my DMS)')
    paginator.add_line('**'+PREFIX+'list** - Sends a list of all the item values in our database in DMS')
    paginator.add_line('')
    paginator.add_line('__Item List__:')
    for item in itemlist:
        paginator.add_line(item)
    paginator.add_line('')
    paginator.add_line('Example:')
    paginator.add_line('?50amazongift')
    paginator.add_line('')
    paginator.add_line('Bot made by WhoseJay#5905')
    for page in paginator.pages:
        await ctx.author.send(page)
    await ctx.send('Check your DMS! :white_check_mark:')

@bot.event
async def on_message(message):
        
    prefix = command_prefix(bot, message)
    if 'a/d' in message.content.lower():
        await message.add_reaction('🇦')
        await message.add_reaction('🇩')
        await message.add_reaction('🇪')
    if message.content.startswith(prefix) and message.author.id != bot.user.id:
        item = message.content.lower()[len(prefix):]
        tz = timezone('EST')
        gc = gspread.authorize(credentials)
        values = gc.open_by_key(SPREADSHEET_ID)
        worksheet = values.sheet1
        if item == 'c:':
            item = 'c:face'
        try:
            item_re = re.compile(r'(\b{}\b)'.format(item))
            cell = worksheet.find(item_re)
        except Exception as e:
            print(str(e.__class__.__name__))
            return await bot.process_commands(message)
        if worksheet.cell(cell.row, cell.col+2).value == '':
            return await bot.process_commands(message)
        if message.guild is None or message.channel.name in whitelist:
            if worksheet.cell(cell.row, cell.col+3).value != '':
                imageurl = worksheet.cell(cell.row, cell.col+3).value
            else:
                imageurl = 'https://www.stickpng.com/assets/images/580b57fcd9996e24bc43c518.png'
            name = worksheet.cell(cell.row, cell.col+1).value
            value = worksheet.cell(cell.row, cell.col+2).value
            embed = discord.Embed(title=name, description=value, color=0xff003c)
            embed.set_image(url=imageurl)
            embed.set_thumbnail(url='https://pngimg.com/uploads/amazon/amazon_PNG5.png')
            embed.set_footer(text="Bot made by aSells Team")
            embed.timestamp = datetime.datetime.now(tz)
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("To see the current aStock's shop, please use this command in <#693583944674967615>!")
@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id == 688161571876372563:
         if payload.emoji.name == '🎉':
              guild = discord.utils.find(lambda g : g.id == payload.guild_id, bot.guilds)
              member = discord.utils.find(lambda m : m.id == payload.user_id, guild.members)
              ROLE = discord.utils.get(guild.roles, name='Giveaway Subscriber')
              await member.add_roles(ROLE)
@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id == 688161571876372563:
         if payload.emoji.name == '🎉':
              guild = discord.utils.find(lambda g : g.id == payload.guild_id, bot.guilds)
              member = discord.utils.find(lambda m : m.id == payload.user_id, guild.members)
              ROLE = discord.utils.get(guild.roles, name='Giveaway Subscriber')
              await member.remove_roles(ROLE)
@bot.event
async def on_command_error(ctx, error):
    # if command has local error handler, return
    if hasattr(ctx.command, 'on_error'):
        return

    # get the original exception
    error = getattr(error, 'original', error)

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.BotMissingPermissions):
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        if len(missing) > 2:
            fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        _message = 'I need the **{}** permission(s) to run this command.'.format(fmt)
        await ctx.send(_message)
        return

    if isinstance(error, commands.DisabledCommand):
        await ctx.send('This command has been disabled.')
        return

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("This command is on cooldown, please retry in {}s.".format(math.ceil(error.retry_after)))
        return

    if isinstance(error, commands.MissingPermissions):
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        if len(missing) > 2:
            fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        _message = 'You need the **{}** permission(s) to use this command.'.format(fmt)
        await ctx.send(_message)
        return

    if isinstance(error, commands.UserInputError):
        await ctx.send("Invalid input.")
        await self.send_command_help(ctx)
        return

    if isinstance(error, commands.NoPrivateMessage):
        try:
            await ctx.author.send('This command cannot be used in direct messages.')
        except discord.Forbidden:
            pass
        return

    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command.")
        return

    # ignore all other exception types, but print them to stderr
    print('Ignoring exception in command {}:'.format(ctx.command))
    traceback.print_exception(type(error), error, error.__traceback__)
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    game = discord.Activity(type=discord.ActivityType.listening, name=PREFIX+'stock')
    await bot.change_presence(activity=game)
bot.run(TOKEN)
