# simulate old F1 races using Gemini AI
#
import irc.client
from google import genai
from google.genai import types, errors
import time
import os
import configparser
import sys

with open('e:/ai/genai_api_key.txt') as file:
    api_key = file.read().strip()
client = genai.Client(api_key=api_key)

chats = {}

def load_config(config_file=sys.argv[1]):
    try:
        config = configparser.ConfigParser()
        config.read(config_file)

        server_info = {
            'server': config['IRCServer']['server'],
            'port': int(config['IRCServer']['port'])
        }

        general_info = {
            'nick': config['General']['nick']
        }

        specifics_info = {
            'sysprompt': config['Specifics']['sysprompt']
        }
        channels_str = config['General']['channels']
        channels_str = channels_str.strip('[]')
        channels = [ch.strip().strip("'\"") for ch in channels_str.split(',')]
        general_info['channels'] = channels


        return {
            'server': server_info,
            'general': general_info,
            'specifics': specifics_info
        }

    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing required configuration key: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

config = load_config()

print("=== IRC Bot Configuration ===")
print(f"Server: {config['server']['server']}")
print(f"Port: {config['server']['port']}")
print(f"Nickname: {config['general']['nick']}")
print(f"Channels: {config['general']['channels']}")
print(f"SysPrompt: {config['specifics']['sysprompt']}")

SERVER = config['server']['server']
PORT = config['server']['port']
NICK = config['general']['nick']
CHANNELS = config['general']['channels']
SYSPROMPT = config['specifics']['sysprompt']

def on_connect(connection, event):
    for chan in CHANNELS:
        sys_instruct = f"{SYSPROMPT}."
        chat = client.chats.create(
                model="gemini-2.0-flash-thinking-exp",
                config=types.GenerateContentConfig(system_instruction=sys_instruct),                
                )
        chats[chan] = chat
        print("Joining channel: " + chan)
        connection.join(chan)

def main():
    reactor = irc.client.Reactor()
    try:
        c = reactor.server().connect(SERVER, PORT, NICK)
        c.add_global_handler("welcome", on_connect)
        c.add_global_handler("pubmsg", on_message)
        reactor.process_forever()
    except irc.client.ServerConnectionError:
        print("Connection error")

def on_message(connection, event):
    inputtext = event.arguments[0].strip()
    inputtext2 = event.arguments[0].strip()
    inputtext = event.source.nick + ": " + inputtext
    chan = event.target
    logging(event, inputtext)
    if event.arguments[0][:len(NICK)].lower().strip() == NICK.lower():
        if event.arguments[0].find("!start") != -1:
            start_race(event, connection)
            return
    
def start_race(event, connection):
# setup race
    chan = event.target
    if chan in chats:
        response = chats[chan].send_message("Set up the race.  Include the track, weather, top 10 grid positions, number of laps and any other relevant details.")
        para_text = response.text.splitlines()
        nonempty_para_text = [line for line in para_text if line.strip()]
        for paragraph in nonempty_para_text:
            output = remove_lfcr(paragraph)
            output = output[:450]
            print(output)
            connection.privmsg(event.target,output)        
            time.sleep(2)
        time.sleep(2)
        connection.privmsg(event.target,"***** RACE ABOUT TO START *****")
        time.sleep(3)
        response = chats[chan].send_message("The race starts.  Simulate lap 1.  Include the lap time, position changes, and any incidents.")
        para_text = response.text.splitlines()
        nonempty_para_text = [line for line in para_text if line.strip()]
        for paragraph in nonempty_para_text:
            output = remove_lfcr(paragraph)
            output = output[:450]
            print(output)
            connection.privmsg(event.target,output)        
            time.sleep(4)
        time.sleep(2)
        lap_roundup(event, connection,chan)
        while True:
            time.sleep(2)
            if do_lap(event, connection, chan) == "STOP":
                break
            time.sleep(2)
            lap_roundup(event, connection, chan)
            time.sleep(2)

def remove_lfcr(text):
    return text.replace("\n"," ").replace("\r"," ")

def logging(event, inputtext):
    print(event.target + ":" + event.source.nick + ": " + event.arguments[0])
    print(event.target + ":" + event.source.nick + ": " + inputtext)

def lap_roundup(event, connection, chan):
        connection.privmsg(event.target,"***** LAP Roundup *****")
        time.sleep(3)
        response = chats[chan].send_message("Give the current lap number, top 10 positions and lap times including gaps to the driver in behind.")
        para_text = response.text.splitlines()
        nonempty_para_text = [line for line in para_text if line.strip()]
        for paragraph in nonempty_para_text:
            output = remove_lfcr(paragraph)
            output = output[:450]
            print(output)
            connection.privmsg(event.target,output)        
            time.sleep(1)    

def do_lap(event, connection, chan):
        connection.privmsg(event.target,"***** Next Lap *****")
        time.sleep(3)
        response = chats[chan].send_message("Give the current lap number and Simulate the lap continuing from the previous one.  Include the lap time, position changes, and any incidents.  If the race has finished only reply with STOP")
        end_race = response.text.splitlines()
        if end_race[0].find("STOP") != -1: 
            connection.privmsg(event.target,"***** RACE FINISHED *****")
            do_after_race(event, connection, chan)
            return("STOP")
        para_text = response.text.splitlines()
        nonempty_para_text = [line for line in para_text if line.strip()]
        for paragraph in nonempty_para_text:
            output = remove_lfcr(paragraph)
            output = output[:450]
            print(output)
            connection.privmsg(event.target,output)        
            time.sleep(5)  

def do_after_race(event, connection, chan):
        connection.privmsg(event.target,"***** AFTER THE RACE *****")
        time.sleep(3)
        response = chats[chan].send_message("Give a roundup of the results and celebration.")
        end_race = response.text.splitlines()
        if end_race[0].find("STOP") != -1: 
            connection.privmsg(event.target,"***** RACE FINISHED *****")
            do_after_race(event, connection)
            return
        para_text = response.text.splitlines()
        nonempty_para_text = [line for line in para_text if line.strip()]
        for paragraph in nonempty_para_text:
            output = remove_lfcr(paragraph)
            output = output[:450]
            print(output)
            connection.privmsg(event.target,output)        
            time.sleep(3) 
        quit() 

if __name__ == "__main__":
    main()
