# ksu-esports-tournament-bot
KSU IT Capstone Fall 2024 - Project 17 - KSU eSports Tournament Bot (Team 2)

This is a Discord bot for organizing and managing League of Legends tournaments within the Kennesaw State University eSports Discord server.

What follows is an improved guide for setup of the existing KSU Esports Bot, based on the one created by a capstone team during the spring 2024 semester.

To start with, create a file called “.env” in the same directory as “bot.py” and the other files downloaded from the GitHub repository linked above. Paste this code into it:
	BOT_TOKEN = 

GUILD_TOKEN =

GOOGLE_SHEETS_ID =

GOOGLE_SHEETS_NAME =

Open the Discord Developer Portal: https://discord.com/developers/applications
	After signing in, create a new application, name it whatever and agree to the TOS.
Click the “Bot” tab on the left side of the page, then click “Reset Token”.

The page will give you a warning that any existing bot code containing a token will break if you do this; ignore that for now and click okay, then copy the string that appears. Your token should look something like this:
MTI4ADEzNzU0NDg6MTR5ODU3MA.G7Chtm.BZJvZtXtZ3s01d8zoyxZzfCw67wjJ9gCiCFVdc

Paste the bot token into your .env file. It should look like this:


Open the Discord client, and under the “Advanced” settings tab, make sure “Developer Mode” is switched on. This enables you to copy Discord user and guild (server) IDs. Right-click the icon of the server you want to use the bot in, then click “Copy Server ID”. Paste the result after “GUILD_TOKEN = “.


“GOOGLE_SHEETS_ID” 
The sheet id is just the ID of the google sheet that you are trying to use. To find it, all you need to do is look at the url of your google sheet. You can find the id here in the URL:

docs.google.com/spreadsheets/d/ID_IS_HERE/
Exclude any characters following the final slash shown here, such as “/edit?gid=[numbers]”.
Sheet name should be self-explanatory, it is just the name of the google spreadsheet

Finally, go to the following Discord developer portal link again, and under “Bot Permissions” on the bot tab, ensure “Manage Roles” is selected. You should also go in your Discord server settings and create “Player” and “Volunteer” roles, or the bot will not function once set up (future versions should create these roles automatically).
https://discord.com/developers/applications

Set up Google API access using this guide:
https://developers.google.com/sheets/api/quickstart/python
Once you have setup your api access you must do the following things:
Go to Google Cloud Console -> APIs & Services -> Credentials (left side) -> Create Credentials (Choose OAuth client ID) -> Select Desktop app for Application type -> Download JSON file -> Rename it to 'credentials.json' Once that is done, create a folder within this folder, it should be called src. Put the credentials.json in side that folder
You will need to put this credentials in the following location as well
"C:\Users\user\AppData\Roaming\gspread" OR "~/.config/gspread"
You may need to create these folders, but these are necessary to make the bot run

[Future versions of the bot will remove the gspread library and related functionality, so this portion of the guide is being rewritten].
