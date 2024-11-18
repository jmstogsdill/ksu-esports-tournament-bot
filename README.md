# Team-F24-17-Discord-Tournament-T2

KSU IT Capstone Fall 2024 - Project 17 - KSU Esports Tournament Bot (Team 2)

This is a Discord bot for organizing and managing tournaments within the Kennesaw State University League of Legends Discord server. It builds off of a preexisting bot created by a capstone team during the spring 2024 semester.

## Contents

**[Setup/Installation](#how-to-set-up-the-discord-bot)**

**[Recommendations for Future Development](#recommendations-for-further-development)**

**[User Guide](#user-guide)**


## How to set up the Discord bot

After you've downloaded the contents of this GitHub repository, locate the `.env.template` file and rename it to just `.env`.

**Note:** If you are using Windows and do not have "File name extensions" turned on in File Explorer's "View" tab, you will need to turn it on to rename the file properly. If you are renaming the file correctly you will get a warning telling you that the file might become unusable if you change its extension.

We will be filling this `.env` file with several values to allow the Discord bot to function.

## Generating the Discord bot token

Open the Discord Developer Portal: https://discord.com/developers/applications

After signing in, create a new application, name it whatever you'd like and agree to the terms of service.

Click the “Bot” tab on the left side of the page, then click “Reset Token”.

The page will give you a warning that any existing bot code containing a token will break if you do this; ignore that for now and click okay, then copy the string that appears. Your token should look something like this:
MTI4ADEzNzU0NDg6MTR5ODU3MA.G7Chtm.BZJvZtXtZ3s01d8zoyxZzfCw67wjJ9gCiCFVdc

While you're on this "Bot" page, you should also scroll down to "Privileged Gateway Intents" and **enable "Server Members Intent"**. The Server Members intent is used by the bot to access the usernames of members in your server and @ them when they join so they use /link. The other intents (Message Content and Presence) can be left disabled unless you are a developer and plan to add functionality that requires viewing users' online status, activities (i.e. games being played) or the content of messages that are not slash commands (which could be useful for moderation features).

When that's done, paste the bot token you copied into your `.env` file. There should be no spaces between variables and equal signs anywhere in the file.

## Obtaining the guild token

Open the Discord client, and under the “Advanced” settings tab, make sure “Developer Mode” is switched on. This enables you to copy Discord user and guild (server) IDs. Right-click the icon of the server you want to use the bot in, then click “Copy Server ID”. Paste the result after `GUILD_TOKEN=` in `.env`.

## Declare spreadsheet & database paths

We have two template files - "PlayerStats.xlsx" and "main_db.db" - included in this repository. **If you are planning to make changes to the bot after use, make sure you change these files' names** or edit .gitignore, otherwise you may inadvertently upload files containing user data.

Unless you want to move your spreadsheet and database files to another folder or rename them, **you can leave `SPREADSHEET_PATH` and `DB_PATH` to their defaults**, which are relative paths specifying the template spreadsheet/database files we have included in the repository.

> SPREADSHEET_PATH=PlayerStats.xlsx
> 
> DB_PATH=main_db.db

## Setting up Riot API key

Visit https://developer.riotgames.com/app-type, make an account, and click "Register Product" under "Personal API Key". Agree to the terms of service, give a name and brief description of what you're using the key for (a Discord bot performing League tournament administration tasks), then submit the request for your key.

When you click your username in the top-right corner, click "Apps" in the dropdown, and you should see your app listed somewhere in the dark column on the left side of the screen. Select this, and you will see a "General Info" section containing the status of your registration and (if it's approved) an API key beginning with "RGAPI". Copy this into the line of .env with `RIOT_API_KEY`.

In our experience, getting the app approved and receiving the key was extremely fast (it seemingly took just a few minutes) but it's possible that this process could last for a day or longer. If that is the case for you and you need a temporary API key, return to the main Riot developer dashboard page, and you can see a "Development API Key" which will expire every 24 hours.

## Installation of dependencies
To finish setting up the bot, ensure you have at least Python version 3.12.6 installed on the machine that will be hosting it, and run the following command in the same directory as the bot's files (including bot.py and requirements.txt).

> pip3 install -r requirements.txt



*Note: if you want to run a containerized version of the bot using Docker, skip this step and see [our instructions for Docker setup](#docker-support) once you've populated the `.env` file with values and added the bot to your server.*

## Adding the Discord bot to your server

Return to the Discord developer portal link from the section where we generated a bot token, and under the “OAuth” menu, select the “applications.commands” and “bot” scopes. Scrolling down to “Bot Permissions,” select “Manage Roles” under General Permissions. Note that the permissions required by the bot are likely to change in future versions, and this may need to be revised.

Selecting just the “Administrator” permission will prevent any permissions-related issues from occurring with the bot, though granting this permission is generally not considered best practice. Below the scopes/bot permissions checklists, select “Guild Install,” and open the URL at the bottom of the menu in a new tab. This will display a prompt allowing you to add the Discord bot account to your server.

## Running the bot

Open a command prompt window in the same directory as bot.py, and type either `python bot.py`, `python3 bot.py`, or simply `bot.py` (depending on your Python installation) to run the bot. Depending on your installation you may also be able to run it by simply double-clicking the bot.py file. If successful, after (at most) a minute you will see a terminal output that says “Logged in as [your bot’s name],” and you’ll see that the bot account you added to your server is online in your Discord client. [Jump to our user guide for more information.](#user-guide--command-reference)

## Docker Support

*[Note: Docker support for this bot is largely untested and major functionality may be unusable at present.](#recommendations-for-further-development)*

Our repository contains a functional Dockerfile, and once users with Docker with installed have followed all other steps (i.e. populated .env and added their bot to a server) they should be able to run a containerized version of the bot.

This is done by running the following commands in a terminal, which create a Docker image and Docker image container:

> docker build -t ksu-esports-bot .

> docker run -d --name ksu-esports-bot-container --env-file .env ksu-esports-bot

However, this functionality has undergone very limited testing, using only the "Docker Desktop" (AMD64) application installed on a machine running Windows 10. Any functionality beyond running the containerized bot and having it log in to Discord are untested, and extensive alterations may be required for the bot to function fully with Docker.


# User Guide & Command Reference

If the bot is running when it is added to a server for the first time, it will post a welcome message listing all its commands.

When a new user joins the server, the bot will automatically @ them with a welcome message and tell them to use both /link and /rolepreference. By default, the bot does this in the "#general" channel if it exists. However, the bot host can copy a numeric channel ID (using the same method to copy a guild token) and paste it in `.env` after `WELCOME_CHANNEL_ID=` in order to specify a different channel for the bot to do this. Alternatively, this can be left blank to disable welcome messages entirely if there's no #general channel.

## 📜 General Commands

### /help

- Displays a multi-page help menu with brief explanations of each bot command. Any server member can type this command.

### /link

- Links a user's Riot ID to their Discord account.
- All new members joining the bot's server will be welcomed and prompted to type this command through the on_member_join() function. It takes in a user's Riot ID (e.g. username#1234 or username#NA1) and checks whether it exists using the Riot Games API if a key has been specified in `.env`. The user's Riot ID is then stored in the database alongside the numeric Discord ID and username (technically, display name) of the person who typed the command.
- This command has error handling so if a user enters an invalid ID or an ID that someone else has already stored in the database, they will receive messages telling them about it. In the latter case, the bot will send the username of the person who has previously linked the given Riot ID (in clickable @Username format) and tell the user typing the command to notify an admin if a mistake was made. This situation is where [/unlink](#unlink) comes in handy.

### /rolepreference

- Allows users to set their preference for the 5 different League of Legend roles from 1-5 (with 1 being most preferred, and 5 being least).
- Each of the 5 roles (top lane, jungle, mid lane, bottom lane and support) displays as its own dropdown menu which players can select to instantly update their "RolePreference" string in the database. This string is stored as a 5-digit number with each digit corresponding to a role and its preference. This command is only usable by players who have previously linked their Riot ID to their Discord account.
- The command also handles the edge case in which a player somehow receives a Volunteer or Player role despite not having a linked account, and it will send an error message if that happens.

### /stats [player]

- Displays statistics about a given server member who has used `/link` to connect their account.
- Utilizes the get_encrypted_summoner_id() and update_player_rank() functions to make a Riot Games API request and pull the updated rank for a given Riot ID.
- Riot ID and player rank (solo/duo queue) are displayed in an embed, along with inhouse tournament statistics: participation points, games played, wins, MVP points, and winrate.
- **Potential for improvement:** This is one of only three commands/actions that calls the function to updates players' Discord display names in the database; the other two are `/checkin` and `/sitout` (to prevent players from joining matchmaking without up-to-date display names in the database, which would potentially cause confusion for admins). This is also the *only* command that calls the update_excel() function, and it only updates the Excel spreadsheet on a per-user basis. See our [recommendations for further development](#simple--short-term-improvements) for more information about this.


## 🎲 Matchmaking & Role Commands

### /checkin

- Displays two buttons allowing the user to add or remove themselves from the "Player" role.
- Buttons should not function prior to using `/link`, but they will appear regardless of who uses the command
- Prerequisite to inclusion in teams generated by `/matchmake`.
- When an admin types `/points` upon the conclusion of a match, users who have checked in to receive the "Player" role will have their "GamesPlayed" and "Participation" incremented in the database.
- One of three actions that calls the update_username() function along with the `/stats` and `/sitout` commands

### /sitout

- Displays two buttons allowing the user to add or remove themselves from the "Volunteer" role, which indicates the user is volunteering to sit out from an upcoming inhouse match.
- Buttons should not function prior to using `/link`, but they will appear regardless of who uses the command
- Players volunteering to sit out from a match are displayed at the bottom of a `/matchmake` embed separately from the red and blue teams
- When an admin types `/points` upon the conclusion of a match, users who have volunteered to sit out will have their "Participation" incremented in the database.
- Referred to as `/volunteer` in other versions of this bot
- One of three actions that calls the update_username() function along with the `/stats` and `/checkin` commands

### /players

- Lists all users with Player and Volunteer roles
- Usable by anyone


### /clear 🛡️

- Admin-only; removes all users from Player and Volunteer roles

### /matchmake [match_number]

- Attempts to generate lobbies consisting of 10 users with the "Player" role each. This command will attempt to create two teams that are as balanced as possible taking into account players' role preferences and skill (i.e. rank/tier).
- Players should, in most cases, never be matched against someone more than 1 tier above/below them.
- There is support for up to 3 lobbies (which would require 30 users with the Player role).
- Randomization is implemented so re-running this command with the same set of players twice should not generate identical teams.
- Bot hosts can easily modify the degree to which the matchmaking algorithm favors balancing player skill over role preference using the `.env` file. By default, TIER_WEIGHT is set to 0.7 and ROLE_PREFERENCE_WEIGHT is set to 0.3. Both values should always add to 1, but the bot host can, for example, reverse those values to make the bot favor role preference a bit more than player tier when it builds teams.
- The bot host can also edit how ranks are split into tiers using `.env` by altering placement of commas/colons for the value of the TIER_GROUPS variable.
- With default settings, unranked/iron/bronze/silver are in a tier, gold/platinum are in a tier, and emerald and above are each their own unique tier.
- **Admins should always type `/win` and `/points` at the conclusion of a match.**


### /win [match_number] [lobby_number] [team] 🛡️

- Admin-only. Increments "Wins" in database for all members of a winning team. The command will only allow you to specify 1, 2, or 3 for match_number, and "red" or "blue" for team. **Should be typed at the end of every match.**


### /points 🛡️

- Admin-only. Increments "GamesPlayed" and "Participation" database values for users with the Player role, and just "Participation" for users with the Volunteer role. **Should be typed at the end of every match.**

### /toxicity [player] 🛡️

- Admin-only. Used to penalize players for poor sportsmanship during a match.
- Increments "ToxicityPoints" database value for a specified member of the Discord server who has correctly used `/link`, simultaneously reducing their "TotalPoints".


### /unlink [player] 🛡️

- Admin-only. Used to delete a server member's database record in certain situations, for example if they have entered another user's Riot ID instead of their own. If deleting the entire record would also remove a player's genuine statistics from previous tournaments, it is advised admins make a backup of these stats before using the command or simply remove the record from the database manually.
- The command will prompt the admin with a warning before actually deleting a player's database record


### /confirm

- Confirmation command for admins using `/unlink`


### /resetdb 🛡️🛡️🛡️

- Only usable by the *owner* of the server the command is typed in. This will reset all players' "Participation," "Wins," "MVPs," "ToxicityPoints," "GamesPlayed," "WinRate" and "TotalPoints" in the database, while maintaining records of linked users' ranks, tiers and role preference.


## 🛠️ Commands Subject to Change

### /votemvp [player]

- Allows a user to initiate a 5-minute MVP voting period. Other players can vote on server members with the Player role to have that person's "MVPs" database value incremented. A tie (i.e. 2 MVPs) is possible provided a minimum number of users participates in the vote.
- Updates are sent to the chat notifying users when 3 minutes, 2 minutes and 1 minute are left remaining.
- Restricted to use just 3 times per day, due to the fact that 3 matches are held at each tournament. However, this design choice did not take into account the existence of multiple lobbies.
- Subject to significant change or removal, possibly to be combined with `/win`; see [our recommendations for future development](#highest-priority-fixes--changes).


### /finishvoting 🛡️

- Admin-only. Forces the voting period to finish so that the highest-voted person is immediately chosen as MVP.
- Subject to removal pending alteration of overall MVP functionality


### /cancelvoting 🛡️

- Admin-only. Cancels the voting period so no MVP is selected.
- Subject to removal pending alteration of overall MVP functionality





# Recommendations for Further Development

The following is a list of recommendations by our team for future capstone students looking to improve upon the bot. Any of these that significantly alter the bot's user experience should be double-checked with sponsors to ensure they are implemented in line with KSU eSports' objectives.

### Highest Priority Fixes / Changes
- In the current version of the bot, the `/matchmake` command is non-functional, as tiers are not being correctly stored/retrieved from the database despite their assignment through `.env`. This should be the number one priority for any future development on this version of the bot.
- Rework / finish implementation of MVP voting to allow for multiple voting pools, as the current matchmaking implementation provides for creation of multiple lobbies with concurrently-running matches. In other words, users with the "Player" and "Volunteer" from different lobbies should each be able to vote for MVPs only within their own lobby. A possible solution for this is tying MVP voting directly to the `/win` command, but there should also be functionality for users to vote for an "ace" (MVP on the losing team). Two rows of buttons could pop up with players' usernames, one row showing winning team voting options and one row showing losing team members as voting options.
- `/points` currently increases "Participation" value in the database for all users that currently have the "Player" and "Volunteer" roles, and is intended to be typed once a match has completed. However, this functionality could be merged into an improved version of `/win` that along with MVP voting.

### Simple / Short-term Improvements
- Screenshots can be included in a GitHub repository subfolder and embedded in README.md, simplifying the bot setup process.
- When creating the bot application, specify just the bot permissions that are actually needed instead of using "Administrator", as this is not considered best practice.
- /stats embed UI could be improved to display a user's full ranking information (for example, GOLD II instead of just GOLD). This change would necessitate documentation specifying that different tiers within ranks do not affect matchmaking, however.
- A possible UX improvement is combining /checkin and /sitout (formerly /volunteer) into a single command with 3 buttons.
- When `/resetdb` is entered twice within 10 seconds (i.e. successfully performing a reset), the initial confirmation message is erroneously sent a second time along with the message announcing a successful reset. The 10-second expiration message is also sent afterward, despite the reset already being carried out. This command could also be reworked to remove the need for an import of the "datetime" library.
- All commands except for `/help` are supposed to be disabled for users who haven't used `/link`, and other commands which alter the database are intended to be admin-only. However, more testing should be done to ensure that this is the case. Currently `/rolepreference` is completely impossible for unlinked users to enter so it at least is working perfectly.
- Currently, Discord usernames (technically regarded by Discord as "display names" not usernames) are stored by the bot's database and corresponding Excel sheet just so users are more recognizable to admins. The bot has a function `update_username()` which is called when someone types `/stats` for a user, and also whenever a user presses a button to check in or sit out from a matchmaking lobby. These calls effectively prevent someone from joining matchmaking while their username in the DB is out-of-date, but there should still be a function to check for username updates on a timed basis without players needing to use commands first.
- Similarly, the function to update the Excel sheet `update_excel()` is only called for a player when `/stats` is used on them, meaning it only gets updated 1 player at a time. This isn't crucial as this spreadsheet is not used by the bot's backend in any way, but for anyone wanting to view all player data without a way of opening the database it is highly problematic as /stats would need to be typed for every player, every time one of their statistics is updated to keep the sheet perfectly up to date. We recommend implementing functionality to update the sheet on a timed basis, i.e. once per hour.
- The bot could automatically create a channel (e.g. #registration) if it does not already exist, and use Discord's "modal" functionality to show users a form having them enter/update both their Riot ID and role preferences simultaneously.


### Long-term / Complex Development Goals
- Most, if not all, of the bot's commands currently have a `guild` parameter set to `discord.Object(GUILD)` (i.e the guild token users paste into `.env`). This restricts the bot's functions to the single server that has an ID in your `.env` file. A future capstone team could conceivably alter the code to handle multiple, comma-separated guild IDs in `.env`, but a better solution would be to allow *global* commands by removing the guild parameters along with the `GUILD_TOKEN` in .env. The reason we don't do this now is because "global" slash (/) commands can take up to an hour to appear across the various servers that a bot is added to, and this is problematic for testing purposes. We only recommend making a command global if a future team improves it to an ideal state after which it needs no significant testing/improvement. The `GUILD_TOKEN` field in `.env` could also be used as an optional field for developers to specify a testing server, so unstable ones can be restricted to it, while other, stable ones can be left global (i.e for use in the KSU League of Legends / TFT server).
- Finish implementation of Docker support to provide a convenient and more portable alternative to normal setup.
