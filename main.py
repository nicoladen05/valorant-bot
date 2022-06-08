import discord
from discord.ext import commands
from requests import get
import asyncio
import json
import os
import time
import sqlite3
import feedparser
from dotenv import load_dotenv
from todoist_api_python.api import TodoistAPI

# configuration
announcements_channel_id = 980051595947544576

intents = discord.Intents.default()
intents.members = True
intents.presences = True

client = commands.Bot(command_prefix=".", intents=intents)

# load dotenv
load_dotenv()

# set firefox as the useragent
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0"
}

# make a dictionary of all the valorant ranks
valorant_ranks = {
    1: "Unused",
    2: "Unused",
    3: "Iron 1",
    4: "Iron 2",
    5: "Iron 3",
    6: "Bronze 1",
    7: "Bronze 2",
    8: "Bronze 3",
    9: "Silver 1",
    10: "Silver 2",
    11: "Silver 3",
    12: "Gold 1",
    13: "Gold 2",
    14: "Gold 3",
    15: "Platinum 1",
    16: "Platinum 2",
    17: "Platinum 3",
    18: "Diamond 1",
    19: "Diamond 2",
    20: "Diamond 3",
    21: "Immortal 1",
    22: "Immortal 2",
    23: "Immortal 3",
    24: "Radiant",
}


async def check_name(name, ctx):
    # if name is a discord user
    if name.startswith("<@") and name.endswith(">"):
        # get their corresponding valorant name from the database
        conn = sqlite3.connect("players.db")
        c = conn.cursor()
        try:
            c.execute(
                "SELECT ingame_name FROM players WHERE discord_name = ?", (name[2:-1],)
            )
            name = c.fetchone()[0]

            # split name at #
            name = name.split("#")

            conn.close()

            return name
        # if the user is not in the database
        except TypeError:
            # embed you have to link your account
            embed = discord.Embed(
                title="You have to link your account first!",
                description="Use `.link` to link your account.",
                color=0x00FF00,
            )

            # send the embed
            await ctx.send(embed=embed)

            conn.close()

            # return None
            return


    # if name is a valorant name
    else:
        name = name.split("#")

        # return name
        return name


@client.event
async def on_ready():
    # change the bots status
    await client.change_presence(activity=discord.Game(name=".help"))

    # print the bot's login message
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")

    # loop that gets run every 15 minutes
    while True:
        # get all players from the database
        db = sqlite3.connect("players.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM players")
        players = cursor.fetchall()

        print("Linked players:")
        for player in players:
            print(player)

        # check the ranks of every linked player
        for player in players:
            # split ingame_name into name and tag
            name = player[1].split("#")[0]
            tag = player[1].split("#")[1]

            discord_ping = player[0]

            # get the rank of the player
            url = "https://api.henrikdev.xyz/valorant/v1/mmr/eu/" + name + "/" + tag
            response = get(url, headers=headers)

            json_response = json.loads(response.text)
            rank = json_response["data"]["currenttier"]

            print(
                "Checking player "
                + name
                + "#"
                + tag
                + " with rank "
                + str(rank)
                + " / in database: "
                + str(player[2])
            )

            # if the player is not found, skip
            if response.status_code == 404:
                print("Error checking player")
                continue

            # if the rank is different from the one in the database, update it and send a message to a discord channel
            if rank != player[2]:
                cursor.execute(
                    "UPDATE players SET rank_int="
                    + str(rank)
                    + " WHERE ingame_name="
                    + '"'
                    + player[1]
                    + '"'
                )
                db.commit()

                rank_icon_url = f"https://media.valorant-api.com/competitivetiers/564d8e28-c226-3180-6285-e48a390db8b1/{rank}/smallicon.png"

                # if old rank is higher than new rank, send a message to the discord channel
                if player[2] > rank:
                    # make an embed message
                    embed = discord.Embed(
                        title="Rank down!",
                        description="<@!"
                        + discord_ping
                        + "> ist von "
                        + valorant_ranks[player[2]]
                        + " zu "
                        + valorant_ranks[rank]
                        + " abgestiegen",
                        color=0xFF0000,
                    )

                    # add the rank icon to the embed message
                    embed.set_thumbnail(url=rank_icon_url)

                    # send the message
                    await client.get_channel(announcements_channel_id).send(embed=embed)

                # if old rank is lower than new rank, send a message to the discord channel
                if player[2] < rank:
                    # make an embed message
                    embed = discord.Embed(
                        title="Rank up!",
                        description="<@!"
                        + discord_ping
                        + "> ist von "
                        + valorant_ranks[player[2]]
                        + " zu "
                        + valorant_ranks[rank]
                        + " aufgestiegen",
                        color=0x00FF00,
                    )

                    # add the rank icon to the embed message
                    embed.set_thumbnail(url=rank_icon_url)

                    # send the message
                    await client.get_channel(announcements_channel_id).send(embed=embed)

            else:
                print(f"{name}s rank did not change")

        db.close()

        print("Checking for new articles")
        # post an announcement to discord when a new post is added to an rss feed
        # get the rss feed
        url = "https://createfeed.fivefilters.org/extract.php?url=https%3A%2F%2Fplayvalorant.com%2Fen-us%2Fnews%2F&item=div%5Bclass%2A%3D%22NewsCard-module--featured%22%5D+a&item_title=img+%40alt&item_desc=p%5Bclass%2A%3D%22copy-02+NewsCard-module--description%22%5D&item_date=p%5Bclass%2A%3D%22copy-02+NewsCard-module--dateWrapper%22%5D+span%5Bclass%2A%3D%22NewsCard-module--published%22%5D&item_date_format=m%2Fd%2Fy&feed_title=Valorant+RSS+News&max=5&order=document&guid=url"
        response = get(url, headers=headers)

        # parse the rss feed
        parsed_rss = feedparser.parse(response.text)

        # store last_post_date in another file
        with open("last_post_date.txt", "r") as f:
            last_post_date = f.readline()
            f.close

        # check if the article has already been posted to the discord channel
        for post in parsed_rss.entries:
            # convert post.published to a unix timestamp
            post_date = int(time.mktime(post.published_parsed))
            if post_date > int(last_post_date):
                print("New post found")

                # get the title of the article
                title = post.title

                # get summary of the article
                summary = post.summary

                # get the link of the article
                link = post.link

                # make an embed message
                embed = discord.Embed(title=title, description=link, color=0x00FF00)

                # add embed field
                embed.add_field(name="Summary", value=summary, inline=False)
                embed.add_field(
                    name="Published", value=f"<t:{post_date}:R>", inline=False
                )

                # send the message
                await client.get_channel(announcements_channel_id).send(embed=embed)

                with open("last_post_date.txt", "w") as f:
                    f.write(str(post_date))
                    f.close()

        await asyncio.sleep(900)


# change the default help command
client.remove_command("help")


@client.command()
async def help(ctx):
    embed = discord.Embed(
        title="Help",
        description="Here are all the commands you can use:",
        color=0x00FF00,
    )

    embed.add_field(name=".help", value="Shows this message", inline=True)
    embed.add_field(name=".info", value="Shows the bot's info", inline=True)
    embed.add_field(
        name=".suggest", value="Suggests a new feature for the bot", inline=True
    )
    embed.add_field(name=".stats ", value="Show general account stats", inline=True)
    embed.add_field(
        name=".rank", value="Show a players current rank and elo", inline=True
    )
    embed.add_field(name=".history", value="Show a players match history", inline=True)
    embed.add_field(
        name=".link", value="Links a discord account to a valorant account", inline=True
    )
    embed.add_field(
        name=".unlink",
        value="Unlinks a discord account from a valorant account",
        inline=True,
    )
    embed.add_field(
        name=".looking", value="Look for players that you can queue with", inline=True
    )
    await ctx.send(embed=embed)


@client.command()
async def info(ctx):
    embed = discord.Embed(
        title="Info",
        description="This bot was created by: <@!368090462659149826> \n Github Repository: https://github.com/nicoladen05/valorant-bot",
        color=0x00FF00,
    )

    await ctx.send(embed=embed)


# get basic valorant stats
@client.command()
async def stats(ctx, *, nametag):

    check = await check_name(nametag, ctx)

    # split checkname nametag at #
    name = check[0]
    tag = check[1]

    # make a get request
    url = "https://api.henrikdev.xyz/valorant/v1/account/" + name + "/" + tag
    response = get(url, headers=headers)

    # check if the response is valid
    if response.status_code == 200:

        json_response = json.loads(response.text)

        stats = json_response["data"]

        embedicon = stats["card"]

        embed = discord.Embed(
            title=name + "'s Account", thumbnail=embedicon["small"], color=0x00FF00
        )

        # add embedicon as thumbnail
        embed.set_thumbnail(url=embedicon["small"])

        # add embed field with account_level
        embed.add_field(name="Level", value=stats["account_level"], inline=True)

        await ctx.send(embed=embed)

    elif response.status_code == 404:
        # make a embed
        embed = discord.Embed(
            title="Error",
            description="The player you searched for doesn't exist",
            color=0xFF0000,
        )

        await ctx.send(embed=embed)

    else:
        # send error embed
        embed = discord.Embed(
            title="Error", description="An error occured", color=0xFF0000
        )

        await ctx.send(embed=embed)


# add a rank command
@client.command()
async def rank(ctx, *, nametag):
    check = await check_name(nametag, ctx)

    # split checkname nametag at #
    name = check[0]
    tag = check[1]

    # make a get request
    url = "https://api.henrikdev.xyz/valorant/v1/mmr/eu/" + name + "/" + tag
    response = get(url, headers=headers)

    # check if the response is valid
    if response.status_code == 200:

        json_response = json.loads(response.text)

        stats = json_response["data"]

        # easter egg xd
        if name == "nicoladen 鳩" and tag == "hart":
            embed = discord.Embed(title=name + "'s Rank", color=0x00FF00)
            rank_int = int(stats["currenttier"])

            rank_icon_url = f"https://media.valorant-api.com/competitivetiers/564d8e28-c226-3180-6285-e48a390db8b1/24/smallicon.png"

            # set embed thumbnail
            embed.set_thumbnail(url=rank_icon_url)

            embed.add_field(name="Current Rank", value="Radiant", inline=True)

            mmr = stats["mmr_change_to_last_game"]
            if mmr != None:
                if mmr > 0:
                    embed.add_field(
                        name="Last Match", value="+" + str(mmr), inline=True
                    )
                elif mmr < 0:
                    embed.add_field(name="Last Match", value=str(mmr), inline=True)

            embed.add_field(name="Elo", value="∞", inline=True)

            embed.add_field(name="Total Elo", value="∞", inline=True)

            await ctx.send(embed=embed)

            return

        embed = discord.Embed(title=name + "'s Rank", color=0x00FF00)

        # rank icon
        if stats["currenttier"] == None:
            rank_int = 0
        else:
            rank_int = int(stats["currenttier"])

        rank_icon_url = f"https://media.valorant-api.com/competitivetiers/564d8e28-c226-3180-6285-e48a390db8b1/{rank_int}/smallicon.png"

        # set embed thumbnail
        embed.set_thumbnail(url=rank_icon_url)

        mmr = stats["mmr_change_to_last_game"]

        if stats["currenttierpatched"] == None:
            rank = "Unranked"
        else:
            rank = stats["currenttierpatched"]

        embed.add_field(name="Current Rank", value=rank, inline=True)

        if mmr != None:
            if mmr > 0:
                embed.add_field(name="Last Match", value="+" + str(mmr), inline=True)
            elif mmr < 0:
                embed.add_field(name="Last Match", value=str(mmr), inline=True)

        embed.add_field(name="Elo", value=stats["ranking_in_tier"], inline=True)

        embed.add_field(name="Total Elo", value=stats["elo"], inline=True)

        await ctx.send(embed=embed)

    elif response.status_code == 404:
        # make a embed
        embed = discord.Embed(
            title="Error",
            description="The player you searched for doesn't exist",
            color=0xFF0000,
        )

        await ctx.send(embed=embed)

    else:
        # send error embed
        embed = discord.Embed(
            title="Error", description="An error occured", color=0xFF0000
        )

        await ctx.send(embed=embed)


# history command
@client.command()
async def history(ctx, *, nametag):
    check = await check_name(nametag, ctx)

    # split checkname nametag at #
    name = check[0]
    tag = check[1]

    url = "https://api.henrikdev.xyz/valorant/v3/matches/eu/" + name + "/" + tag
    response = get(url, headers=headers)

    # check if the response is valid
    if response.status_code == 200:

        json_response = json.loads(response.text)

        stats = json_response["data"]

        # send title embed
        embed = discord.Embed(title=name + "'s History", color=0x0000FF)

        # send embed
        await ctx.send(embed=embed)

        # make a for loop to get the metadata the last 5 games
        for i in range(0, 5):

            # get data from metadata
            map = stats[i]["metadata"]["map"]
            start_unix = stats[i]["metadata"]["game_start"]
            mode = stats[i]["metadata"]["mode"]

            # search for name in stats[i]['players'] and ignore capitalization
            for j in range(0, len(stats[i]["players"]["all_players"])):
                if (
                    stats[i]["players"]["all_players"][j]["name"].lower()
                    == name.lower()
                ):
                    player_stats = stats[i]["players"]["all_players"][j]
                    break
                else:
                    return

            player_team = player_stats["team"]
            player_character = player_stats["character"]
            player_character_icon = player_stats["assets"]["agent"]["small"]
            kills = player_stats["stats"]["kills"]
            deaths = player_stats["stats"]["deaths"]
            assists = player_stats["stats"]["assists"]

            # total shots hit
            total_shots_hit = (
                player_stats["stats"]["headshots"]
                + player_stats["stats"]["bodyshots"]
                + player_stats["stats"]["legshots"]
            )
            # check if total_shots_hit is 0 so it doesnt break the bot
            if total_shots_hit == 0:
                total_shots_hit = 1
            # raw hs percent
            headshot_percent_raw = player_stats["stats"]["headshots"] / total_shots_hit
            # calculate headshot_percent_raw into a percent value
            headshot_percent = str(round(headshot_percent_raw * 100, 2)) + "%"

            # check if the player has won
            if stats[i]["teams"][str(player_team).lower()]["has_won"]:
                won = True
            else:
                won = False

            # get exact score
            rounds_won = stats[i]["teams"][str(player_team).lower()]["rounds_won"]
            rounds_lost = stats[i]["teams"][str(player_team).lower()]["rounds_lost"]

            # combine the score
            score = str(rounds_won) + "-" + str(rounds_lost)

            # change embed color depending on if the player has lost or won
            if won:
                embed_color = 0x00FF00
            else:
                embed_color = 0xFF0000

            embed = discord.Embed(color=embed_color)

            # make embed
            embed.add_field(name="Map", value=map, inline=True)
            embed.add_field(name="Mode", value=mode, inline=True)
            embed.add_field(name="Time", value=f"<t:{start_unix}:R>", inline=True)
            embed.add_field(name="Team", value=player_team, inline=True)
            embed.add_field(name="Character", value=player_character, inline=True)
            embed.add_field(name="Score", value=score, inline=True)
            embed.add_field(name="Kills", value=kills, inline=True)
            embed.add_field(name="Deaths", value=deaths, inline=True)
            embed.add_field(name="Assists", value=assists, inline=True)
            embed.add_field(name="Headshots", value=headshot_percent, inline=True)
            embed.set_thumbnail(url=player_character_icon)

            await ctx.send(embed=embed)

    elif response.status_code == 404:
        # make a embed
        embed = discord.Embed(
            title="Error",
            description="The player you searched for doesn't exist",
            color=0xFF0000,
        )

        await ctx.send(embed=embed)

    else:
        # send error embed
        embed = discord.Embed(
            title="Error", description="An error occured", color=0xFF0000
        )

        await ctx.send(embed=embed)


# suggest command
@client.command()
async def suggest(ctx, *, suggestion):

    # connect to todoist api
    TODOIST_TOKEN = os.getenv("TODOIST_TOKEN")
    todoist = TodoistAPI(TODOIST_TOKEN)

    # add a task to todoist
    try:
        todoist.add_task(content=suggestion, project_id=2292334118)

        # send embed suggestion added
        embed = discord.Embed(
            title="Suggestion Added",
            description="Your suggestion has been added to the todoist list",
            color=0x0000FF,
        )

        await ctx.send(embed=embed)

    except Exception as error:
        # your suggestion could not be added to todoist
        embed = discord.Embed(
            title="Error",
            description="Your suggestion could not be added to todoist",
            color=0xFF0000,
        )

        await ctx.send(embed=embed)


# add a link command
@client.command()
async def link(ctx, *, link):

    # connect to database players database
    conn = sqlite3.connect("players.db")
    c = conn.cursor()

    # create players table if it doesnt exist with the following columns: discord_name, ingame_name, rank_int
    c.execute(
        """CREATE TABLE IF NOT EXISTS players (discord_name text, ingame_name text, rank_int int)"""
    )

    # split link at #
    link_split = link.split("#")

    name = link_split[0]
    tag = link_split[1]

    # get the rank of the player
    url = "https://api.henrikdev.xyz/valorant/v1/mmr/eu/" + name + "/" + tag
    response = get(url, headers=headers)

    json_response = json.loads(response.text)

    # if respone is 200 the player exists
    if response.status_code == 200:
        print(json_response)
        rank = int(json_response["data"]["currenttier"])

        # check if the player isnt already in the database
        c.execute("""SELECT * FROM players WHERE discord_name = ?""", (ctx.author.id,))
        result = c.fetchone()

        # if the player isnt in the database
        if result == None:
            # add the player to the database
            c.execute(
                """INSERT INTO players (discord_name, ingame_name, rank_int) VALUES (?, ?, ?)""",
                (ctx.author.id, link, rank),
            )
            conn.commit()

            # make embed
            embed = discord.Embed(
                title="Link Added",
                description="Your accounts have been linked",
                color=0x00FF00,
            )

            await ctx.send(embed=embed)

        else:
            # make embed
            embed = discord.Embed(
                title="Error",
                description="Your account is already linked",
                color=0xFF0000,
            )

            await ctx.send(embed=embed)

    else:
        # make embed
        embed = discord.Embed(
            title="Error",
            description="The Valorant account name you entered does not exist",
            color=0xFF0000,
        )

        await ctx.send(embed=embed)

    # close database
    conn.close()


# unlink command
@client.command()
async def unlink(ctx):
    # connect to databse
    conn = sqlite3.connect("players.db")
    c = conn.cursor()

    # check if the player is in the database
    c.execute("""SELECT * FROM players WHERE discord_name = ?""", (ctx.author.name,))
    result = c.fetchone()

    # if the player is in the database
    if result != None:
        # delete the player from the database
        c.execute("""DELETE FROM players WHERE discord_name = ?""", (ctx.author.name,))
        conn.commit()

        # make embed
        embed = discord.Embed(
            title="Link Removed",
            description="Your accounts have been unlinked",
            color=0x00FF00,
        )

        await ctx.send(embed=embed)

    else:
        # make embed
        embed = discord.Embed(
            title="Error", description="Your account is not linked", color=0xFF0000
        )

        await ctx.send(embed=embed)

    # close database
    conn.close()


# looking for players command
@client.command()
async def looking(ctx, stacksize_str=5):
    # check if the author is in players database
    conn = sqlite3.connect("players.db")
    c = conn.cursor()

    c.execute("""SELECT * FROM players WHERE discord_name = ?""", (ctx.author.id,))
    result = c.fetchone()

    players_messaged_list = []
    players_found_list = []
    players_denied_list = []

    players_found = 0

    # convert stacksize to int
    stacksize = int(stacksize_str)

    # if the author is in the database
    if result != None:
        if stacksize < 5 and stacksize > 0:
            # check for other players online whose rank_int is at max 3 off the players rank
            c.execute(
                """SELECT * FROM players WHERE rank_int - ? <= 3 OR rank_int - ? >= 3""",
                (
                    result[2],
                    result[2],
                ),
            )
            result = c.fetchall()

            # check if players in result are online on discord
            for player in result:
                check_member = ctx.guild.get_member(int(player[0]))

                # if the user is online and isnt the message author
                if (
                    str(check_member.status) == "online"
                    and check_member.id != ctx.author.id
                ):

                    member = ctx.guild.get_member(int(player[0]))
                    user = client.get_user(member.id)
                    rank = player[1]

                    # add to players_messaged_list
                    players_messaged_list.append(user)

                    players_found += 1

                    # make an embed to dm to the player
                    embed = discord.Embed(
                        title="Player Found",
                        description="<@!"
                        + str(ctx.author.id)
                        + "> is looking to play VALORANT with a team with a stack size of "
                        + str(stacksize)
                        + ". To play with him react with .",
                        color=0x00FF00,
                    )

                    # add footer
                    embed.set_footer(
                        text="You are getting this message because you linked your VALORANT-Account in the NERD Universe server. To stop these messages please use the .unlink command"
                    )

                    # send the embed as dm
                    dm = await user.send(embed=embed)
                    await dm.add_reaction("\u2705")
                    await dm.add_reaction("\u274C")

                    # start a threaded loop that checks for reactions
                    async def check_reactions():
                        cache_dm = discord.utils.get(client.cached_messages, id=dm.id)
                        counter = 0
                        while True:
                            await asyncio.sleep(1)
                            counter += 1
                            # check if the message has been reacted to
                            if cache_dm.reactions:
                                # check if the message has been reacted with the accept emoji
                                if cache_dm.reactions[0].count == 2:

                                    # check if the message has been reacted with the deny emoji
                                    await dm.delete()

                                    # add the player to the players_found_list
                                    players_found_list.append(user)

                                if cache_dm.reactions[1].count == 2 or counter == 300:
                                    # delete the message
                                    await dm.delete()

                                    # add user to list of denied players
                                    players_denied_list.append(user)

                    async def check_list():
                        while True:
                            await asyncio.sleep(3)
                            # if players_found is the same size as the stacksize exit the loop
                            if (
                                len(players_found_list) >= int(stacksize) - 1
                            ):  # enough players accepted
                                # all players found

                                # check if there are players in players_messages_list that arent in players_found_list
                                for player in players_messaged_list:
                                    if player not in players_found_list:
                                        # message the player that they were denied (embed)
                                        embed = discord.Embed(
                                            title="Denied!",
                                            description="You were denied because you didnt react to the message in time",
                                            color=0xFF0000,
                                        )

                                        # send the embed
                                        await player.send(embed=embed)
                                    else:
                                        pass

                                embed = discord.Embed(
                                    title="Players found!",
                                    description="The following players have been found to queue with:",
                                    color=0x00FF00,
                                )

                                # add fields
                                for player in players_found_list:
                                    embed.add_field(
                                        name=rank,
                                        value="<@!" + str(player.id) + ">",
                                        inline=False,
                                    )

                                # footer
                                embed.set_footer(
                                    text="Please meet up in a VALORANT-Lobby"
                                )

                                # send embed
                                await ctx.send(embed=embed)

                                break

                            elif int(stacksize) - 1 <= len(
                                players_denied_list
                            ):  # to many players denied
                                # embed not enough players found
                                embed = discord.Embed(
                                    title="Not enough players found!",
                                    description="Too many players denied your request. Please try a lower stack size. (online players: "
                                    + str(len(players_found_list))
                                    + ")",
                                    color=0xFF0000,
                                )

                                # send embed
                                await ctx.send(embed=embed)

                                conn.close()

                                break

                    # threaded loop
                    asyncio.run_coroutine_threadsafe(check_reactions(), client.loop)
                    # another one of these threads will be running the  check_lists function
                    asyncio.run_coroutine_threadsafe(check_list(), client.loop)

            # if players_found is one less than wished stacksize
            if players_found == int(stacksize) - 1:
                # send a dm to ever player
                # send a message that players are found
                embed = discord.Embed(
                    title="Players Found",
                    description="There are "
                    + str(players_found)
                    + " players online which you could queue with. They have been notified via DM",
                    color=0x00FF00,
                )

                await ctx.send(embed=embed)

            else:
                # embed not enough players found
                embed = discord.Embed(
                    title="Not enough players found!",
                    description="Not enough players online. Please try a lower stack size. (online players: "
                    + str(len(players_found_list))
                    + ")",
                    color=0xFF0000,
                )

                # send embed
                await ctx.send(embed=embed)

        else:
            # stacksize is not valid embed
            embed = discord.Embed(
                title="Error",
                description="The stacksize you entered is not valid",
                color=0xFF0000,
            )

            await ctx.send(embed=embed)

    else:
        # embed you have to link your account
        embed = discord.Embed(
            title="Error",
            description="You have not linked your Valorant account to Discord yet. Please do so by using the .link command",
            color=0xFF0000,
        )

    # cleanup
    conn.close()


client.run(os.getenv("TOKEN"))
