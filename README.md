# Team-F24-17-Discord-Tournament-T2

KSU IT Capstone Fall 2024 - Project 17 - KSU Esports Tournament Bot (Team 2)

This is a Discord bot for organizing and managing League of Legends tournaments within the Kennesaw State University Esports Discord server. It builds off of a preexisting bot created by a capstone team during the spring 2024 semester.

# How to set up the Discord bot

To start with, create a file called “.env” in the same directory as “bot.py” and the other files downloaded from the GitHub repository linked above. Paste this text into it:

`BOT_TOKEN = `

`GUILD_TOKEN = `

`SPREADSHEET_PATH = `

`DB_PATH = `

`RIOT_API_KEY = `

# Generating the Discord bot token

Open the Discord Developer Portal: https://discord.com/developers/applications

After signing in, create a new application, name it whatever you'd like and agree to the terms of service.

Click the “Bot” tab on the left side of the page, then click “Reset Token”.

The page will give you a warning that any existing bot code containing a token will break if you do this; ignore that for now and click okay, then copy the string that appears. Your token should look something like this:
MTI4ADEzNzU0NDg6MTR5ODU3MA.G7Chtm.BZJvZtXtZ3s01d8zoyxZzfCw67wjJ9gCiCFVdc

Paste the bot token into your .env file.

# Obtaining the guild token

Open the Discord client, and under the “Advanced” settings tab, make sure “Developer Mode” is switched on. This enables you to copy Discord user and guild (server) IDs. Right-click the icon of the server you want to use the bot in, then click “Copy Server ID”. Paste the result after “GUILD_TOKEN = “.

# Declare spreadsheet & database paths

WIP, may be removed if we take these sections out of .env and declare paths to the bot directory inside our code. We could also make these optional if the bot host wants to move the files to more convenient locations.

# Setting up Riot API key

WIP

# Installation of dependencies
To finish setting up the bot, ensure you have at least Python version 3.12.6 installed on the machine that will be hosting it, and run the following command in the same directory as the bot's files (including bot.py and requirements.txt).

`pip3 install -r requirements.txt`

# Adding the Discord bot to your server

Return to the Discord developer portal link from the section where we generated a bot token, and under the “OAuth” menu, select the “applications.commands” and “bot” scopes. Scrolling down to “Bot Permissions,” select “Manage Roles” under General Permissions. Note that the permissions required by the bot are likely to change in future versions, and this may need to be revised.

Selecting just the “Administrator” permission will prevent any permissions-related issues from occurring with the bot, though granting this permission is generally not considered best practice. Below the scopes/bot permissions checklists, select “Guild Install,” and open the URL at the bottom of the menu in a new tab. This will display a prompt allowing you to add the Discord bot account to your server.

You should also go in your Discord server settings and create “Player” and “Volunteer” roles, or the bot will not function once run (future versions should create these roles automatically).

# Finishing setup

Open a command prompt window in the same directory as bot.py, and type either `python bot.py`, `python3 bot.py`, or simply `bot.py` (depending on your Python installation) to run the bot. Depending on your installation you may also be able to run it by simply double-clicking the bot.py file. If successful, after (at most) a minute you will see a terminal output that says “Logged in as [your bot’s name],” and you’ll see that the bot account you added to your server is online in your Discord client.

# Note:

Future versions of this guide could utilize screenshots to simplify setup, though this will add to the file size of our repository.
