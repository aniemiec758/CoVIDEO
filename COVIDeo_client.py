import vlc, pafy # to handle video playing
import sys # for sys.exit() in version checking
import threading # a thread is created to endlessly listen for incoming socket commands from the server
import re # regex matching required for navigating video timestamps

#=========================<Important globals>===================================

SERVER = "data.cs.purdue.edu:25566" # default value can be kept by user
SESSION_ID = "" # for the server to know which incoming requests are for who
PAUSE_AUTO = "" # should new videos be paused automatically for this session?
NEW_USER_NOTIFY = "" # do you want to be notified when a new user joins the session?
PLAYBACK_NOTIFY = "" # do you want to be notified about when other users are managing the video?
SETTINGS_NOTIFY = "" # do you want to be notified when someone changes their username/edits server-wide settings?
USERNAME = "" # display name

#=========================<Help messages>=======================================

def print_simple_help():
    print("----> type \"play <youtube URL>\" to load up a new video URL for everybody")
    print("----> type \"pause\" to pause a playing video for everybody")
    print("----> type \"resume\" to resume a paused video for everybody")
    print("----> type \"nav-forward\" to jump forwards by 10 seconds, or \"nav-forward <number>\" to jump forwards by <number> seconds for everybody")
    print("----> type \"nav-back\" to jump back by 10 seconds, or \"nav-back <number>\" to jump back by <number> seconds for everybody")
    print("----> type \"nav-to <format>\" to jump to a specific timestamp of the video for everybody")
    print("------> type the format in terms of \"__h__m__s\" to specify hours, minutes, and seconds (i.e. \"nav-to 5m17s\" to go to 5:17)")
    print("----> type \"help-simple\" for this quick-reference list itself, or \"help\" for a full list of commands")

def print_full_help():
    print("--> Simple video player commands:")
    print("----> type \"play <youtube URL>\" to load up a new video URL for everybody")
    print("----> type \"pause\" to pause a playing video for everybody")
    print("----> type \"resume\" to resume a paused video for everybody")
    print("----> type \"nav-forward\" to jump forwards by 10 seconds, or \"nav-forward <number>\" to jump forwards by <number> seconds for everybody")
    print("----> type \"nav-back\" to jump back by 10 seconds, or \"nav-back <number>\" to jump back by <number> seconds for everybody")
    print("----> type \"nav-to\ <format>\" to jump to a specific timestamp of the video for everybody")
    print("------> type the format in terms of \"__h__m__s\" to specify hours, minutes, and seconds (i.e. \"nav-to 5m17s\" to go to 5:17)")
    print("----> type \"help-simple\" for a printout of just this quick-reference list")
    print("\n--> Session-wide commands:")
    print("----> type \"toggle-auto [ON|OFF]\" to set whether newly-loaded videos will start paused or not for everybody")
    print("\n--> Personal commands:")
    print("----> type \"change-username <new username to use>\" to modify your username, helpful if two people end up using the same name!")
    print("------> (you must pick a username that does not have spaces in it)")
    print("---> type \"whoami\" to get your current username")
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

def configure_new_session():
    print("\n--> Now just answer a few questions regarding your connection to this session (any of these values may be changed later on via commands):")

    # auto-pausing
    pause_input = input("----> Would you like new videos to automatically be paused for everybody? (yes/no) ")
    if (pause_input == "yes"):
        PAUSE_AUTO = "ON"
        print("------> Video pausing turned ON")
    else:
        PAUSE_AUTO = "OFF"
        print("------> Video pausing turned OFF")

    # TODO TODO TODO anything else? (if you want to specify a video quality or go auto, etc pafy things)
    # update in help text, infinite command parsing block, notifications printout, have a global, communicate with server, etc

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
    

#=========================<Socket interfacing>=======================================

# endlessly listen for server requests coming over the socket
def socket_handler():
    # TODO TODO TODO TODO
    pass

# formulates and sends a message to the server
def send_message():
    # TODO TODO TODO TODO
    pass

#=========================<Playback commands>===================================

def handle_play(video_url):
    print("-handle_play, with video_url %" + video_url + "%")
    # TODO TODO server communication
    pass

def handle_pause():
    print("-handle_pause")
    # TODO TODO server communication
    pass

def handle_resume():
    print("-handle_resume")
    # TODO TODO server communication
    pass

def handle_nav_forward(t=""):
    print("-handle_nav_forward, with t %" + t + "%")
    # TODO TODO server communication
    pass

def handle_nav_back(t=""):
    print("-handle_nav_back, with t %" + t + "%")
    # TODO TODO server communication
    pass

def handle_nav_to(time_format=""):
    print("-handle_nav_to, with time format %" + time_format + "%")
    # TODO TODO server communication
    pass

#=========================<Main>================================================

def main():
    # version checking - very important, since python2 uses raw_input() for I/O and python3 uses input()
    if sys.version_info[0] < 3:
        print("--> Error: you must use python3 to run COVIDeo")
        sys.exit()

    # introductory block text
    print("=== Welcome to COVIDeo! ===")
    print("** IMPORTANT: COVIDeo requires VLC Media Player, a freeware video playing application, to be installed on your device (https://www.videolan.org/vlc/) **")
    print("--> Thank you for choosing our application in these trying times!")
    print("\n--> First, type in which server you wish to contact in <server IP>:<port number> format.")
    print("----> (type \"default\" for the default input of 'data.cs.purdue.edu:25566' - this is the recommended option for grading TA's!)")

    # configuring server address
    server_input = input("server: ")

    if (server_input != "default"):
        SERVER = server_input
        print("--> Using custom server")
    else:
        SERVER = "data.cs.purdue.edu:25566"
        print("--> Using default server, an excellent choice!")

    # attempting to connect to server
    # TODO TODO TODO TODO TODO
    print("----> Connected to server successfully!")

    # creating or joining a session
    print("\n--> Would you like to join an existing COVIDeo session, or start a new one?")
    print("----> (type \"new\" to have a new session ID generated for you, otherwise type the session ID of your friend!)")

    session_input = input("session_id: ")

    # error handling aroud SESSION_ID
    if (session_input != "new"):
        # verifying session ID, otherwise reprompting endlessly
        print("------> Attempting to connect to session " + session_input + "...")
        # TODO TODO TODO TODO communicate with server to verify given SESSION_ID; if-else block about infinite loop or something
        print("------> Success!")

    else:
        print("------> Attempting to create new session ID...")
        # TODO TODO TODO TODO communicate with server to get and set new SESSION_ID
        print("----> New session ID created: " + SESSION_ID)
        print("------> (this may be viewed anytime by typing the command \"session-id\"")

        # configuring a new session
        configure_new_session()

    # any lingering questions to ask regarding personal settings
    configure_personal_settings()

    # all ready to go, final remarks before endless command handling and socket listening
    print("\n--> All ready to go! To see the full list of commands, type \"help\", but here's the gist:")
    print_simple_help()
    print("** IMPORTANT: you must use these commands to sync up with your friends - using VLC itself to navigate or play/pause won't send these commands out! **")

    # endless socket listening
    sock_thr = threading.Thread(target = socket_handler)
    sock_thr.start()
    sock_thr.join()

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
            handle_play(cmd_list[1])
        elif (cmd == "pause"):
            check_args_req(cmd_line, 1)
            handle_pause()
        elif (cmd == "resume"):
            check_args_req(cmd_line, 1)
            handle_resume()
        elif (cmd == "nav-forward"):
            check_args_req(cmd_line, 1, 2)
            if (len(cmd_list) > 1): # optional arg
                handle_nav_forward(cmd_list[1])
            else:
                handle_nav_forward()
        elif (cmd == "nav-back"):
            check_args_req(cmd_line, 1, 2)
            if (len(cmd_list) > 1): # optional arg
                handle_nav_back(cmd_list[1])
            else:
                handle_nav_back()
        elif (cmd == "nav-to"):
            if (not check_args_req(cmd_line, 2)):
                print("No time format specified (in __h__m__s format, see \"help\" for more details)")
                continue
            # must check pattern, and given the pattern must check if cmd_list[1] is empty (i.e. user typed "nav-to " with a trailing space but no arg)
            if (not cmd_list[1] or not check_timestamp_pattern(cmd_list[1])):
                print("** timestamp argument must be in the format __h__m__s (to specify hours, minutes, and seconds (i.e. \"nav-to 5m17s\" to go to 5:17)")
                continue
            handle_nav_to(cmd_list[1])

        # session-wide
        elif (cmd == "toggle-auto"):
            if (not check_args_req(cmd_line, 2)):
                print("Must specify \"ON\" or \"OFF\"")
                continue
            if (check_toggle_on_off(cmd_list[1])):
                PAUSE_AUTO = cmd_list[1]
                # TODO TODO TODO update the server with this information

        # personal
        elif (cmd == "change-username"):
            if (not check_args_req(cmd_line, 2)):
                print("Must specify a new username that does not have spaces in it")
                continue
            USERNAME = cmd_list[1]
            # TODO TODO TODO update the server with this information
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

        # no clue
        else:
            print("** command not found - type \"help\" to get the full list of what's possible (or if there had been a typo in your query)")

        # TODO TODO TODO should there be an "exit" command, and if you're the last user of a session, the session gets deleted? stretch-goal if time permits
        # TODO TODO something like printing current session ID, printing all users in room, etc... maybe a chat option???
        #       switching to a chat mode vs command mode?

if __name__ == '__main__':
    main()
