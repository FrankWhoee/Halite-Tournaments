import discord
import asyncio
import os
import json
import funcs
import settings

client = discord.Client()
path = os.path.dirname(os.path.realpath(__file__))

commands = {"!help":"Show this message",
            "!submit":"Select your file and write this as a comment to submit your bot, you this in the season-"+settings.season+" to submit for the tournament",
            "!rules":"Display the rules of the current tournament",
            "!brackets":"Check current brackets",
            "!matches":"Print upcoming matches, tag a user after to check his upcoming matches",
            "!submissions":"Check if submissions are opened/closed and when they close/open",
            "!languages":"Check supported languages for submissions, add a language name to know how it's compiled/run e.g. !language python",
            "!battle":"Run a match between two players, !battle [p1] [p2] [height map] [width map]",
            "!donations":"Get infos about donations"}

adminCommands = {"!subs":"!subs True/False opens or closes submissions",
                 "!brk":"To add as a comment with the brackets image to update it",
                 "!clear":"!clear [n of message to delete] [channel, use * to select current]",
                 "!type":"!type [message to make the HTBot type]",
                 "!post":"!post [path to file in the server] [channel, se * to Select current] to post a file from the server",
                 "!ontour":"!ontour True/False to change the current tournament status",
                 "!admin":"Print this message",
                 "!time":"Change time of submissions"}

@client.event
async def on_ready(): #startup
    print("Bot "+client.user.name+" ready to operate!")
    print("-------")

@client.event
async def on_message(message):
    try :
        if message.content.startswith("!submit"):
            if not settings.submit : #if the submissions are closed
                await client.delete_message(message)
                await client.send_message(message.channel, "**Submissions are closed at the moment!** "+message.author.mention)
            else:
                if str(message.channel) != "season-"+settings.season and str(message.channel) != "battles": #if message is in the wrong channel
                    await client.delete_message(message)
                    await client.send_message(message.channel, "**Cannot use this command in this channel!** "+message.author.mention)
                else:
                    try:
                        await client.send_message(message.channel, "`Submitting, compiling and testing your bot...` "+message.author.mention)
                        response, compileLog = await funcs.uploadBot(message.attachments[0].get('url'), str(message.author), message.attachments[0].get('filename'))
                        await client.delete_message(message)
                        await client.send_message(message.channel, "`"+response+"` "+message.author.mention)
                        if compileLog != "": #if compiled and run successfully
                            await client.send_message(message.author, "**Here your compile and run log for yout bot submission!**")
                            await client.send_file(message.author, compileLog)

                    except IndexError : #no attachments present
                        await client.send_message(message.channel, "`No attachment present!` "+message.author.mention)


        elif message.content.startswith("!submissions"): #check submissions
            if settings.submit:
                s, s2 = "opened", "close"
            else :
                s, s2 = "closed", "open"
            await client.send_message(message.channel, "**Current status of submissions : "+s+", the submissions will "+s2+" at : "+settings.timeSub+"**")

        elif message.content.startswith("!help"): #help function
            text = "```\n"
            for k,c in sorted(commands.items()):
                text += k + " : " + c + "\n"
            text += "```"
            await client.send_message(message.channel, text)

        elif message.content.startswith("!rules"): #print info about the tournament
            if settings.onTour:
                try :
                    with open(settings.infos, "r") as f:
                        infos = f.read()
                        infos = infos.replace("\\n","\n")
                        await client.send_message(message.channel, infos)

                except FileNotFoundError:
                    await client.send_message(message.channel, "**Rules for current tournament are not ultimated!**")
            else:
                await client.send_message(message.channel, "**No tournament currently ongoing!**")


        elif message.content.startswith("!matches"): #check upcoming matches
            if settings.onTour: #if we are running in a tournament
                m = str(message.content).split()
                if len(m) == 1: #check all matches
                    text = "**Here are the upcoming matches!**\n\n"
                    for k,v in sorted(settings.matches.items()):
                        text += "**" + k + "** : \n"
                        for p in v:
                            text += "\t" + p + "\n"

                else: #check specific matches for player
                    t = ""
                    player = ""
                    try :
                        player = str(message.mentions[0])

                    except IndexError:
                        text = "**Wrong formatting! Check `!help` for more info**"

                    if player != "":
                        for k,v in sorted(settings.matches.items()):
                            for p in v:
                                if player in p:
                                    t += "**" + k + "** : \n"
                                    t += "\t" + p + "\n"

                    if t != "":
                        text = "**Here are all the matches of : "+m[1]+"**\n"+t

                    elif player != "" and t == "" :
                        text = "**No matches scheduled for : "+m[1]+" !**"

            else :
                text = "**No scheduled matches!**"

            await client.send_message(message.channel, text)

        elif message.content.startswith("!battle"):
            #if we are in a tournament and in the right channel
            if settings.onTour and str(message.channel) == "battles" :
                try:
                    #get the two players from mentions
                    p1 = str(message.mentions[0])
                    p2 = str(message.mentions[1])
                    try :
                        #get the map sizes
                        width = message.content.split()[3]
                        height = message.content.split()[4]

                    except ValueError: #if there is a problem set default size
                        width = "240"
                        height = "160"

                    await client.send_message(message.channel, "*Running battle...* <:logo:416779058924355596>")
                    status, result, log1, log2, replay = await funcs.battle(p1, p2, width, height, False)
                    await client.send_message(message.channel, status)

                    if result != "": #if we have an output
                        await client.send_message(message.channel, result)
                        if replay != "":
                            await client.send_file(message.channel, replay)
                        #check if logs are present and send them
                        if log1 != "":
                            await client.send_message(message.mentions[0], "**Here is the logfile of your bot : (timstamp battle : "+funcs.getTime()+")**")
                            await client.send_file(message.mentions[0], log1)
                            os.remove(log1)
                        if log2 != "":
                            await client.send_message(message.mentions[1], "**Here is the logfile of your bot : (timstamp battle : "+funcs.getTime()+")**")
                            await client.send_file(message.mentions[1], log2)
                            os.remove(log2)

                except IndexError : #formatting error
                    await client.send_message(message.channel, "**Bad formatting! Run !help for info about commands**")

            elif str(message.channel) != "battles": #wrong channel!
                battles = discord.utils.get(client.get_all_channels(), server__name=settings.serverName, name='battles')
                await client.send_message(message.channel, "**Run this in the "+battles.mention+" channel!**")

            else: #tournament is closed
                await client.send_message(message.channel, "**Feature not avaible at the moment!**")


        elif message.content.startswith("!brackets"): #get current brackets
            if settings.onTour:
                try:
                    await client.send_file(message.channel, settings.brackets)

                except:
                    await client.send_message(message.channel, "**Brackets are not up yet!**")

            else : #if no tournament is running
                await client.send_message(message.channel, "**No tournament currently ongoing!**")

        elif message.content.startswith("!languages"): #send all supported languages
            m = message.content.split()
            if len(m) == 1:
                t = "**Here are the languages supported for your bot:**\n\n"
                for l in sorted(funcs.languages.keys()):
                    t += l+", "
                t += "\n\nIf your language is **not supported** compile it in a `MyBot` file, or dm Splinter if you have problems"

            else:
                t = ""
                for k,v in funcs.languages.items():
                    if m[1] == k:
                        if v[1] == "" :
                            v[1] = "Not necessary"

                        t += "**File extension : **`"+v[0]+"`, **Compile command : **`"+v[1]+"`, **Run command : **`"+v[2]+"`"

                        if m[1] == "python":
                            t+= "\n\n**External libraries installation command : **`pip3 install -r requirements.txt`"
                        break

                if t == "":
                    t = "**Language not supported!**"

            await client.send_message(message.channel, t)

        elif message.content.startswith("!donations"):
            text = "Donations are used to help support Halite Tournaments. We use your contributions to run our servers and give cash prizes. Donate here: https://www.paypal.me/HaliteTournaments. Donating will give you the **Contributor** role which has access to the Contributors voice channel. More privileges for Contributors will be coming!"
            await client.send_message(message.channel, text)
        #admin commands
        elif str(message.author) in settings.admins:
            if message.content.startswith("!type"): #make bot type in current channel
                await client.delete_message(message)
                await client.send_message(message.channel, str(message.content).replace("!type", ""))

            elif message.content.startswith("!match"):
                if settings.onTour :
                    try:
                        #get the two players from mentions
                        p1 = str(message.mentions[0])
                        p2 = str(message.mentions[1])

                        await client.send_message(message.channel, "*Running match...*")
                        status, result, _, _, replay = await funcs.battle(p1, p2, "", "", True)
                        await client.send_message(message.channel, status)

                        if result != "": #if we have an output
                            await client.send_message(message.channel, result)
                            if replay != "":
                                await client.send_file(message.channel, replay)

                    except IndexError : #formatting error
                        await client.send_message(message.channel, "**Bad formatting! Run !help for info about commands**")

                else :
                    await client.send_message(message.channel, "**Feature not avaible at the moment!**")

            elif message.content.startswith("!admin"): #print admin commands
                text = "```\n"
                for k,c in sorted(adminCommands.items()):
                    text += k + " : " + c + "\n"
                text += "```"
                await client.send_message(message.channel, text)

            elif message.content.startswith("!clear"): #delete n messages in a channel
                try :
                    n = int(message.content.split()[1]) #number of messages
                    ch = message.content.split()[2] #channel
                    if ch != "*": #current channel
                        channel = discord.utils.get(client.get_all_channels(), server__name=settings.serverName, name=ch)
                    else :
                        channel = message.channel
                    await client.purge_from(channel, limit=n)

                except IndexError:
                    await client.send_message(discord.utils.get(client.get_all_channels(), server__name=settings.serverName, name='halite'), "**Wrong command formatting**")

            elif message.content.startswith("!post"): #upload a file from server to channel
                try :
                    await client.delete_message(message)
                    c = message.content.replace("!post", "")
                    f, ch = c.split()[0], c.split()[1]
                    if ch != "*":
                        channel = discord.utils.get(client.get_all_channels(), server__name=settings.serverName, name=ch)
                    else :
                        channel = message.channel
                    await client.send_file(channel, f, content=c.replace(f+" "+ch, ""))

                except FileNotFoundError:
                    s = funcs.log("File "+f+" not found!")
                    await client.send_message(discord.utils.get(client.get_all_channels(), server__name=settings.serverName, name='halite'), s)

                except IndexError :
                    await client.send_message(discord.utils.get(client.get_all_channels(), server__name=settings.serverName, name='halite'), "**Wrong command formatting**")

            elif message.content.startswith("!subs"): #change submissions status
                s = message.content.replace("!subs", "").split()
                if s != "":
                    try:
                        boo = funcs.str_to_bool(s[0])
                        with open("settings.json", "r") as f:
                            g = json.load(f)
                            g.update({'submit':boo})

                        with open("settings.json", "w") as f:
                            json.dump(g, f, indent="\t")

                        with open("env/run.txt", "w") as f:
                            if boo:
                                f.write("1")
                            else :
                                f.write("0")

                        settings.submit = boo
                        await client.send_message(message.channel, "**Setting : "+s[0]+" in submissions**")

                    except IndexError :
                        await client.send_message(message.channel, "!submissions")

                else :
                    await client.send_message(message.channel, "!submissions")

            elif message.content.startswith("!ontour"): #chane onTour status
                s = message.content.replace("!ontour", "").split()
                if s != "":
                    boo = funcs.str_to_bool(s[0])
                    with open("settings.json", "r") as f:
                        g = json.load(f)
                        g.update({'onTour':boo})

                    with open("settings.json", "w") as f:
                        json.dump(g, f, indent="\t")

                    settings.onTour = boo
                    await client.send_message(message.channel, "**Setting : "+s[0]+" in onTour**")

                else :
                    await client.send_message(message.channel, "**Invalid command**")

            elif message.content.startswith("!brk"): #upload new file to brackets
                try :
                    os.system('wget -q -O '+settings.brackets+' ' + message.attachments[0].get('url'))
                    await client.send_message(message.channel, "**Brackets updated**")
                except:
                    await client.send_message(message.channel, "**Error while uploading the brackets**")

            elif message.content.startswith("!time"):
                t = message.content.replace("!time", "")
                if t != "":
                    with open("settings.json", "r") as f:
                        g = json.load(f)
                        g.update({'timeSub':t})

                    with open("settings.json", "w") as f:
                        json.dump(g, f, indent="\t")

                    settings.timeSub = t
                    await client.send_message(message.channel, "**Setting : "+t+" in timeSub**")

                else:
                    await client.send_message(message.channel, "**Invalid command**")

    except Exception as e:
        s = funcs.log(str(e))
        await client.send_message(discord.utils.get(client.get_all_channels(), server__name=settings.serverName, name='halite'), s)

@client.event
async def on_member_join(member):
    channel = discord.utils.get(client.get_all_channels(), server__name=settings.serverName, name='announcements')
    funcs.log("Member joined : "+str(member))
    await client.send_message(discord.utils.get(client.get_all_channels(), server__name=settings.serverName, name='general'),
        "Welcome "+member.mention+" to Halite Tournaments! Check out the section "+channel.mention+" for information about the upcoming tournaments! <:logo:416779058924355596>")

if settings.token == "":
    token = str(input("Insert token for bot : "))
    settings.token = token

if settings.serverName == "":
    name = str(input("Insert name of operating server : "))
    settings.serverName = name

client.run(settings.token)
