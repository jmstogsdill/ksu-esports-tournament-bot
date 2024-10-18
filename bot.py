import asyncio
import discord
import os
import itertools
import gspread
import logging
import random

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv, find_dotenv
from discord import app_commands
from discord.utils import get

load_dotenv(find_dotenv())
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

TOKEN = os.getenv('BOT_TOKEN')#Gets the bot's password token from the .env file and sets it to TOKEN.
GUILD = os.getenv('GUILD_TOKEN')#Gets the server's id from the .env file and sets it to GUILD.
SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')#Gets the Google Sheets ID from the .env file and sets it to SHEETS_ID.
SHEETS_NAME = os.getenv('GOOGLE_SHEETS_NAME')#Gets the google sheets name from the .env and sets it to SHEETS_NAME
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']#Allows the app to read and write to the google sheet.

-----------
{
    "riotGames": {
    "lolApiKey": "RGAPI-06e58380-2b89-49b0-8bbc-fb9ee9c0e744", 
    "rank": ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER", "EMERALD"], 
    "tier": [1, 2, 3, 4, 5, 6, 7]
    }
},
"discord": {
    discordID": "<<1278960443653623818>>", 
    #"clientSecret": "<<aSrS7YCrCsQmUpRbtLLlDXpF71J0DmC2>>", //IS THIS NEEDED? 
    "OWNER": "<<452664152343707655>>", 
    "token": "<<MTI3ODk2MDQ0MzY1MzYyMzgxOA.Giu-dm.MWs00Unu751IJFJ9qJ-asre9iR2-bJnnhtNAj0>>", 
}
----------

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(GUILD))
    print(f'Logged in as {client.user}')

"""#Logger to catch discord disconects and ignores them.
class GatewayEventFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__('discord.gateway')
    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info is not None and isinstance(record.exc_info[1], discord.ConnectionClosed):
            return False
        return True"""

def get_preference_weight(tier):
    tier_weights = {
"IRON": 1,
"BRONZE": 2,
"SILVER": 3,
"GOLD": 4,
"PLATINUM": 5,
"DIAMOND": 6,
"MASTER": 7,
"GRANDMASTER": 8,
"CHALLENGER": 9,
"EMERALD": 10
    }

return tier_weights.get(tier.upper(), 0)

#Player class.
class Player:
    def __init__(self, tier, username, discord_id, top_priority, jungle_priority, mid_priority, bot_priority, support_priority):
        self.tier = tier
        self.username = username
        self.discord_id = discord_id
        self.top_priority = top_priority
        self.jungle_priority = jungle_priority
        self.mid_priority = mid_priority
        self.bot_priority = bot_priority
        self.support_priority = support_priority
        self.weight = get_preference_weight(tier)

    def __str__(self):
        return f"Player: {self.username} (Tier {self.tier}), Weight: {self.weight}), Top: {self.top_priority}, Jungle: {self.jungle_priority}, Mid: {self.mid_priority}, Bot: {self.bot_priority}, Support: {self.support_priority}"

    def set_roles(self, top_priority, jungle_priority, mid_priority, bot_priority, support_priority):
        self.top_priority = top_priority
        self.jungle_priority = jungle_priority
        self.mid_priority = mid_priority
        self.bot_priority = bot_priority
        self.support_priority = support_priority

#Team class.
class Team:
    def __init__(self, top_laner, jungle, mid_laner, bot_laner, support):
        self.top_laner = top_laner
        self.jungle = jungle
        self.mid_laner = mid_laner
        self.bot_laner = bot_laner
        self.support = support

    def __str__(self):
        return f"Top Laner: {self.top_laner.username} priority: {self.top_laner.top_priority} (Tier {self.top_laner.tier})\nJungle: {self.jungle.username} priority:{self.jungle.jungle_priority} \
              (Tier {self.jungle.tier})\nMid Laner: {self.mid_laner.username} priority: {self.mid_laner.mid_priority} (Tier {self.mid_laner.tier})\nBot Laner: {self.bot_laner.username} \
                  priority: {self.bot_laner.bot_priority} (Tier {self.bot_laner.tier})\nSupport: {self.support.username} priority: {self.support.support_priority} (Tier {self.support.tier})"


def randomize_teams(players):
    random.shuffle(players)
    teams = []
    for i in range(0, len(players), 5):
    if i + 5 <= len(players):
    team = Team(players[i], players[i+1], players[i+2], players[i+3], players[i+4])
    return teams

#Check-in button class for checking in to tournaments.
class CheckinButtons(discord.ui.View):
    # timeout after 900 seconds = end of 15-minute check-in period
    def __init__(self, *, timeout = 900):
        super().__init__(timeout = timeout)
    """
    This button is a green button that is called check in
    When this button is pulled up, it will show the text "Check-In"

    The following output when clicking the button is to be expected:
    If the user already has the player role, it means that they are already checked in.
    If the user doesn't have the player role, it will give them the player role. 
    """
    @discord.ui.button(
            label = "Check-In",
            style = discord.ButtonStyle.green)
    async def checkin(self, interaction: discord.Interaction, button: discord.ui.Button):

        player = get(interaction.guild.roles, name = 'Player')
        member = interaction.user

        if player in member.roles:
            await interaction.response.edit_message(view = self)
            await interaction.followup.send('You have already checked in.', ephemeral=True)
            return "Is already checked in"
        await member.add_roles(player)
        await interaction.response.edit_message(view = self)
        await interaction.followup.send('You have checked in!', ephemeral = True)
        return "Checked in"        

    """
    This button is the leave button. It is used for if the player checked in but has to leave
    The following output is to be expected:

    If the user has the player role, it will remove it and tell the player that it has been removed
    If the user does not have the player role, it will tell them to check in first.
    """
    @discord.ui.button(
            label = "Leave",
            style = discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):

        player = get(interaction.guild.roles, name = 'Player')
        member = interaction.user

        if player in member.roles:
            await member.remove_roles(player)
            await interaction.response.edit_message(view = self)
            await interaction.followup.send('Sorry to see you go.', ephemeral = True)
            return "Role Removed"
        await interaction.response.edit_message(view = self)
        await interaction.followup.send('You have not checked in. Please checkin first', ephemeral = True)
        return "Did not check in yet"

class volunteerButtons(discord.ui.View):
    # timeout after 900 seconds = end of 15-minute volunteer period
    def __init__(self, *, timeout = 900):
        super().__init__(timeout = timeout)
    """
    This button is a green button that is called check in
    When this button is pulled up, it will show the text "Volunteer"

    The following output when clicking the button is to be expected:
    If the user already has the volunteer role, it means that they are already volunteered.
    If the user doesn't have the volunteer role, it will give them the volunteer role. 
    """
    @discord.ui.button(
            label = "Volunteer",
            style = discord.ButtonStyle.green)
    async def checkin(self, interaction: discord.Interaction, button: discord.ui.Button):

        player = get(interaction.guild.roles, name = 'Player')
        volunteer = get(interaction.guild.roles, name = 'Volunteer')
        member = interaction.user

        if player in member.roles:
            await member.remove_roles(player)
        if volunteer in member.roles:
            await interaction.response.edit_message(view = self)
            await interaction.followup.send('You have already volunteered to sit out, if you wish to rejoin click rejoin.', ephemeral=True)
            return "Is already checked in"
        await member.add_roles(volunteer)
        await interaction.response.edit_message(view = self)
        await interaction.followup.send('You have volunteered to sit out!', ephemeral = True)
        return "Checked in"        

    """
    This button is the leave button. It is used for if the player who has volunteer wants to rejoin
    The following output is to be expected:

    If the user has the player role, it will remove it and tell the player that it has been removed
    If the user does not have the volunteer role, it will tell them to volunteer first.
    """
    @discord.ui.button(
            label = "Rejoin",
            style = discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        player = get(interaction.guild.roles, name = 'Player')
        volunteer = get(interaction.guild.roles, name = 'Volunteer')
        member = interaction.user

        if volunteer in member.roles:
            await member.remove_roles(volunteer)
            await member.add_roles(player)
            await interaction.response.edit_message(view = self)
            await interaction.followup.send('Welcome back in!', ephemeral = True)
            return "Role Removed"
        await interaction.response.edit_message(view = self)
        await interaction.followup.send('You have not volunteered to sit out, please volunteer to sit out first.', ephemeral = True)
        return "Did not check in yet"

#Method to write values from a Google Sheets spreadsheet.
def get_values_matchmaking(range_name):
    creds = None
    #Checks for the token.json authentication credentials that is created the first time accessing the spreadsheet.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    #Checks for credentials, and if there are none or are not valid.
    if not creds or not creds.valid:
        #Checks if the credentials exist, have expired, and there is a refresh token.
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        #If none of the above exist, then it will check for the credentials file and check the permissions to access the Google Sheet spreadsheet.
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'src/credentials.json', SCOPES)
            creds = flow.run_local_server(port = 0)
        #Saves the credentials for every run after the first.
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    #Gets the values from the specified cells in the spreadsheet.
    try:
        service = build('sheets', 'v4', credentials = creds)
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId = SHEETS_ID, range = range_name)
            .execute()
        )
        values = result.get('values', [])
        return values
    except HttpError as error:
        print(f'An error occured: {error}')
        return error

#Method to write values from a Google Sheets spreadsheet.
def update_points(interaction, player_users, volunteer_users):
    gs = gspread.oauth()
    range_name = 'A1:J100'
    sh = gs.open(SHEETS_NAME)
    player = get(interaction.guild.roles, name = 'Player')
    volunteer = get(interaction.guild.roles, name = 'Volunteer')
    try:
        values = sh.sheet1.get_values(range_name)
        for i, row in enumerate(values, start = 1):
            for player in player_users:
                if player.lower() == row[0].lower():
                    player_participation = int(row[2])
                    sh.sheet1.update_cell(i, 3, player_participation + 1)
                    current_matches = int(row[7])
                    sh.sheet1.update_cell(i, 8, current_matches + 1)
            for volunteer in volunteer_users:
                if volunteer.lower() == row[0].lower():
                    volunteer_participation = int(row[2])
                    sh.sheet1.update_cell(i, 3, volunteer_participation + 1)
    except HttpError as e:
        (f'An error occured: {e}')
        return e
    
def update_toxicity(interaction, discord_username):
    gs = gspread.oauth()
    range_name = 'A1:J100'
    sh = gs.open(SHEETS_NAME)
    try:
        values = sh.sheet1.get_values(range_name)
        found_user = False
        for i, row in enumerate(values, start = 1):
            if discord_username.lower() == row[0].lower():
                user_toxicity = int(row[5])
                sh.sheet1.update_cell(i, 6, user_toxicity + 1)
                found_user = True
        return found_user   
    except HttpError as e:
        (f'An error occured: {e}')
        return e
    

def check_player(interaction, discord_username):
    gs = gspread.oauth()
    range_name = 'A1:J100'
    sh = gs.open(SHEETS_NAME)
    try:
        values = sh.sheet1.get_values(range_name)
        found_user = False
        for i, row in enumerate(values, start = 1):
            if discord_username.lower() == row[0].lower():
                found_user = True
        return found_user   
    except HttpError as e:
        (f'An error occured: {e}')
        return e
    
def update_wins(interaction, winners):
    gs = gspread.oauth()
    range_name = 'A1:J100'
    sh = gs.open(SHEETS_NAME)
    try:
        wins = []
        for str in winners:
            wins.append(str.lower())

        values = sh.sheet1.get_values(range_name)
        found_users = 0

        for i, row in enumerate(values, start = 1):
            for w in wins:
                if w == row[0].lower():
                    found_users += 1
        if found_users == 5:
            for i, row in enumerate(values, start = 1):
                for w in wins:
                    if w == row[0].lower():
                        user_win = int(row[3])
                        sh.sheet1.update_cell(i, 4, user_win + 1)
            return True
        else:
            return False 
    except HttpError as e:
        (f'An error occured: {e}')
        return e

#Command to start check-in
@tree.command(
    name = 'checkin',
    description = 'Initiate tournament check-in',
    guild = discord.Object(GUILD))
async def checkin(interaction):
    view = CheckinButtons()
    await interaction.response.send_message('Check-in for the tournament has started! You have 15 minutes to check in.', view = view)

#Command to start volunteer
@tree.command(
    name = 'volunteer',
    description = 'Initiate check for volunteers',
    guild = discord.Object(GUILD))
async def volunteer(interaction):
    view = volunteerButtons()
    await interaction.response.send_message('The Volunteer check has started! You have 15 minutes to volunteer if you wish to sit out.', view = view)

@tree.command(
        name = 'toxicity',
        description = 'Give a user a point of toxicity.',
        guild = discord.Object(GUILD))
async def toxicity(interaction: discord.Interaction, discord_username: str):
    try:
        await interaction.response.defer(ephemeral = True)
        await asyncio.sleep(1)
        found_user = update_toxicity(interaction = interaction, discord_username = discord_username)
        if found_user:
            await interaction.followup.send(f"{discord_username}'s toxicity points have been updated.")
        else:
            await interaction.followup.send(f"{discord_username} could not be found.")
    except Exception as e:
        print(f'An error occured: {e}')

@tree.command(
        name = 'wins',
        description = "Adds a point to each winner's 'win' points.",
        guild = discord.Object(GUILD))
async def wins(interaction: discord.Interaction, player_1: str, player_2: str, player_3: str, player_4: str, player_5: str):
    try:
        winners = [player_1, player_2, player_3, player_4, player_5]
        await interaction.response.defer(ephemeral = True)
        await asyncio.sleep(1)
        found_users = update_wins(interaction = interaction, winners = winners)
        if found_users:
            await interaction.followup.send("All winners' 'win' points have been updated.")
        else:
            await interaction.followup.send("At least one of the winners could not be found.")
    except Exception as e:
        print(f'An error occured: {e}')

#Slash command to remove all users from the Player and Volunteer role.
@tree.command(
    name = 'clear',
    description = 'Remove all users from Players and Volunteer roles.',
    guild = discord.Object(GUILD))
async def remove(interaction: discord.Interaction):
    try:
        player = get(interaction.guild.roles, name = 'Player')
        volunteer = get(interaction.guild.roles, name = 'Volunteer')
        await interaction.response.defer(ephemeral = True)
        await asyncio.sleep(1)
        for user in interaction.guild.members:
            if player in user.roles:
                await user.remove_roles(player)
            if volunteer in user.roles:
                await user.remove_roles(volunteer)
        await interaction.followup.send('All users have been removed from roles.')
    except Exception as e:
        print(f'An error occured: {e}')

#Slash command to find and count all of the players and volunteers
@tree.command(
        name='players',
        description='Find all players and volunteers currently enrolled in the game',
        guild = discord.Object(GUILD))
async def players(interaction: discord.Interaction):
    try:
        player_users = []
        player = get(interaction.guild.roles, name = 'Player')
        for user in interaction.guild.members:
            if player in user.roles:
                player_users.append(user.name)
        
        #Finds all volunteers in discord, adds them to a list
        volunteer_users = []
        volunteer = get(interaction.guild.roles, name = 'Volunteer')
        for user in interaction.guild.members:
            if volunteer in user.roles:
                volunteer_users.append(user.name)

        player_count = sum(1 for user in interaction.guild.members if player in user.roles)
        volunteer_count = sum(1 for user in interaction.guild.members if volunteer in user.roles)

        #Embed to display all users who volunteered to sit out.
        embedPlayers = discord.Embed(color = discord.Color.green(), title = 'Total Players')
        embedPlayers.set_footer(text = f'Total players: {player_count}')
        for pl in player_users:
            embedPlayers.add_field(name = '', value = pl)

        embedVolunteers = discord.Embed(color = discord.Color.orange(), title = 'Total Volunteers')
        embedVolunteers.set_footer(text = f'Total volunteers: {volunteer_count}')
        for vol in volunteer_users:
            embedVolunteers.add_field(name = '', value = vol)
        
        next_increment = 10 - (player_count % 10)
        message = ''
        if player_count == 10:
            message += "There is a full lobby with 10 players!"
            embedMessage = discord.Embed(color = discord.Color.dark_green(), title = 'Players/Volunteers')
            embedMessage.add_field(name = '', value = message)
        elif next_increment==10 and player_count!=0:
            message += "There are multiple full lobbies ready!"
            embedMessage = discord.Embed(color = discord.Color.dark_green(), title = 'Players/Volunteers')
            embedMessage.add_field(name = '', value = message)
        elif player_count < 10:
            message += "A full lobby requires at least 10 players!"
            embedMessage = discord.Embed(color = discord.Color.dark_red(), title = 'Players/Volunteers')
            embedMessage.add_field(name = '', value = message)
        else:
            message += f"For a full lobby {next_increment} players are needed or {10-next_increment} volunteers are needed!"
            embedMessage = discord.Embed(color = discord.Color.dark_red(), title = 'Players/Volunteers')
            embedMessage.add_field(name = '', value = message)

        await interaction.response.send_message(embeds = [embedMessage, embedPlayers, embedVolunteers])
    except Exception as e:
        print(f'An error occured: {e}')

@tree.command(
        name='points',
        description='Print data from specific cell value',
        guild = discord.Object(GUILD))
async def points(interaction: discord.Interaction):
    try:
        #Finds all players in discord, adds them to a list
        player_users = []
        player = get(interaction.guild.roles, name = 'Player')
        for user in interaction.guild.members:
            if player in user.roles:
                player_users.append(user.name)
        
        #Finds all volunteers in discord, adds them to a list
        volunteer_users = []
        volunteer = get(interaction.guild.roles, name = 'Volunteer')
        for user in interaction.guild.members:
            if volunteer in user.roles:
                volunteer_users.append(user.name)
        
        await interaction.response.defer(ephemeral = True)
        await asyncio.sleep(1)
        update_points(interaction = interaction, player_users = player_users, volunteer_users = volunteer_users)
        await interaction.followup.send('Updated spreadsheet!')

    except Exception as e:
        print(f'An error occured: {e}')

@tree.command(
    name = 'matchmake',
    description = "Form teams for all players enrolled in the game",
    guild = discord.Object(GUILD))
async def matchmake(interaction: discord.Interaction, match_number: str):
    try:
        #Finds all players in discord, adds them to a list
        player_users = []
        player = get(interaction.guild.roles, name = 'Player')
        for user in interaction.guild.members:
            if player in user.roles:
                player_users.append(user.name)
        
        #Finds all volunteers in discord, adds them to a list
        volunteer_users = []
        volunteer = get(interaction.guild.roles, name = 'Volunteer')
        for user in interaction.guild.members:
            if volunteer in user.roles:
                volunteer_users.append(user.name)

        await interaction.response.defer()
        await asyncio.sleep(8)
        values = get_values_matchmaking('Player Tiers!A1:E100')

        matched_players = []
        for i, row in enumerate(values):
            for player in player_users:
                if player.lower() == row[0].lower():
                    top_prio = 5
                    jg_prio = 5
                    mid_prio = 5
                    bot_prio = 5
                    supp_prio = 5
                    if row[3] == 'fill':
                        top_prio = 1
                        jg_prio = 1
                        mid_prio = 1
                        bot_prio = 1
                        supp_prio = 1
                    roles = row[3].split('/')
                    index = 1
                    for i, role in enumerate(roles):
                        if role.lower() == 'top':
                            top_prio = index
                        if role.lower() == 'jg' or role.lower() == 'jung' or role.lower() == 'jungle':
                            jg_prio = index
                        if role.lower() == 'mid':
                            mid_prio = index
                        if role.lower() == 'bot' or role.lower() == 'adc':
                            bot_prio = index
                        if role.lower() == 'supp' or role.lower() == 'support':
                            supp_prio = index
                        index += 1
                    matched_players.append(Player(tier=row[4],username=row[1],discord_id=row[0], top_priority=top_prio, jungle_priority=jg_prio, mid_priority=mid_prio, bot_priority=bot_prio, support_priority=supp_prio))
        if len(matched_players) % 10!=0:
            if len(matched_players)!=len(player_users):
                await interaction.followup.send("Error: The number of players must be a multiple of 10. A player could also not be found in the spreadsheet.")
                return
            await interaction.followup.send("Error: The number of players must be a multiple of 10.")
            return
        if len(matched_players)!=len(player_users):
            await interaction.followup.send('A player could not be found on the spreadsheet.')
            return
        best_teams = await create_best_teams(matched_players)

        embedLobby2 = None
        embedLobby3 = None
        for i, (team1, team2, team1_priority, team2_priority, diff) in enumerate(best_teams, start=1):
            if i == 1:
                embedLobby1 = discord.Embed(color = discord.Color.from_rgb(255, 198, 41), title = f'Lobby 1 - Match: {match_number}')
                embedLobby1.add_field(name = 'Roles', value = '')
                embedLobby1.add_field(name = 'Team 1', value = '')
                embedLobby1.add_field(name = 'Team 2', value = '')
                embedLobby1.add_field(name = '', value = 'Top Laner')
                embedLobby1.add_field(name = '', value = team1.top_laner.username)
                embedLobby1.add_field(name = '', value = team2.top_laner.username)
                embedLobby1.add_field(name = '', value = 'Jungle')
                embedLobby1.add_field(name = '', value = team1.jungle.username)
                embedLobby1.add_field(name = '', value = team2.jungle.username)
                embedLobby1.add_field(name = '', value = 'Mid Laner')
                embedLobby1.add_field(name = '', value = team1.mid_laner.username)
                embedLobby1.add_field(name = '', value = team2.mid_laner.username)
                embedLobby1.add_field(name = '', value = 'Bot Laner')
                embedLobby1.add_field(name = '', value = team1.bot_laner.username)
                embedLobby1.add_field(name = '', value = team2.bot_laner.username)
                embedLobby1.add_field(name = '', value = 'Support')
                embedLobby1.add_field(name = '', value = team1.support.username)
                embedLobby1.add_field(name = '', value = team2.support.username)
            if i == 2:
                embedLobby2 = discord.Embed(color = discord.Color.from_rgb(255, 198, 41), title = f'Lobby 2 - Match: {match_number}')
                embedLobby2.add_field(name = 'Roles', value = '')
                embedLobby2.add_field(name = 'Team 1', value = '')
                embedLobby2.add_field(name = 'Team 2', value = '')
                embedLobby2.add_field(name = '', value = 'Top Laner')
                embedLobby2.add_field(name = '', value = team1.top_laner.username)
                embedLobby2.add_field(name = '', value = team2.top_laner.username)
                embedLobby2.add_field(name = '', value = 'Jungle')
                embedLobby2.add_field(name = '', value = team1.jungle.username)
                embedLobby2.add_field(name = '', value = team2.jungle.username)
                embedLobby2.add_field(name = '', value = 'Mid Laner')
                embedLobby2.add_field(name = '', value = team1.mid_laner.username)
                embedLobby2.add_field(name = '', value = team2.mid_laner.username)
                embedLobby2.add_field(name = '', value = 'Bot Laner')
                embedLobby2.add_field(name = '', value = team1.bot_laner.username)
                embedLobby2.add_field(name = '', value = team2.bot_laner.username)
                embedLobby2.add_field(name = '', value = 'Support')
                embedLobby2.add_field(name = '', value = team1.support.username)
                embedLobby2.add_field(name = '', value = team2.support.username)
            if i == 3:
                embedLobby3 = discord.Embed(color = discord.Color.from_rgb(255, 198, 41), title = f'Lobby 2 - Match: {match_number}')
                embedLobby3.add_field(name = 'Roles', value = '')
                embedLobby3.add_field(name = 'Team 1', value = '')
                embedLobby3.add_field(name = 'Team 2', value = '')
                embedLobby3.add_field(name = '', value = 'Top Laner')
                embedLobby3.add_field(name = '', value = team1.top_laner.username)
                embedLobby3.add_field(name = '', value = team2.top_laner.username)
                embedLobby3.add_field(name = '', value = 'Jungle')
                embedLobby3.add_field(name = '', value = team1.jungle.username)
                embedLobby3.add_field(name = '', value = team2.jungle.username)
                embedLobby3.add_field(name = '', value = 'Mid Laner')
                embedLobby3.add_field(name = '', value = team1.mid_laner.username)
                embedLobby3.add_field(name = '', value = team2.mid_laner.username)
                embedLobby3.add_field(name = '', value = 'Bot Laner')
                embedLobby3.add_field(name = '', value = team1.bot_laner.username)
                embedLobby3.add_field(name = '', value = team2.bot_laner.username)
                embedLobby3.add_field(name = '', value = 'Support')
                embedLobby3.add_field(name = '', value = team1.support.username)
                embedLobby3.add_field(name = '', value = team2.support.username)

        #Embed to display all users who volunteered to sit out.
        embedVol = discord.Embed(color = discord.Color.blurple(), title = 'Volunteers - Match: ' + match_number)
        for vol in volunteer_users:
            embedVol.add_field(name = '', value = vol)
        if not volunteer_users:
            embedVol.add_field(name = '', value = 'No volunteers.')

        if embedLobby2 == None:
            await interaction.followup.send( embeds = [embedVol, embedLobby1])
        elif embedLobby2 == None and not volunteer_users:
            await interaction.followup.send( embeds = embedLobby1)
        elif embedLobby3 == None:
            await interaction.followup.send( embeds = [embedVol, embedLobby1, embedLobby2])
        elif embedLobby3 == None and not volunteer_users:
            await interaction.followup.send( embeds = [embedLobby1, embedLobby2])
        elif volunteer_users == None:
            await interaction.followup.send( embeds = [embedLobby1, embedLobby2, embedLobby3])
        else:
            await interaction.followup.send( embeds = [embedVol, embedLobby1, embedLobby2, embedLobby3])
        
    except Exception as e:
        print(f'An error occured: {e}')

#creates 2 best team (1 match) which has the lowest score
async def create_best_teams_helper(players):
    if len(players) != 10:
        raise ValueError("The length of players should be exactly 10.")

    lowest_score = float('inf')
    lowest_score_teams = []

    for team1_players in itertools.permutations(players, len(players) // 2):
        team1 = Team(*team1_players)
        team2_players = [player for player in players if player not in team1_players]
        for team2_players_permutations in itertools.permutations(team2_players, len(players) // 2):
            team2 = Team(*team2_players_permutations)

            t1_priority=0
            t1_priority+=team1.top_laner.top_priority**2
            t1_priority+=team1.jungle.jungle_priority**2
            t1_priority+=team1.mid_laner.mid_priority**2
            t1_priority+=team1.bot_laner.bot_priority**2
            t1_priority+=team1.support.support_priority**2
        
            t2_priority=0
            t2_priority+=team2.top_laner.top_priority**2
            t2_priority+=team2.jungle.jungle_priority**2
            t2_priority+=team2.mid_laner.mid_priority**2
            t2_priority+=team2.bot_laner.bot_priority**2
            t2_priority+=team2.support.support_priority**2
            
            diff = (int(team1.top_laner.tier) - int(team2.top_laner.tier)) ** 2 + \
            (int(team1.mid_laner.tier) - int(team2.mid_laner.tier)) ** 2 + \
            (int(team1.bot_laner.tier) - int(team2.bot_laner.tier)) ** 2 + \
            (int(team1.jungle.tier) - int(team2.jungle.tier)) ** 2 + \
            (int(team1.support.tier) - int(team2.support.tier)) ** 2
            
            score = (t1_priority + t2_priority) / 2.5 + diff

            if score < lowest_score:
                lowest_score = score
                lowest_score_teams = [(team1, team2, t1_priority, t2_priority, diff)]
            
            #This can be kept if we want to return multiple games of the same score.
            #elif score == lowest_score:
            #lowest_score_teams.append((team1, team2, team1_priority, team2_priority, diff))

    return lowest_score_teams

#creates best matches for all players
async def create_best_teams(players):
    if len(players)%10!=0:
        return 'Only call this method with 10, 20 30, etc players'
    sorted_players = sorted(players, key=lambda x: x.tier)
    group_size = 10
    num_groups = (len(sorted_players) + group_size - 1) // group_size
    best_teams = []

    for i in range(num_groups):
        group = sorted_players[i * group_size: (i + 1) * group_size]
        best_teams.extend(await create_best_teams_helper(group))

    return best_teams

#calculates the role priorities for all players any given team
async def calculate_team_priority(top,jungle,mid,bot,support):
    priority=0
    priority+=top.top_priority**2
    priority+=jungle.jungle_priority**2
    priority+=mid.mid_priority**2
    priority+=bot.bot_priority**2
    priority+=support.support_priority**2
    return priority

#calculates the score difference in tier for any 2 given teams
async def calculate_score_diff(team1, team2):
    diff = (team1.top_laner.tier - team2.top_laner.tier) ** 2 + \
                     (team1.mid_laner.tier - team2.mid_laner.tier) ** 2 + \
                     (team1.bot_laner.tier - team2.bot_laner.tier) ** 2 + \
                     (team1.jungle.tier - team2.jungle.tier) ** 2 + \
                     (team1.support.tier - team2.support.tier) ** 2
    return diff
def get_roles(role_string):
    role_priorities = {'top': 5, 'jungle': 5, 'mid': 5, 'bot': 5, 'support': 5}
    if role_string == 'fill':
        return {role: 1 for role in role_priorities}
    roles = role_string.split('/')
    for index, role in enumerate(roles, start=1):
        if role.lower() in role_priorities:
            role_priorities[role.lower()] = index
    return role_priorities
# Synergy score based on roles
def calculate_synergy(team):
    if has_roles(team, ["tank", "support", "damage"]):
        return 10  # Higher synergy score
    else:
        return 5  # Lower score for less balanced teams
# Keep a history of team matchups
def calculate_repetition_penalty(team1, team2, previous_matches):
    penalty = 0
    for match in previous_matches:
        if set(team1.players) == set(match.team1.players) or set(team2.players) == set(match.team2.players):
            penalty += 10  # Add a penalty for repetition
    return penalty

# Some randomization code I was messing around with

# Group players by tier (or nearby tiers)
def group_players_by_rank(players):
    tier_groups = {}
    
    # Group players into their respective tiers
    for player in players:
        if player.tier not in tier_groups:
            tier_groups[player.tier] = []
        tier_groups[player.tier].append(player)
    
    return tier_groups
# Shuffle players within each rank group
def shuffle_players_within_tier_groups(tier_groups):
    for tier in tier_groups:
        random.shuffle(tier_groups[tier])
    return tier_groups
# Relax rank restriction by borrowing players from nearby ranks
def balance_tier_groups(tier_groups):
    balanced_groups = []
    remaining_players = []

    # Combine players from adjacent ranks if necessary
    for tier, players in tier_groups.items():
        if len(players) % 10 != 0:
            remaining_players.extend(players)
        else:
            balanced_groups.append(players)

    # If there are leftover players, merge them into nearby groups
    for i in range(0, len(remaining_players), 10):
        group = remaining_players[i:i+10]
        if len(group) == 10:
            balanced_groups.append(group)
        else:
            # Handle edge cases, add these players to nearby tiers
            # Or combine them into a custom group
            pass
    
    return balanced_groups
async def create_random_teams_within_ranks(players):
    # Group players by rank
    tier_groups = group_players_by_rank(players)
    
    # Shuffle players within each tier group for randomization
    tier_groups = shuffle_players_within_tier_groups(tier_groups)
    
    # Balance the tier groups to make sure each group has a multiple of 10 players
    balanced_groups = balance_tier_groups(tier_groups)

    # Now create best teams using random players from each balanced group
    best_teams = []
    for group in balanced_groups:
        if len(group) == 10:
            best_teams.extend(await create_best_teams_helper(group))
        else:
            # Handle incomplete groups or relax rules
            pass
    
    return best_teams





"""
@tree.command(
    name='votemvp',
    description='Vote for the mvp of your match',
    guild = discord.Object(GUILD))
async def voteMVP(interaction: discord.Interaction, player: str):
    await interaction.response.defer(ephemeral=True)
    asyncio.sleep(1)
    found_player = check_player(interaction = interaction, discord_username = player)
    channel = client.get_channel(1207123664168820736)
    user = interaction.user
    if found_player:
        await interaction.followup.send(f'You have voted for {player} to be MVP of the match')
        await channel.send(f'{user} has voted - MVP: {player}')
    else:
        await interaction.followup.send('This player could not be found in the spreadsheet')
"""

#logging.getLogger('discord.gateway').addFilter(GatewayEventFilter())
#starts the bot
client.run(TOKEN)
