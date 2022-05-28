from email import header
import discord
from discord.ext import commands
from requests import get
import random
import asyncio
import json
import os
import time

client = commands.Bot(command_prefix='.')

# set firefox as the useragent
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0'}

@client.event
async def on_ready():
    # change the bots status
    await client.change_presence(activity=discord.Game(name='WIP | .help'))

    # print the bot's login message
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


# change the default help command
client.remove_command('help')


@client.command()
async def help(ctx):
    embed = discord.Embed(
        title="Help",
        description="Here are all the commands you can use:",
        color=0x00ff00
    )

    embed.add_field(name='.help', value='Shows this message', inline=True)
    embed.add_field(name='.info', value='Shows the bot\'s info', inline=True)
    await ctx.send(embed=embed)


@client.command()
async def info(ctx):
    embed = discord.Embed(
        title="Info",
        description="This bot was created by: <@!368090462659149826>",
        color=0x00ff00
    )

    await ctx.send(embed=embed)

# get basic valorant stats
@client.command()
async def stats(ctx, *, nametag):

    # split the nametag at the #
    name_split = nametag.split('#')

    name = name_split[0]
    tag = name_split[1]


    # make a get request
    url = 'https://api.henrikdev.xyz/valorant/v1/account/' + name + '/' + tag
    response = get(url, headers=headers)

    # check if the response is valid
    if response.status_code == 200:

        json_response = json.loads(response.text)

        stats = json_response['data']

        embedicon = stats['card']

        embed = discord.Embed(
            title=name + "'s Account",
            thumbnail=embedicon['small'],
            color=0x00ff00
        )

        # add embedicon as thumbnail
        embed.set_thumbnail(url=embedicon['small'])

        # add embed field with account_level
        embed.add_field(name='Level', value=stats['account_level'], inline=True)

        await ctx.send(embed=embed)

    elif response.status_code == 404:
        # make a embed
        embed = discord.Embed(
            title="Error",
            description="The player you searched for doesn't exist",
            color=0xff0000
        )

        await ctx.send(embed=embed)

    else:
        # send error embed
        embed = discord.Embed(
            title="Error",
            description="An error occured",
            color=0xff0000
        )

        await ctx.send(embed=embed)

# add a rank command
@client.command()
async def rank(ctx, *, nametag):
    # split the nametag at the #
    name_split = nametag.split('#')

    name = name_split[0]
    tag = name_split[1]


    # make a get request
    url = 'https://api.henrikdev.xyz/valorant/v1/mmr/eu/' + name + '/' + tag
    response = get(url, headers=headers)

    # check if the response is valid
    if response.status_code == 200:

        json_response = json.loads(response.text)

        stats = json_response['data']

        embed = discord.Embed(
            title=name + "'s Rank",
            color=0x00ff00
        )

        #rank icon
        rank_int = int(stats['currenttier'])
        rank_icon_url = f'https://media.valorant-api.com/competitivetiers/564d8e28-c226-3180-6285-e48a390db8b1/{rank_int}/smallicon.png'

        # set embed thumbnail
        embed.set_thumbnail(url=rank_icon_url)



        mmr = stats['mmr_change_to_last_game']

        embed.add_field(name='Current Rank', value=stats['currenttierpatched'], inline=True)

        if mmr > 0:
            embed.add_field(name='Last Match', value='+' + str(mmr), inline=True)
        elif mmr < 0:
            embed.add_field(name='Last Match', value=str(mmr), inline=True)

        embed.add_field(name='Elo', value=stats['ranking_in_tier'], inline=True)

        embed.add_field(name='Total Elo', value=stats['elo'], inline=True)



        await ctx.send(embed=embed)

    elif response.status_code == 404:
        # make a embed
        embed = discord.Embed(
            title="Error",
            description="The player you searched for doesn't exist",
            color=0xff0000
        )

        await ctx.send(embed=embed)

    else:
        # send error embed
        embed = discord.Embed(
            title="Error",
            description="An error occured",
            color=0xff0000
        )

        await ctx.send(embed=embed)


    

client.run('OTc5ODI3MjExNjUxNjQ1NTAw.GbxAJm.3B5sv0vgimID0nvTKi9U_y7aL2xDoelOncOkB8')