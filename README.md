# Team-F24-17-Discord-Tournament-T2

KSU IT Capstone Fall 2024 - Project 17 - KSU Esports Tournament Bot (Team 2)

This is a Discord bot for organizing and managing tournaments within the Kennesaw State University League of Legends Discord server. It builds off of a preexisting bot created by a capstone team during the spring 2024 semester.

# How to set up the Discord bot

After you've downloaded the contents of this GitHub repository, locate the `.env.template` file and rename it to just `.env`. We will be filling this `.env` file with several values to allow the Discord bot to function.

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

We have two template files - "PlayerStats.xlsx" and "main_db.db" - included in this repository. **If you are planning to make changes to the bot after use, make sure you change these files' names** or edit .gitignore, otherwise you may inadvertently upload files containing user data.

Unless you want to move your spreadsheet and database files to another folder, you can simply use the relative paths for the template spreadsheet/database files we have included in the repository. So these two lines would look like this:
`SPREADSHEET_PATH= PlayerStats.xlsx`
`DB_PATH= main_db.db`

Make sure you change the names of these 

# Setting up Riot API key

Visit https://developer.riotgames.com/app-type, make an account, and click "Register Product" under "Personal API Key". Agree to the terms of service, give a name and brief description of what you're using the key for (a Discord bot performing League tournament administration tasks), then submit the request for your key. When you click your username in the top-right corner, click "Apps" in the dropdown, and you should see your app listed somewhere in the dark column on the left side of the screen. Select this, and you will see a "General Info" section containing the status of your registration and (if it's approved) an API key beginning with "RGAPI". Copy this into the line of .env with `RIOT_API_KEY`.

In our experience, getting the app approved and receiving the key was extremely fast - it seemingly took just a few minutes - but it's possible that this process could last for a day or longer. If that is the case for you and you need a temporary API key, return to the main Riot developer dashboard page, and you can see a "Development API Key" which will expire every 24 hours.

# Installation of dependencies
To finish setting up the bot, ensure you have at least Python version 3.12.6 installed on the machine that will be hosting it, and run the following command in the same directory as the bot's files (including bot.py and requirements.txt).

`pip3 install -r requirements.txt`

# Adding the Discord bot to your server

Return to the Discord developer portal link from the section where we generated a bot token, and under the “OAuth” menu, select the “applications.commands” and “bot” scopes. Scrolling down to “Bot Permissions,” select “Manage Roles” under General Permissions. Note that the permissions required by the bot are likely to change in future versions, and this may need to be revised.

Selecting just the “Administrator” permission will prevent any permissions-related issues from occurring with the bot, though granting this permission is generally not considered best practice. Below the scopes/bot permissions checklists, select “Guild Install,” and open the URL at the bottom of the menu in a new tab. This will display a prompt allowing you to add the Discord bot account to your server.

You should also go in your Discord server settings and create “Player” and “Volunteer” roles, or the bot will not function once run (future versions should create these roles automatically).

# Finishing setup

Open a command prompt window in the same directory as bot.py, and type either `python bot.py`, `python3 bot.py`, or simply `bot.py` (depending on your Python installation) to run the bot. Depending on your installation you may also be able to run it by simply double-clicking the bot.py file. If successful, after (at most) a minute you will see a terminal output that says “Logged in as [your bot’s name],” and you’ll see that the bot account you added to your server is online in your Discord client.

# Notes

If you are planning to adjust 

# Recommendations for Futher Development

The following is a list of recommendations by our team for future capstone students looking to improve upon our work.

- Screenshots can be included in a GitHub repository and embedded in README.md, simplifying the bot setup process
- When creating the bot application, specify just the bot permissions that are actually needed instead of using "Administrator", as this is not considered best practice.
- Finish implementation of Docker support to provide a convenient alternative to normal setup