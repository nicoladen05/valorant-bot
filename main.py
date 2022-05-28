from ast import parse
import discord
from discord.ext import commands
from requests import get
import random
import asyncio
import json
import os
import time
import sqlite3
import feedparser
from todoist_api_python.api import TodoistAPI

# configuration
announcements_channel_id = 980051595947544576

client = commands.Bot(command_prefix='.')

# set firefox as the useragent
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0'}

# make a dictionary of all the valorant ranks
valorant_ranks = {
    1: 'Unused',
    2: 'Unused',
    3: 'Iron 1',
    4: 'Iron 2',
    5: 'Iron 3',
    6: 'Bronze 1',
    7: 'Broneze 2',
    8: 'Bronze 3',
    9: 'Silver 1',
    10: 'Silver 2',
    11: 'Silver 3',
    12: 'Gold 1',
    13: 'Gold 2',
    14: 'Gold 3',
    15: 'Platinum 1',
    16: 'Platinum 2',
    17: 'Platinum 3',
    18: 'Diamond 1',
    19: 'Diamond 2',
    20: 'Diamond 3',
    21: 'Immortal 1',
    22: 'Immortal 2',
    23: 'Immortal 3',
    24: 'Radiant'
}

@client.event
async def on_ready():
    # change the bots status
    await client.change_presence(activity=discord.Game(name='WIP | .help'))

    # print the bot's login message
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

    # loop that gets run every 30 seconds
    while True:
        # get all players from the database
        db = sqlite3.connect('players.db')
        cursor = db.cursor()
        cursor.execute('SELECT * FROM players')
        players = cursor.fetchall()
 
        print('Linked players:')
        for player in players:
            print(player)

        # check the ranks of every linked player
        for player in players:
            # split ingame_name into name and tag
            name = player[1].split('#')[0]
            tag = player[1].split('#')[1]

            discord_ping = player[0]

            # get the rank of the player
            url = 'https://api.henrikdev.xyz/valorant/v1/mmr/eu/' + name + '/' + tag
            response = get(url, headers=headers)

            json_response = json.loads(response.text)
            rank = json_response['data']['currenttier']

            print('Checking player ' + name + '#' + tag + ' with rank ' + str(rank) + ' / in database: ' + str(player[2]))

            # if the player is not found, skip
            if response.status_code == 404:
                print("Error checking player")
                continue

            # if the rank is different from the one in the database, update it and send a message to a discord channel
            if rank != player[2]:
                cursor.execute('UPDATE players SET rank_int=' + str(rank) + ' WHERE ingame_name='  + '"' + player[1] + '"')
                db.commit()

                rank_icon_url = f'https://media.valorant-api.com/competitivetiers/564d8e28-c226-3180-6285-e48a390db8b1/{rank}/smallicon.png'

                # if old rank is higher than new rank, send a message to the discord channel
                if player[2] > rank:
                    # make an embed message
                    embed = discord.Embed(title='Rank down!', description='<@!' + discord_ping + '> ist von ' + valorant_ranks[player[2]] + ' zu ' + valorant_ranks[rank] + ' abgestiegen', color=0xff0000)

                    # add the rank icon to the embed message
                    embed.set_thumbnail(url=rank_icon_url)

                    # send the message
                    await client.get_channel(announcements_channel_id).send(embed=embed)

                # if old rank is lower than new rank, send a message to the discord channel
                if player[2] < rank:
                    # make an embed message
                    embed = discord.Embed(title='Rank up!', description='<@!' + discord_ping + '> ist von ' + valorant_ranks[player[2]] + ' zu ' + valorant_ranks[rank] + ' aufgestiegen', color=0x00ff00)

                    # add the rank icon to the embed message
                    embed.set_thumbnail(url=rank_icon_url)

                    # send the message
                    await client.get_channel(announcements_channel_id).send(embed=embed)



            else:
                print(f'{name}s rank did not change')

        db.close()


        print('Checking for new articles')
        # post an announcement to discord when a new post is added to an rss feed
        # get the rss feed
        url = 'https://createfeed.fivefilters.org/extract.php?url=https%3A%2F%2Fplayvalorant.com%2Fen-us%2Fnews%2F&item=div%5Bclass%2A%3D%22NewsCard-module--featured%22%5D+a&item_title=img+%40alt&item_desc=p%5Bclass%2A%3D%22copy-02+NewsCard-module--description%22%5D&item_date=p%5Bclass%2A%3D%22copy-02+NewsCard-module--dateWrapper%22%5D+span%5Bclass%2A%3D%22NewsCard-module--published%22%5D&item_date_format=m%2Fd%2Fy&feed_title=Valorant+RSS+News&max=5&order=document&guid=url'
        response = get(url, headers=headers)

        # parse the rss feed
        parsed_rss = feedparser.parse(response.text)

        # store last_post_date in another file
        with open('last_post_date.txt', 'r') as f:
            last_post_date = f.readline()
            f.close

        # check if the article has already been posted to the discord channel
        for post in parsed_rss.entries:
            # convert post.published to a unix timestamp
            post_date = int(time.mktime(post.published_parsed))
            if post_date > int(last_post_date):
                print('New post found')

                # get the title of the article
                title = post.title

                # get summary of the article
                summary = post.summary

                # get the link of the article
                link = post.link

                # make an embed message
                embed = discord.Embed(title=title, description=link, color=0x00ff00)

                # add embed field
                embed.add_field(name='Summary', value=summary, inline=False)
                embed.add_field(name='Published', value=f'<t:{post_date}:R>', inline=False)

                # send the message
                await client.get_channel(announcements_channel_id).send(embed=embed)

                with open('last_post_date.txt', 'w') as f:
                    f.write(str(post_date))
                    f.close()

        await asyncio.sleep(900)

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
    embed.add_field(name='.suggest', value='Suggests a new feature for the bot', inline=True)
    embed.add_field(name='.stats', value='Show general account stats', inline=True)
    embed.add_field(name='.rank', value='Show a players current rank and elo', inline=True)
    embed.add_field(name='.history', value='Show a players match history', inline=True)
    embed.add_field(name='.link', value='Links a discord account to a valorant account', inline=True)
    embed.add_field(name='.unlink', value='Unlinks a discord account from a valorant account', inline=True)
    await ctx.send(embed=embed)


@client.command()
async def info(ctx):
    embed = discord.Embed(
        title="Info",
        description="This bot was created by: <@!368090462659149826> \n Github Repository: https://github.com/nicoladen05/valorant-bot",
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
        if stats['currenttier'] == None:
            rank_int = 0 
        else:
            rank_int = int(stats['currenttier'])

        rank_icon_url = f'https://media.valorant-api.com/competitivetiers/564d8e28-c226-3180-6285-e48a390db8b1/{rank_int}/smallicon.png'

        # set embed thumbnail
        embed.set_thumbnail(url=rank_icon_url)



        mmr = stats['mmr_change_to_last_game']

        if stats['currenttierpatched'] == None:
            rank = 'Unranked'
        else:
            rank = stats['currenttierpatched']

        embed.add_field(name='Current Rank', value=rank, inline=True)


        if mmr != None:
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


# history command
@client.command()
async def history(ctx, *, nametag):
    # split nametag into name and tag at #
    name_split = nametag.split('#')

    name = name_split[0]
    tag = name_split[1]

    # make a get request
    url = 'https://api.henrikdev.xyz/valorant/v3/matches/eu/' + name + '/' + tag
    response = get(url, headers=headers)

    # check if the response is valid
    if response.status_code == 200:
            
            json_response = json.loads(response.text)

            stats = json_response['data']

            # send title embed
            embed = discord.Embed(
                title=name + "'s History",
                color=0x0000ff
            )

            # send embed
            await ctx.send(embed=embed)
    
            #make a for loop to get the metadata the last 5 games
            for i in range(0, 5):

                # get data from metadata
                map = stats[i]['metadata']['map']
                start_unix = stats[i]['metadata']['game_start']
                mode = stats[i]['metadata']['mode']

                # search for name in stats[i]['players'] and ignore capitalization
                for j in range(0, len(stats[i]['players']['all_players'])):
                    if stats[i]['players']['all_players'][j]['name'].lower() == name.lower():
                        player_stats = stats[i]['players']['all_players'][j]
                        break
                
                player_team = player_stats['team']
                player_character = player_stats['character']
                player_character_icon = player_stats['assets']['agent']['small']
                kills = player_stats['stats']['kills']
                deaths = player_stats['stats']['deaths']
                assists = player_stats['stats']['assists']


                # total shots hit
                total_shots_hit = player_stats['stats']['headshots'] + player_stats['stats']['bodyshots'] + player_stats['stats']['legshots']
                # check if total_shots_hit is 0 so it doesnt break the bot
                if total_shots_hit == 0:
                    total_shots_hit = 1
                # raw hs percent
                headshot_percent_raw = player_stats['stats']['headshots'] / total_shots_hit
                # calculate headshot_percent_raw into a percent value
                headshot_percent = str(round(headshot_percent_raw * 100, 2)) + '%'

                # check if the player has won
                if stats[i]['teams'][str(player_team).lower()]['has_won']:
                    won = True
                else:
                    won = False

                # get exact score
                rounds_won = stats[i]['teams'][str(player_team).lower()]['rounds_won']
                rounds_lost = stats[i]['teams'][str(player_team).lower()]['rounds_lost']

                # combine the score
                score = str(rounds_won) + '-' + str(rounds_lost)

                # change embed color depending on if the player has lost or won
                if won:
                    embed_color = 0x00ff00
                else:
                    embed_color = 0xff0000

                embed = discord.Embed(
                    color=embed_color
                )

                # make embed
                embed.add_field(name='Map', value=map, inline=True)
                embed.add_field(name='Mode', value=mode, inline=True)
                embed.add_field(name='Time', value=f'<t:{start_unix}:R>', inline=True)
                embed.add_field(name='Team', value=player_team, inline=True)
                embed.add_field(name='Character', value=player_character, inline=True)
                embed.add_field(name='Score', value=score, inline=True)
                embed.add_field(name='Kills', value=kills, inline=True)
                embed.add_field(name='Deaths', value=deaths, inline=True)
                embed.add_field(name='Assists', value=assists, inline=True)
                embed.add_field(name='Headshots', value=headshot_percent, inline=True)
                embed.set_thumbnail(url=player_character_icon)

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


# suggest command
@client.command()
async def suggest(ctx, *, suggestion):

    # connect to todoist api
    TODOIST_TOKEN = os.environ.get('TODOIST_TOKEN')
    todoist = TodoistAPI(TODOIST_TOKEN)

    # add a task to todoist
    try:
        todoist.add_task(content=suggestion, project_id=2292334118)

        # send embed suggestion added
        embed = discord.Embed(
            title="Suggestion Added",
            description="Your suggestion has been added to the todoist list",
            color=0x0000ff
        )

        await ctx.send(embed=embed)

    except Exception as error:
        # your suggestion could not be added to todoist
        embed = discord.Embed(
            title="Error",
            description="Your suggestion could not be added to todoist",
            color=0xff0000
        )

        await ctx.send(embed=embed)




# add a link command
@client.command()
async def link(ctx, *, link):

    # connect to database players database
    conn = sqlite3.connect('players.db')
    c = conn.cursor()

    # create players table if it doesnt exist with the following columns: discord_name, ingame_name, rank_int
    c.execute('''CREATE TABLE IF NOT EXISTS players (discord_name text, ingame_name text, rank_int int)''')


    # split link at #
    link_split = link.split('#')

    name = link_split[0]
    tag = link_split[1]



    # get the rank of the player
    url = 'https://api.henrikdev.xyz/valorant/v1/mmr/eu/' + name + '/' + tag
    response = get(url, headers=headers)

    json_response = json.loads(response.text)


    # if respone is 200 the player exists
    if response.status_code == 200:
        print(json_response)
        rank = int(json_response['data']['currenttier'])

        # check if the player isnt already in the database
        c.execute('''SELECT * FROM players WHERE discord_name = ?''', (ctx.author.name,))
        result = c.fetchone()

        # if the player isnt in the database
        if result == None:
            # add the player to the database
            c.execute('''INSERT INTO players (discord_name, ingame_name, rank_int) VALUES (?, ?, ?)''', (ctx.author.id, link, rank))
            conn.commit()

            # make embed
            embed = discord.Embed(
                title="Link Added",
                description="Your accounts have been linked",
                color=0x00ff00
            )

            await ctx.send(embed=embed)

        else:
            # make embed
            embed = discord.Embed(
                title="Error",
                description="Your account is already linked",
                color=0xff0000
            )

            await ctx.send(embed=embed)

    else:
        # make embed
        embed = discord.Embed(
            title="Error",
            description="The Valorant account name you entered does not exist",
            color=0xff0000
        )

        await ctx.send(embed=embed)


    # close database
    conn.close()


# unlink command
@client.command()
async def unlink(ctx):
    # connect to databse
    conn = sqlite3.connect('players.db')
    c = conn.cursor()

    # check if the player is in the database
    c.execute('''SELECT * FROM players WHERE discord_name = ?''', (ctx.author.name,))
    result = c.fetchone()

    # if the player is in the database
    if result != None:
        # delete the player from the database
        c.execute('''DELETE FROM players WHERE discord_name = ?''', (ctx.author.name,))
        conn.commit()

        # make embed
        embed = discord.Embed(
            title="Link Removed",
            description="Your accounts have been unlinked",
            color=0x00ff00
        )

        await ctx.send(embed=embed)

    else:
        # make embed
        embed = discord.Embed(
            title="Error",
            description="Your account is not linked",
            color=0xff0000
        )

        await ctx.send(embed=embed)

    # close database
    conn.close()


TOKEN = os.environ.get('TOKEN')
client.run(TOKEN)