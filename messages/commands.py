async def process_command(message, prefix):
    text = message.content[len(prefix):].split()
    command = text[0] if len(text) > 0 else ""
    optionals = text[1:] if len(text) > 1 else []
    print(command)

    if command == "" or not command[0].isalnum():
        return

    if command == "ping":
        await message.channel.send("pong")
    elif command == "hello":
        await message.channel.send("world")
    else:
        await message.channel.send("I don't understand that command")
