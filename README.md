# Team-F24-17-Discord-Tournament-T2

KSU IT Capstone Fall 2024 - Project 17 - KSU Esports Tournament Bot (Team 2)

This is a Discord bot for organizing and managing League of Legends tournaments within the Kennesaw State University Esports Discord server. It builds off of a preexisting bot created by a capstone team during the spring 2024 semester.

# How to set up the Discord bot

To start with, create a file called “.env” in the same directory as “bot.py” and the other files downloaded from the GitHub repository linked above. Paste this code into it:

BOT_TOKEN = 

GUILD_TOKEN =

GOOGLE_SHEETS_ID =

GOOGLE_SHEETS_NAME =

SPREADSHEET_PATH = 

DB_PATH = 

RIOT_API = 

# Generating the Discord bot token

Open the Discord Developer Portal: https://discord.com/developers/applications

After signing in, create a new application, name it whatever you'd like and agree to the terms of service.

Click the “Bot” tab on the left side of the page, then click “Reset Token”.

The page will give you a warning that any existing bot code containing a token will break if you do this; ignore that for now and click okay, then copy the string that appears. Your token should look something like this:
MTI4ADEzNzU0NDg6MTR5ODU3MA.G7Chtm.BZJvZtXtZ3s01d8zoyxZzfCw67wjJ9gCiCFVdc

Paste the bot token into your .env file.

# Obtaining the guild token

Open the Discord client, and under the “Advanced” settings tab, make sure “Developer Mode” is switched on. This enables you to copy Discord user and guild (server) IDs. Right-click the icon of the server you want to use the bot in, then click “Copy Server ID”. Paste the result after “GUILD_TOKEN = “.

# Obtaining Google Sheet ID and Sheet name (deprecated)

The sheet id is just the ID of the google sheet that you are trying to use. To find it, all you need to do is look at the url of your google sheet. You can find the ID here in the URL:

docs.google.com/spreadsheets/d/ID_IS_HERE/

If your sheet URL has any characters following the final slash shown here, such as “/edit?gid=[numbers]”, exclude them from the .env file.

The next line, “GOOGLE_SHEETS_NAME”, is self-explanatory; write the name of your Google spreadsheet exactly as it appears in your browser  following the “= “, no quotation marks or underscores necessary.

# Setting paths for necessary files

The current version of the bot utilizes an offline solution for indirect management of the database. The host of the bot can manipulate a spreadsheet using the template sheet provided with the bot, and whenever the bot runs it will automatically draw statistics from this sheet to update the database accordingly. Conversely, when users make changes to statistics either directly through DBMS or bot commands (e.g. commands updating wins, MVP points, etc.), the sheet will be updated.

To set up these functions, you must copy the paths of both the spreadsheet (xlsx) file and database (db) file behind their respective entries in ".env". No quotation marks are needed.

# Setting Riot API key

For the bot to retrieve information about players using the Riot API, you will need to request access to a Riot API key. Use this link to apply for a key, and ensure that you select "Personal" key, not "Development". Development keys will expire every 24 hours:
https://developer.riotgames.com/app-type

The key request can take anywhere from minutes to potentially days to be approved. Once it is, paste it after the RIOT_API entry in ".env".


# Setting up Google Sheets API access
This is currently the most complex part of setup. Following the Google Workspace link below, set up access to the Google Sheets API. When you get to step 2 under “Configure the OAuth consent screen,” ignore what it says about setting the User Type to Internal, as this option will probably be unavailable for you, and set it to External.

https://developers.google.com/sheets/api/quickstart/python

After you have followed the step under the heading “Install the Google client library,” you are done; you do not need to set up or run the sample code shown on the page.
Now that your Sheets API access is set up, go to Google Cloud Console again:

https://console.cloud.google.com

Navigate to the “APIs & Services” menu, then click on the “Credentials” button in the list of sub-menus on the left of the page. Hover over the “Create Credentials” button and click “Choose OAuth client ID”:

For “Application type,” select “Desktop app”, and click to download a JSON file, which you should rename “credentials.json”.

In the same directory as “.env”, “bot.py” and other bot-related files you’re working with, create a new folder called “src” and drop credentials.json inside. You will also need to place a copy of credentials.json in the following location:

"C:\Users\user\AppData\Roaming\gspread" OR "~/.config/gspread"

If any of the folders mentioned above don’t already exist, you will need to create them as they are necessary to make the bot run. Future versions of the bot should attempt to check for and/or create these folders automatically, rendering this step unnecessary.

# Installation of packages
To finish setting up the bot, there are a few Python packages you need to have installed on your computer for it to work:

aiosqlite

asyncio

discord

gspread

python-dotenv

Google API

All of these packages can be installed by typing `pip3 install [package name]` in Command Prompt, with the exception of the Google API package. The command to install it is found in the Google Developers link from the section where we set up API access (typing it should’ve been the last thing you did before finishing the step).

# Adding the Discord bot to your server

Return to the Discord developer portal link from the section where we generated a bot token, and under the “OAuth” menu, select the “applications.commands” and “bot” scopes. Scrolling down to “Bot Permissions,” select “Manage Roles” under General Permissions. Note that the permissions required by the bot are likely to change in future versions, and this may need to be revised.

Selecting just the “Administrator” permission will prevent any permissions-related issues from occurring with the bot, though granting this permission is generally not considered best practice. Below the scopes/bot permissions checklists, select “Guild Install,” and open the URL at the bottom of the menu in a new tab. This will display a prompt allowing you to add the Discord bot account to your server.

You should also go in your Discord server settings and create “Player” and “Volunteer” roles, or the bot will not function once run (future versions should create these roles automatically).

# Finishing setup

Open a command prompt window in the same directory as bot.py, and type either `python bot.py`, `python3 bot.py`, or simply `bot.py` (depending on your Python installation) to run the bot. If successful, you will see an output that says “Logged in as [your bot’s name],” and you’ll see that the bot account you added to your server is online in your Discord client.

# Note:
Future versions of the bot will likely remove or heavily alter the usage of the gspread package and related Google API functionality, so the latter half of this guide is being rewritten. As such, this readme may not reflect the real steps needed to set up the bot at the moment.

Future versions of this guide will also utilize screenshots that should simplify setup considerably.
