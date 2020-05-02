import vlc, pafy # to handle video playing
import sys # for sys.exit() in version checking
import threading # a thread is created to endlessly listen for incoming socket commands from the server
import re # regex matching required for navigating video timestamps
import socket # for server communication

#=========================<Important globals>===================================

DEFAULT_NAV = 10 # how many seconds to move forward/back as a default
SERVER = "" # where to connect to
SERVER_PORT = "" # where to connect to, more specifically
#SOCK = "" # socket to listen to
PAUSE_AUTO = "" # should new videos be paused automatically for this session?
NEW_USER_NOTIFY = "" # do you want to be notified when a new user joins the session?
PLAYBACK_NOTIFY = "" # do you want to be notified about when other users are managing the video?
SETTINGS_NOTIFY = "" # do you want to be notified when someone changes their username/edits server-wide settings?
USERNAME = "" # display name
CURRENT_URL = "" # what video is playing?
MEDIA_PLAYER = "" # VLC session to keep track of!

#=========================<Help messages>=======================================

def print_simple_help():
    print("----> type \"play <youtube URL>\" to load up a new video URL for everybody")
    print("----> type \"pause\" to pause a playing video for everybody")
    print("----> type \"resume\" to resume a paused video for everybody")
    print("----> type \"nav-forward\" to jump forwards by " + str(DEFAULT_NAV) + " seconds, or \"nav-forward <number>\" to jump forwards by <number> seconds for everybody")
    print("----> type \"nav-back\" to jump back by " + str(DEFAULT_NAV) + " seconds, or \"nav-back <number>\" to jump back by <number> seconds for everybody")
    print("----> type \"nav-to <format>\" to jump to a specific timestamp of the video for everybody")
    print("------> type the format in terms of \"__h__m__s\" to specify hours, minutes, and seconds (i.e. \"nav-to 5m17s\" to go to 5:17)")
    print("----> type \"help-simple\" for this quick-reference list itself, or \"help\" for a full list of commands")

def print_full_help():
    print("--> Simple video player commands:")
    print("----> type \"play <youtube URL>\" to load up a new video URL for everybody")
    print("----> type \"pause\" to pause a playing video for everybody")
    print("----> type \"resume\" to resume a paused video for everybody")
    print("----> type \"nav-forward\" to jump forwards by " + str(DEFAULT_NAV) + " seconds, or \"nav-forward <number>\" to jump forwards by <number> seconds for everybody")
    print("----> type \"nav-back\" to jump back by " + str(DEFAULT_NAV) + " seconds, or \"nav-back <number>\" to jump back by <number> seconds for everybody")
    print("----> type \"nav-to\ <format>\" to jump to a specific timestamp of the video for everybody")
    print("------> type the format in terms of \"__h__m__s\" to specify hours, minutes, and seconds (i.e. \"nav-to 5m17s\" to go to 5:17)")
    print("----> type \"help-simple\" for a printout of just this quick-reference list")
    print("\n--> Session-wide commands:")
    print("----> type \"toggle-auto [ON|OFF]\" to set whether newly-loaded videos will start paused or not for everybody")
    print("\n--> Personal commands:")
    print("----> type \"change-username <new username to use>\" to modify your username, helpful if two people end up using the same name!")
    print("------> (you must pick a username that does not have spaces in it)")
    print("----> type \"whoami\" to get your current username")
    print("----> type \"get-url\" to get the URL of the currently playing video")
    print("----> type \"new-user-notify [ON|OFF]\" to set whether you personally will get command-line notifications of new users joining the session")
    print("----> type \"playback-notify [ON|OFF]\" to set whether you personally will get command-line notifications of other users managing the video")
    print("----> type \"settings-notify [ON|OFF]\" to set whether you personally will get command-line notifications of other users editing session-wide settings")
    print("------> (this includes timestamp navigation, playing/pausing, and loading up a new URL)")
    print("----> type \"help\" for the full list of commands, like you did just now!")
    print("----> type \"print-settings\" for a list of session-wide and personal settings that have been configured")

def print_current_settings():
    print("--> Your username: " + USERNAME)
    print("--> Current session-wide settings:")
    print("----> Automatically pausing newly loaded-up videos for everyone: " + PAUSE_AUTO)
    print("--> Current personal settings that apply to just you:")
    print("----> Notify when a new user joins the session: " + NEW_USER_NOTIFY)
    print("----> Notify when other users manage video playback: " + PLAYBACK_NOTIFY)
    print("----> Notify when other users change their username or edits session-wide settings: " + SETTINGS_NOTIFY)
    print("--> type \"help\" to see which commands you can use to edit these settings")

#=========================<Helpers>=============================================

def get_session_settings():
    # TODO TODO query for PAUSE-AUTO via 'get-pause-auto/r/n'
    #print("----> Pause new videos automatically for everybody: " + PAUSE-AUTO)

    # TODO TODO TODO anything else? (if you want to specify a video quality or go auto, etc pafy things)
    # update in help text, infinite command parsing block, notifications printout, have a global, communicate with server, etc
    pass

def configure_personal_settings():
    print("\n--> Finally, answer some questions regarding your personal login session")

    # username to transmit
    USERNAME = input("----> What username would you like to use? Pick something unique! ")

    # notifications
    notification_input = input("----> Would you like to be notified when a new user joins the session? (yes/no) ")
    if (notification_input == "yes"):
        print("------> New user notifications turned ON")
        NEW_USER_NOTIFY = "ON"
    else:
        NEW_USER_NOTIFY = "OFF"
        print("------> New user notifications turned OFF")

    notification_input = input("----> Would you like to be notified in-terminal when someone pauses, resumes, navigates, or starts a new video? (yes/no) ")
    if (notification_input == "yes"):
        print("------> Playback notifications turned ON")
        PLAYBACK_NOTIFY = "ON"
    else:
        PLAYBACK_NOTIFY = "OFF"
        print("------> Playback notifications turned OFF")

    notification_input = input("----> Would you like to be notified in-terminal when someone makes changes to the session-wide settings? (yes/no) ")
    if (notification_input == "yes"):
        print("------> Settings notifications turned ON")
        SETTINGS_NOTIFY = "ON"
    else:
        SETTINGS_NOTIFY = "OFF"
        print("------> Settings notifications turned OFF")

# does the command word have the required number of n space-separated arguments
def check_args_req(cmd_line, min_length, max_length=""):
    if (max_length == ""): # not set, i.e. not a variable-length command
        max_length = min_length

    n = len(cmd_line.split())
    if (n > max_length):
        print("** you have supplied more arguments than necessary for this command - did you mean to do something else? (type \"help\" to check)")
        return 1
    elif (n >= min_length):
        return 1
    else:
        print("** insufficient number of arguments!", end=" ")
        return 0

# checks to see if a command option is "ON" or "OFF", for commands that explicitly expect these options
def check_toggle_on_off(option):
    if (option == "ON" or option == "OFF"):
        return 1
    else:
        print("** this command only takes the argument \"ON\" or \"OFF\" (case-sensitive)")
        return 0

# verifies __h__m__s format (I am not very good at regex)
def check_timestamp_pattern(p):
    if (bool(re.match(r"^[0-9]+[smh]$", p))): # *h, *m, and *s
        return 1
    if (bool(re.match(r"^[0-9]+m[0-9]+s$", p))): # *m*s
        return 1
    if (bool(re.match(r"^[0-9]+h[0-9]+s$", p))): # *h*s
        return 1
    if (bool(re.match(r"^[0-9]+h[0-9]+m$", p))): # *h*m
        return 1
    if (bool(re.match(r"^[0-9]+h[0-9]+m[0-9]+s$", p))): # *h*m*s
        return 1

    return 0

# is a video even playing to manipulate?
def check_video():
    if (MEDIA_PLAYER == ""):
        print("** No video is currently playing")
        return 0
    else:
        return 1

#=========================<Socket interfacing>=======================================

# endlessly listen for server requests coming over the socket
def socket_handler():
    global SOCK
    while (1): # forever, within its own thread
        # receiving from socket
        c = ""
        msg = ""
        while (1):
            c = SOCK.recv(1)
            s += c
        c = SOCK.recv(1) # final \n, all commands end with \r\n

        # handling request; commands can be assumed to be correctly-typed, since they were checked before they were sent over the socket originally
        print("~~~~~~~MESSAGE FROM THE SOCKET::: " + msg)

        cmd_list = msg.split()
        cmd = cmd_list[1]

        if (cmd == "play"):
            print("* " + cmd_list[0] + " played a new URL")
            handle_play(cmd_list[2])
        elif (cmd == "pause"):
            print("* " + cmd_list[0] + " paused")
            handle_pause()
        elif (cmd == "resume"):
            print("* " + cmd_list[0] + " resumed")
            handle_resume()
        elif (cmd == "nav-forward"):
            print("* " + cmd_list[0] + " navigated forwards " + cmd_list[2] + " seconds")
            handle_nav_forward(cmd_list[2])
        elif (cmd == "nav-back"):
            print("* " + cmd_list[0] + " navigated back " + cmd_list[2] + " seconds")
            handle_nav_back(cmd_list[2])
        elif (cmd == "nav-to"):
            print("* " + cmd_list[0] + " went to " + cmd_list[2])
            handle_nav_to(cmd_list[2])

        elif (cmd == "toggle-auto"):
            print("* " + cmd_list[0] + " turned auto-pausing " + cmd_list[2])
            PAUSE_AUTO = cmd_list[2]

        elif (cmd == "change-username"):
            print("* " + cmd_list[0] + " changed their username to " + cmd_list[2])

# formulates and sends a message to the server
def send_message(m):
    print("~~~~~~~~~~~~~~~~~~~~sending message: " + m)
    SOCK.send((USERNAME + " " + m + "\r\n").encode())

#=========================<Playback commands>===================================

def handle_play(video_url):
    CURRENT_URL = video_url

    # starting in VLC
    vid = pafy.new(video_url)
    best = vid.getbest()
    new_media_player = vlc.MediaPlayer(best.url)
    #if (not new_media_player.will_play()):
    #    print("** Unable to play the video at the specified URL (is it a YouTube link? do you have VLC installed? are you doing this in an SSH client?)")
    #    return 0
    MEDIA_PLAYER = new_media_player
    MEDIA_PLAYER.play()
    return 1

def handle_pause():
    if (not check_video()):
        return
    if (MEDIA_PLAYER.get_state == vlc.State.Paused):
        print("** Video is already paused")
        return
    MEDIA_PLAYER.pause()

def handle_resume():
    if (not check_video()):
        return
    if (MEDIA_PLAYER.get_state == vlc.State.Playing):
        print("** Video is already playing/resumed")
        return
    MEDIA_PLAYER.pause() # VLC's library resumes a paused video is pause() is called again

def handle_nav_forward(t):
    if (not check_video()):
        return
    if (t < 0):
        print("** Error, negative value not expected")
        return

    # TODO TODO

def handle_nav_back(t):
    if (not check_video()):
        return
    if (t < 0):
        print("** Error, negative value not expected")
        return

    # TODO TODO

def handle_nav_to(time_format):
    if (not check_video()):
        return

    # starting in VLC
    vid = pafy.net(CURRENT_URL + "?t=" + t)
    best = vid.getbest()
    new_media_player = vlc.MediaPlayer(best.url)
    #if (not new_media_player.will_play()):
    #    print("** Unable to play the video at the specified URL (is it a YouTube link? do you have VLC installed? are you doing this in an SSH client?)")
    #    return 0
    MEDIA_PLAYER = new_media_player
    MEDIA_PLAYER.play()
    return 1

#=========================<Main>================================================

def main():
    global SOCK
    # version checking - very important, since python2 uses raw_input() for I/O and python3 uses input()
    if sys.version_info[0] < 3:
        print("--> Error: you must use python3 to run COVIDeo")
        sys.exit()

    # introductory block text
    print("=== Welcome to COVIDeo! ===")
    print("** IMPORTANT: COVIDeo requires VLC Media Player, a freeware video playing application, to be installed on your device (https://www.videolan.org/vlc/) **")
    print("--> Thank you for choosing our application in these trying times!")
    print("\n--> First, type in which server you wish to contact.")
    print("----> (type \"default\" for the default input of 'mc18.cs.purdue.edu' - this is the recommended option for grading TA's!)")

    # configuring server address
    server_input = input("server: ")

    if (server_input != "default"):
        SERVER = server_input
        if (SERVER == "mc18.cs.purdue.edu"):
            print("--> Using 'custom server'... but it's the same as the default one")
        else:
            print("--> Using custom server")
    else:
        SERVER = "mc18.cs.purdue.edu"
        print("--> Using default server, an excellent choice!")

    print("--> Which port number to connect to? Ask who started up the server!")
    SERVER_PORT = input("port: ")
    if (SERVER_PORT == "default"):
        SERVER_PORT = "25565"

    # attempting to connect to server
    if (SERVER != "skip"): # hidden debug flag # TODO TODO TODO remove later
        SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SOCK.connect((SERVER, int(SERVER_PORT)))
        print("----> Connected to server successfully!")

    # questions to ask regarding personal settings
    configure_personal_settings()

    # getting session-wide settings from server
    print("\n--> Getting current session-wide settings from the server...")
    get_session_settings()
    print("--> Any session-wide settings that apply to all users can be configured via commands, see the \"help\" command for more information")

    # all ready to go, final remarks before endless command handling and socket listening
    print("\n--> All ready to go! To see the full list of commands, type \"help\", but here's the gist:")
    print_simple_help()
    print("** IMPORTANT: you must use these commands to sync up with your friends - using VLC itself to navigate or play/pause won't send these commands out! **")

    # TODO TODO send message to server that a user has joined, so that it pops up (or scrap idea if no time left)

    # endless socket listening
    sock_thr = threading.Thread(target = socket_handler)
    sock_thr.start()
    #sock_thr.join()

    # endless command parsing
    while (1):
        # full line
        cmd_line = input("\n\n> ")
        cmd_list = cmd_line.split()

        # command word
        cmd = cmd_list[0]

        # getting help
        if (cmd == "help-simple"):
            check_args_req(cmd_line, 1)
            print_simple_help()
        elif (cmd == "help"):
            check_args_req(cmd_line, 1)
            print_full_help()
        elif (cmd == "print-settings"):
            check_args_req(cmd_line, 1)
            print_current_settings()

        # playback
        elif (cmd == "play"):
            if (not check_args_req(cmd_line, 2)):
                print("YouTube URL not supplied")
                continue

            # must check URL first before sending message
            if (handle_play(cmd_list[1])):
                send_message("play " + CURRENT_URL)
        elif (cmd == "pause"):
            check_args_req(cmd_line, 1)

            send_message("pause")
            handle_pause()
        elif (cmd == "resume"):
            check_args_req(cmd_line, 1)

            send_message("resume")
            handle_resume()
        elif (cmd == "nav-forward"):
            check_args_req(cmd_line, 1, 2)

            if (len(cmd_list) > 1): # optional arg
                send_message("nav-forward " + cmd_list[1])
                handle_nav_forward(cmd_list[1])
            else:
                send_message("nav-forward " + DEFAULT_NAV)
                handle_nav_forward(DEFAULT_NAV)
        elif (cmd == "nav-back"):
            check_args_req(cmd_line, 1, 2)

            if (len(cmd_list) > 1): # optional arg
                send_message("nav-back " + cmd_list[1])
                handle_nav_back(cmd_list[1])
            else:
                send_message("nav-back " + DEFAULT_NAV)
                handle_nav_back(DEFAULT_NAV)
        elif (cmd == "nav-to"):
            if (not check_args_req(cmd_line, 2)):
                print("No time format specified (in __h__m__s format, see \"help\" for more details)")
                continue
            # must check pattern, and given the pattern must check if cmd_list[1] is empty (i.e. user typed "nav-to " with a trailing space but no arg)
            if (not cmd_list[1] or not check_timestamp_pattern(cmd_list[1])):
                print("** timestamp argument must be in the format __h__m__s (to specify hours, minutes, and seconds (i.e. \"nav-to 5m17s\" to go to 5:17)")
                continue

            # must check URL first before sending message
            if (handle_nav_to(cmd_list[1])):
                send_message("nav-to " + cmd_list[1])


        # session-wide
        elif (cmd == "toggle-auto"):
            if (not check_args_req(cmd_line, 2)):
                print("Must specify \"ON\" or \"OFF\"")
                continue
            if (check_toggle_on_off(cmd_list[1])):
                PAUSE_AUTO = cmd_list[1]
                send_message("toggle-auto " + PAUSE_AUTO)

        # personal, but must be transmitted
        elif (cmd == "change-username"):
            if (not check_args_req(cmd_line, 2)):
                print("Must specify a new username that does not have spaces in it")
                continue
            USERNAME = cmd_list[1]
            send_message("change-username " + USERNAME)

        # personal and limited to this client
        elif (cmd == "whoami"):
            check_args_req(cmd_line, 1)
            print("---> You are " + USERNAME)
        elif (cmd == "new-user-notify"):
            if (not check_args_req(cmd_line, 2)):
                print("Must specify \"ON\" or \"OFF\"")
                continue
            if (check_toggle_on_off(cmd_list[1])):
                NEW_USER_NOTIFY = cmd_list[1]
        elif (cmd == "playback-notify"):
            if (not check_args_req(cmd_line, 2)):
                print("Must specify \"ON\" or \"OFF\"")
                continue
            if (check_toggle_on_off(cmd_list[1])):
                PLAYBACK_NOTIFY = cmd_list[1]
        elif (cmd == "settings-notify"):
            if (not check_args_req(cmd_line, 2)):
                print("Must specify \"ON\" or \"OFF\"")
                continue
            if (check_toggle_on_off(cmd_list[1])):
                SETTINGS_NOTIFY = cmd_list[1]
        elif (cmd == "get-url"):
            check_args_req(cmd_line, 1)
            if (not check_video()):
                continue
            print("The current video is playing from " + CURRENT_URL)

        # no clue
        else:
            print("** command not found - type \"help\" to get the full list of what's possible (or if there had been a typo in your query)")

        # TODO TODO something like printing current session ID, printing all users in room, etc... maybe a chat option???
        #       switching to a chat mode vs command mode?
        # TODO have a stop command to stop the video?

if __name__ == '__main__':
    main()
