import os
import datetime
import zipfile
import settings
import time
import random

languages = {'python': ['py', '', 'python3 MyBot.py'],
 'java': ['java', 'javac MyBot.java', 'java MyBot'],
 'rust': ['rs', 'cargo rustc --release -q -- -Awarnings', 'target/release/MyBot'],
 'javascript': ['js', '', 'node MyBot.js'],
 'c++': ['cpp', 'set -e && cmake . && make MyBot', './MyBot'],
 'dart': ['dart', '', 'dart MyBot.dart'],
 'go': ['go', 'export GOPATH=$(pwd) && go get || go build MyBot.go', './MyBot'],
 'haskell': ['hs', 'ghc --make MyBot.hs -O -v0 -rtsopts -outputdir dist', './MyBot.exe'],
 'ruby': ['rb', '', 'ruby MyBot.rb']}

def log(string):

    """
    A simple log function
    """

    string = "Timestamp: - "+getTime()+" "+ string
    with open(settings.logFile, 'a') as (out):
        out.write(string + '\n')
    return '**' + string + '**'

def getTime():

    """
    Function to get and format current time, just to
    speed things up
    """

    return ('{:%Y-%m-%d %H:%M:%S}').format(datetime.datetime.now())

def str_to_bool(s):

    """
    Helper function to handle json settings
    """

    if s == 'True':
        return True
    if s == 'False':
        return False


def uploadBot(link, username, fileName):

    """
    Function that downloads zip file, unzips it,
    recognize the language used and runs the
    compiler function
    """

    username = username.replace(' ', '')
    save = settings.path + '/bots/' + username + '/'
    try:
        os.system('rm -r '+save+" > /dev/null 2>&1")
        os.mkdir(save)
        if fileName[-4:] == '.zip':
            os.system('wget -q -O ' + save + fileName + ' ' + link)
            if fileName[-4:] == '.zip':
                z = zipfile.ZipFile(save + fileName, 'r')
                z.extractall(save)
                z.close()

            ext = None
            found = False
            for f in os.listdir(save):
                if f.startswith('MyBot.'):
                    ext = f.replace('MyBot.', '')
                    for k, v in languages.items():
                        if ext == v[0]:
                            found = True
                            break

                elif f.startswith("src"):
                    for s in os.listdir(save+"src/"):
                        if s == "MyBot.go":
                            ext = "go"
                            found = True
                            break
                        elif s == "main.rs":
                            ext = "rs"
                            found = True
                            break
                if found:
                    break


            compileLog = ""
            if ext != None and found:
                c, compileLog = compileBot(save, ext, username)
                if c:
                    text = 'File bot : ' + fileName + ' ,  submitted, compiled and run successfully! Sending log file...'
                else:
                    text = 'File bot : ' + fileName + ' ,  submitted but encountered an error compiling/running! Sending log file...'
            elif ext != None and not found:
                text = 'File bot : ' + fileName + ' conatins a bot file but the language : '+ext+' isn\'t supported!'
            elif ext == None:
                text = 'File bot : ' + fileName + ' does not contain a **MyBot** file of any type!'

            log(text)
            return False, text, compileLog

        return False, "File wasn't a .zip file, check the rules!"
    except Exception as e:
        s = log(str(e))
        return True, s, ""


def compileBot(save, ext, user):

    """
    Function that writes bot name to compilerQueue
    and waits for output.
    """

    compileLog = settings.path+"/bots/out/"+user+".txt"
    os.system("rm "+compileLog+" > /dev/null 2>&1")
    for k, v in languages.items():
        if ext == v[0]:
            with open(save + "lang.txt", 'w') as f:
                f.write(v[1] + '\n' + v[2])
            with open(settings.path + "/bots/compilerQueue.txt", 'a') as q:
                q.writelines(user)
            break

    secs = 0
    while secs <= settings.compileOut:
        try:
            with open(compileLog, "r") as f:
                status = f.read().splitlines(True)[-1]

            if status.startswith("successful"):
                return True, compileLog
            else :
                break

        except FileNotFoundError:
            time.sleep(1)
            secs += 1

    return False, compileLog

def battle(p1, p2, width, height, official):

    """
    Battle function to interact with the battle
    enviroment.
    p1 = player one, string
    p2 = player two, string
    height = height of the map of game, string
    width = width of the map game, start
    official = if it's an official tournament match or not, bool
    Return variables :
    status = message to send on the channel, string
    result = files to return on the channel, [string, string]
    log1 = log file to send to player one, string
    log2 = log file to send to player two, string
    """

    p1 = p1.replace(' ', '')
    p2 = p2.replace(' ', '')
    p1Ava = os.path.isdir(settings.path+"/bots/"+p1)
    p2Ava = os.path.isdir(settings.path+"/bots/"+p2)
    log1 = ""
    log2 = ""
    result = ""
    replay = ""
    status = ""
    battleName = p1+"VS"+p2

    if p1Ava and p2Ava :
        os.system("rm "+settings.path+"/bots/out/"+battleName+"/* > /dev/null 2>&1")
        if not official:
            with open(settings.path+"/bots/"+"runQueue.txt", "a") as f:
                command = p1+" "+p2+" "+width+" "+height
                f.writelines(command)

            secs = 0
            while secs <= settings.runOut: #time same as bots/handler.py
                if os.path.exists(settings.path+"/bots/out/"+battleName+"/battle.log"):
                    with open(settings.path+"/bots/out/"+battleName+"/battle.log", "r") as l:
                        result = "```"+l.read()+"```"
                    if os.path.exists(settings.path+"/bots/out/"+battleName+"/battle.hlt"):
                        replay = settings.path+"/bots/out/"+battleName+"/battle.hlt"
                        for f in os.listdir(settings.path+"/bots/"+p1):
                            if f.endswith(".log"):
                                log1 = settings.path+"/bots/"+p1+"/"+f
                        for f in os.listdir(settings.path+"/bots/"+p2):
                            if f.endswith(".log"):
                                log2 = settings.path+"/bots/"+p2+"/"+f
                            status = "**Battle ran successfully, here is the replay and halite output. Sending log files of players in DM...**"
                    else:
                        status = "**Error while running the battle, here is the halite output.**"

                    return status, result, log1, log2, replay

                else:
                    time.sleep(1)
                    secs += 1

            status = "**Battle took too much time! Max is "+str(settings.runOut)+"s**"

        else:
            runs = 5
            with open(settings.path+"/bots/runQueue.txt", "a") as f:
                command = "official "+p1+" "+p2
                f.writelines(command)

            secs = 0
            while secs <= settings.runOut*runs:
                if os.path.exists(settings.path+"/bots/out/"+battleName+"/battle.log"):
                    with open(settings.path+"/bots/out/"+battleName+"/battle.log", "r") as l:
                        result = "```"+l.read()+"```"

                    if os.path.exists(settings.path+"/bots/out/"+battleName+"/"+str(runs)+".hlt"):
                        replay = settings.path+"/bots/out/"+battleName+"/match.zip"
                        status = "**Match ran successfully, here are the results and the replays.**"
                    else:
                        status = "**Error while running the match, here is the halite output.**"

                    return status, result, log1, log2, replay

                else:
                    time.sleep(1)
                    secs += 1

            status = "**Battle took too much time! Max is "+str(settings.runOut*runs)+"s**"

    else:
        status = "**Error setting up the battle! Submissions state :** ***"+p1+"="+str(p1Ava)+" "+p2+"="+str(p2Ava)+"***"

    return status, result, log1, log2, replay
