# Team-F24-17-Discord-Tournament-T2

KSU IT Capstone Fall 2024 - Project 17 - KSU Esports Tournament Bot (Team 2)

This is a Discord bot for organizing and managing tournaments within the Kennesaw State University League of Legends Discord server. It builds off of a preexisting bot created by a capstone team during the spring 2024 semester.

# Contents

**[Setup/Installation](#how-to-set-up-the-discord-bot)**

**[Recommendations for Future Development](#recommendations-for-further-development)**

**[User Guide](#user-guide)**


# How to set up the Discord bot

After you've downloaded the contents of this GitHub repository, locate the `.env.template` file and rename it to just `.env`. We will be filling this `.env` file with several values to allow the Discord bot to function.

# Generating the Discord bot token

Open the Discord Developer Portal: https://discord.com/developers/applications

After signing in, create a new application, name it whatever you'd like and agree to the terms of service.

Click the “Bot” tab on the left side of the page, then click “Reset Token”.

The page will give you a warning that any existing bot code containing a token will break if you do this; ignore that for now and click okay, then copy the string that appears. Your token should look something like this:
MTI4ADEzNzU0NDg6MTR5ODU3MA.G7Chtm.BZJvZtXtZ3s01d8zoyxZzfCw67wjJ9gCiCFVdc

Paste the bot token into your `.env` file.

# Obtaining the guild token

Open the Discord client, and under the “Advanced” settings tab, make sure “Developer Mode” is switched on. This enables you to copy Discord user and guild (server) IDs. Right-click the icon of the server you want to use the bot in, then click “Copy Server ID”. Paste the result after `GUILD_TOKEN=` in `.env`.

# Declare spreadsheet & database paths

We have two template files - "PlayerStats.xlsx" and "main_db.db" - included in this repository. **If you are planning to make changes to the bot after use, make sure you change these files' names** or edit .gitignore, otherwise you may inadvertently upload files containing user data.

Unless you want to move your spreadsheet and database files to another folder or rename them, **you can leave `SPREADSHEET_PATH` and `DB_PATH` to their defaults**, which are relative paths specifying the template spreadsheet/database files we have included in the repository.

`SPREADSHEET_PATH=PlayerStats.xlsx`

`DB_PATH=main_db.db`

# Setting up Riot API key

Visit https://developer.riotgames.com/app-type, make an account, and click "Register Product" under "Personal API Key". Agree to the terms of service, give a name and brief description of what you're using the key for (a Discord bot performing League tournament administration tasks), then submit the request for your key. When you click your username in the top-right corner, click "Apps" in the dropdown, and you should see your app listed somewhere in the dark column on the left side of the screen. Select this, and you will see a "General Info" section containing the status of your registration and (if it's approved) an API key beginning with "RGAPI". Copy this into the line of .env with `RIOT_API_KEY`.

In our experience, getting the app approved and receiving the key was extremely fast (it seemingly took just a few minutes) but it's possible that this process could last for a day or longer. If that is the case for you and you need a temporary API key, return to the main Riot developer dashboard page, and you can see a "Development API Key" which will expire every 24 hours.

# Installation of dependencies
To finish setting up the bot, ensure you have at least Python version 3.12.6 installed on the machine that will be hosting it, and run the following command in the same directory as the bot's files (including bot.py and requirements.txt).

`pip3 install -r requirements.txt`



*Note: if you want to run a containerized version of the bot using Docker, skip this step and see [our instructions for Docker setup](#docker-support) once you've populated the `.env` file with values and added the bot to your server.*

# Adding the Discord bot to your server

Return to the Discord developer portal link from the section where we generated a bot token, and under the “OAuth” menu, select the “applications.commands” and “bot” scopes. Scrolling down to “Bot Permissions,” select “Manage Roles” under General Permissions. Note that the permissions required by the bot are likely to change in future versions, and this may need to be revised.

Selecting just the “Administrator” permission will prevent any permissions-related issues from occurring with the bot, though granting this permission is generally not considered best practice. Below the scopes/bot permissions checklists, select “Guild Install,” and open the URL at the bottom of the menu in a new tab. This will display a prompt allowing you to add the Discord bot account to your server.

# Running the bot

Open a command prompt window in the same directory as bot.py, and type either `python bot.py`, `python3 bot.py`, or simply `bot.py` (depending on your Python installation) to run the bot. Depending on your installation you may also be able to run it by simply double-clicking the bot.py file. If successful, after (at most) a minute you will see a terminal output that says “Logged in as [your bot’s name],” and you’ll see that the bot account you added to your server is online in your Discord client.

# Docker Support

*[Note: Docker support for this bot is largely untested and major functionality may be unusable at present.](#recommendations-for-further-development)*

Our repository contains a functional Dockerfile, and once users with Docker with installed have followed all other steps (i.e. populated .env and added their bot to a server) they should be able to run a containerized version of the bot.

This is done by running the following commands in a terminal, which create a Docker image and Docker image container:

`docker build -t ksu-esports-bot .`

`docker run -d --name ksu-esports-bot-container --env-file .env ksu-esports-bot`

However, this functionality has undergone very limited testing, using only the "Docker Desktop" (AMD64) application installed on a machine running Windows 10. Any functionality beyond running the containerized bot and having it log in to Discord are untested, and extensive alterations may be required for the bot to function fully with Docker.



# Recommendations for Further Development

The following is a list of recommendations by our team for future capstone students looking to improve upon our work.

- Screenshots can be included in a GitHub repository and embedded in README.md, simplifying the bot setup process.
- When creating the bot application, specify just the bot permissions that are actually needed instead of using "Administrator", as this is not considered best practice.
- Finish implementation of Docker support to provide a convenient and more portable alternative to normal setup.
- /stats embed UI could be improved to display a user's full ranking information (for example, GOLD II instead of just GOLD). This change would necessitate documentation specifying that different tiers within ranks do not affect matchmaking, however.
- A possible UX improvement is combining /checkin and /sitout (formerly /volunteer) into a single command with 3 buttons.
- The bot could automatically create a channel (e.g. #registration) if it does not already exist, and use Discord's "modal" functionality to show users a form having them enter/update both their Riot ID and role preferences simultaneously. This would simplify the bot's
- When /resetdb is entered twice within 10 seconds (i.e. successfully performing a reset), the initial confirmation message is erroneously sent a second time along with the message announcing a successful reset. The 10-second expiration message is also sent afterward, despite the reset already being carried out. This command could also be reworked to remove the need for an import of the "datetime" library.
- Rework / finish implementation of MVP voting to allow for multiple voting pools, as the current matchmaking implementation provides for creation of multiple lobbies with concurrently-running matches. In other words, users with the "Player" and "Volunteer" from different lobbies should each be able to vote for MVPs only within their own lobby. A possible solution for this is tying MVP voting directly to the /win command, but there should also be functionality for users to vote for an "ace" (MVP on the losing team).



# User Guide & List of Commands

*Note: this section is a work-in-progress. Documentation available through the bot's /help command will be shown here shortly.*