import json
import threading

import redis
from datetime import datetime, time


def confirmation():
    print("1.LOGIN\n2.SIGN UP")
    entry_option = int(input())
    user_password = ""
    if entry_option == 1:
        login_username = input("ENTER YOUR USERNAME: ")
        if r.exists(login_username):
            user_password = r.get(login_username)
        else:
            print(login_username + " DOESN'T EXIST!")
            confirmation()
        given_password = input("ENTER YOUR PASSWORD: ")
        if given_password == user_password:
            print("WELCOME " + login_username)
            menu(login_username)
        else:
            print("INCORRECT PASSWORD!")
            confirmation()
    elif entry_option == 2:
        signup_username = input("ENTER YOUR USERNAME: ")
        if r.exists(signup_username):
            print("USERNAME ALREADY EXISTS!")
            confirmation()
        else:
            signup_password = input("ENTER YOUR PASSWORD: ")
            r.set(signup_username, signup_password)
            print("WELCOME " + signup_username)
            menu(signup_username)
    else:
        print("WRONG INPUT!")
        confirmation()


def menu(username):
    channels = r.smembers("channels")
    for x in channels:
        x_info = json.loads(r.get(x))
        print(x, "*", len(x_info["members"]), "members * bio:", x_info["description"])
    print("-1:create a channel\n-2:back")
    command = input("COMMAND: ")
    if command == "-1":
        creating_channel(username)
    elif command == "-2":
        confirmation()
    elif r.sismember("channels", command):
        channel_info = json.loads(r.get(command))
        members = list(channel_info["members"])
        print("members: ", members)
        if username in members:
            sub = r.pubsub(ignore_subscribe_messages=True)
            sub.subscribe(command)
            channel_view(sub, command, username)
        else:
            subscription = input(f"DO YOU WANT TO SUBSCRIBE TO {command} ?\n1.YES\n2.NO\n")
            if subscription == "1":
                sub = r.pubsub(ignore_subscribe_messages=True)
                sub.subscribe(command)
                members.append(username)
                channel_info["members"] = members
                channel_info = json.dumps(channel_info)
                r.set(command, channel_info)
                print("members: ", members)
                channel_view(sub, command, username)
            elif subscription == "2":
                menu(username)
            else:
                print("INVALID COMMAND")
                menu(username)
    else:
        print("INVALID INPUT!")
        menu(username)


def creating_channel(username):
    channel_name = input("ENTER CHANNEL'S NAME: \n-1:back\n")
    if channel_name == "-1":
        return
    if r.sismember("channels", channel_name):
        print("CHANNEL'S NAME ALREADY EXISTS!")
        creating_channel(username)
    else:
        channel_bio = input("DESCRIBE YOUR CHANNEL: ")
        channel_info = {
            "creator": username,
            "created_at": str(datetime.now()),
            "description": channel_bio,
            "members": list(),
        }
        channel_info_object = json.dumps(channel_info)
        r.set(channel_name, channel_info_object)
        r.sadd("channels", channel_name)
        menu(username)


def channel_view(sub, channel_name, username):
    for history in (p.lrange(channel_name, 0, -1)):
        print(history)
    threading.Thread(target=publisher, args=(channel_name, username)).start()
    for item in sub.listen():
        message = str(item['data'])
        split = message.split(" ")
        sender = split[2]
        if message.__contains__("\\unsubscribe") and sender.__eq__(username):
            sub.unsubscribe(channel_name)
            channel_info = json.loads(r.get(channel_name))
            members = list(channel_info["members"])
            members.remove(username)
            channel_info["members"] = members
            channel_info = json.dumps(channel_info)
            r.set(channel_name, channel_info)
            menu(username)
        elif message.__contains__('\\back'):
            if sender.__eq__(username):
                menu(username)
        else:
            print(message)


def publisher(channel_name, username):
    while True:
        text = input("\\unsubscribe\n\\back\nEnter the message you want to send: \n")
        message = f"[{datetime.now()}] {username} ({channel_name}) : {text}"
        r.publish(channel_name, message)
        if text.__contains__('\\back') or text.__contains__('\\unsubscribe'):
            return
        p.rpush(channel_name, message)


if __name__ == '__main__':
    pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0, password='Moosa6208', decode_responses=True)
    pool2 = redis.ConnectionPool(host='127.0.0.1', port=6379, db=1, password='Moosa6208', decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    p = redis.Redis(connection_pool=pool2)
    confirmation()

