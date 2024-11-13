import aiohttp
import aiosqlite # Using this package instead of sqlite for asynchronous processing support
import asyncio
from collections import defaultdict
import discord
from discord import AllowedMentions
from discord.ext import commands, tasks
import itertools
import json
from openpyxl import load_workbook
import os
import logging
import random
import requests

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
# Paths to spreadsheet and SQLite database on the bot host's computer
SPREADSHEET_PATH = os.getenv('SPREADSHEET_PATH')
DB_PATH = os.getenv('DB_PATH')


# SQLite connection
async def get_db_connection():
    return await aiosqlite.connect('ksu_esports_bot.db') # POSSIBLY CHANGE THIS TO USE 'DB_PATH' FROM .env LATER

# Function to update the Excel file / spreadsheet for offline database manipulation.
# This implementation (as of 2024-10-25) allows the bot host to update the database by simply altering the
# spreadsheet, and vice versa; changes through the bot / db update the spreadsheet at the specified path in .env.
# Niranjanaa:
from openpyxl import load_workbook

def update_excel(discord_id, player_data, sheet_name):
    try:
        # Load the workbook and get the correct sheet
        workbook = load_workbook(SPREADSHEET_PATH)
        if sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
        else:
            raise ValueError(f'Sheet {sheet_name} does not exist in the workbook')

        # Check if the player already exists in the sheet
        found = False
        for row in sheet.iter_rows(min_row=2):  # Assuming the first row is headers
            if str(row[0].value) == discord_id:  # Check if Discord ID matches
                # Update existing row with player data
                row[0].value = player_data["DiscordID"]
                row[1].value = player_data["DiscordUsername"]
                row[2].value = player_data["PlayerRiotID"]
                row[3].value = player_data["Participation"]
                row[4].value = player_data["Wins"]
                row[5].value = player_data["MVPs"]
                row[6].value = player_data["ToxicityPoints"]
                row[7].value = player_data["GamesPlayed"]
                row[8].value = player_data["WinRate"]
                row[9].value = player_data["TotalPoints"]
                row[10].value = player_data["PlayerTier"]
                row[11].value = player_data["PlayerRank"]
                row[12].value = player_data["RolePreference"]
                found = True
                break

        # If player not found, add a new row
        if not found:
            # Find the first truly empty row, ignoring formatting
            empty_row_idx = None
            for i, row in enumerate(sheet.iter_rows(min_row=2), start=2):
                # Check if all cells in the row are empty (ignoring any formatting)
                if all(cell.value is None for cell in row):
                    empty_row_idx = i
                    break

            # If no truly empty row was found, append to the end
            if empty_row_idx is None:
                empty_row_idx = sheet.max_row + 1

            # Insert the new data into the found empty row
            sheet.cell(row=empty_row_idx, column=1).value = player_data["DiscordID"]
            sheet.cell(row=empty_row_idx, column=2).value = player_data["DiscordUsername"]
            sheet.cell(row=empty_row_idx, column=3).value = player_data["PlayerRiotID"]
            sheet.cell(row=empty_row_idx, column=4).value = player_data["Participation"]
            sheet.cell(row=empty_row_idx, column=5).value = player_data["Wins"]
            sheet.cell(row=empty_row_idx, column=6).value = player_data["MVP Points"]
            sheet.cell(row=empty_row_idx, column=7).value = player_data["ToxicityPoints"]
            sheet.cell(row=empty_row_idx, column=8).value = player_data["GamesPlayed"]
            sheet.cell(row=empty_row_idx, column=9).value = player_data["WinRate"]
            sheet.cell(row=empty_row_idx, column=10).value = player_data["TotalPoints"]
            sheet.cell(row=empty_row_idx, column=11).value = player_data["PlayerTier"]
            sheet.cell(row=empty_row_idx, column=12).value = player_data["PlayerRank"]
            sheet.cell(row=empty_row_idx, column=13).value = player_data["RolePreference"]

        # Save the workbook after updates
        workbook.save(SPREADSHEET_PATH)

    except Exception as e:
        print(f"Error updating Excel file: {e}")

        

# creating db tables if they don't already exist
async def initialize_database():
    async with aiosqlite.connect('ksu_esports_bot.db') as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS "PlayerStats" (
                "DiscordID" TEXT NOT NULL UNIQUE,
                "DiscordUsername" TEXT NOT NULL,
                "PlayerRiotID" TEXT UNIQUE,
                "Participation" NUMERIC DEFAULT 0,
                "Wins" INTEGER DEFAULT 0,
                "MVPs" INTEGER DEFAULT 0,
                "ToxicityPoints" NUMERIC DEFAULT 0,
                "GamesPlayed" INTEGER DEFAULT 0,
                "WinRate" REAL,
                "TotalPoints" NUMERIC DEFAULT 0,
                "PlayerTier" INTEGER DEFAULT 0,
                "PlayerRank" TEXT DEFAULT 'UNRANKED',
                "RolePreference" TEXT DEFAULT '55555',
                PRIMARY KEY("DiscordID")
)
        ''')
        await conn.commit()

RIOT_API_KEY = os.getenv('RIOT_API_KEY')

async def get_encrypted_summoner_id(riot_id):
    """
    Fetches the encrypted summoner ID from the Riot API using Riot ID.
    Args:
    - riot_id: The player's Riot ID in 'username#tagline' format.
    Returns:
    - Encrypted summoner ID (summonerId) if successful, otherwise None.
    """
    # Riot ID is expected to be in the format 'username#tagline'
    if '#' not in riot_id:
        return None

    username, tagline = riot_id.split('#', 1)
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{username}/{tagline}"
    headers = {
        "X-Riot-Token": RIOT_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    puuid = data.get('puuid', None)
                    if puuid:
                        # Use the PUUID to fetch the encrypted summoner ID
                        summoner_url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
                        async with session.get(summoner_url, headers=headers) as summoner_response:
                            if summoner_response.status == 200:
                                summoner_data = await summoner_response.json()
                                encrypted_summoner_id = summoner_data.get('id', None)  # The summonerId is referred to as `id` in this response
                                return encrypted_summoner_id
                            else:
                                print(f"Error fetching summoner data: {summoner_response.status}, response: {await summoner_response.text()}")
                                return None
                else:
                    print(f"Error fetching encrypted summoner ID: {response.status}, response: {await response.text()}")
                    return None
    except Exception as e:
        print(f"An error occurred while connecting to the Riot API: {e}")
        return None


    """
    Fetches the player's rank from Riot API and updates it in the database.
    Args:
    - conn: The aiosqlite connection object.
    - discord_id: The player's Discord ID.
    - encrypted_summoner_id: The player's encrypted summoner ID.
    - max_retries was added because sometimes the bot failed to connect to the Riot API and properly pull player rank etc (which was leading to rank showing as N/A in /stats.)
      Now, the bot automatically retries the connection several times if this occurs.
    """
async def update_player_rank(conn, discord_id, encrypted_summoner_id):
    # Initial delay before making the API call
    await asyncio.sleep(3)  # Wait for 3 seconds before the first attempt
    
    url = f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{encrypted_summoner_id}"
    headers = {
        "X-Riot-Token": RIOT_API_KEY
    }

    max_retries = 3  # Number of retry attempts

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for entry in data:
                            if entry.get("queueType") == "RANKED_SOLO_5x5":
                                # Extract only the tier for the rank (e.g., "GOLD")
                                rank = entry.get('tier', 'N/A')
                                await conn.execute(
                                    "UPDATE PlayerStats SET PlayerRank = ? WHERE DiscordID = ?",
                                    (rank, discord_id)
                                )
                                await conn.commit()
                                return rank
                        return "UNRANKED"
                    else:
                        print(f"Error fetching player rank: {response.status}, response: {await response.text()}")
        except Exception as e:
            print(f"An error occurred while connecting to the Riot API (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Failed attempt {attempt + 1}, retrying in 5 seconds...")
                await asyncio.sleep(5)  # Wait for 5 seconds before retrying

    print("All attempts to connect to the Riot API have failed.")
    return "N/A"  # Return "N/A" if all attempts fail


# On bot ready event
@client.event
async def on_ready():
    
    await initialize_database()
    await tree.sync(guild=discord.Object(GUILD))
    print(f'Logged in as {client.user}')

"""#Logger to catch discord disconects and ignores them.
class GatewayEventFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__('discord.gateway')
    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info is not None and is instance(record.exc_info[1], discord.ConnectionClosed):
            return False
        return True"""

"""
Command to display stats for a given user which simultaneously syncs the user's stats from the database to a spreadsheet (specified in .env) for easy viewing.0
This command pulls and displays some stats from the database, but also makes an API call through update_player_rank() to get the user's updated League of Legends rank.
There is a known error where player rank may display as "N/A" on the command embed due to a connection issue, even if the API key is set up properly. However, typing the command a 1-2 more
times resolves this.
"""
@tree.command(
    name='stats',
    description='Get inhouse stats for a server member who has connected their Riot account with /link.',
    guild=discord.Object(GUILD)  # Replace GUILD with your actual guild ID
)
async def stats(interaction: discord.Interaction, player: discord.Member, sheet_name: str = "PlayerStats"):
    # Check if player name is given
    if not player:
        await interaction.response.send_message("Please provide a player name.", ephemeral=True)
        return

    try:
        # Update the player's Discord username in the database if needed
        await update_username(player)

        # Connect to the database
        async with aiosqlite.connect(DB_PATH) as conn:
            # Fetch stats from the database
            async with conn.execute("SELECT * FROM PlayerStats WHERE DiscordID=?", (str(player.id),)) as cursor:
                player_stats = await cursor.fetchone()

            # If player exists in the database, proceed
            if player_stats:
                riot_id = player_stats[2]  # The Riot ID column from the database

                # Update encrypted summoner ID and rank in the database
                if riot_id:
                    encrypted_summoner_id = await get_encrypted_summoner_id(riot_id)
                    player_rank = await update_player_rank(conn, str(player.id), encrypted_summoner_id) if encrypted_summoner_id else "N/A"
                else:
                    player_rank = "N/A"

                # Create an embed to display player stats
                embed = discord.Embed(
                    title=f"{player.display_name}'s Stats",
                    color=0xffc629  # Hex color #ffc629
                )
                embed.set_thumbnail(url=player.avatar.url if player.avatar else None)

                # Add player stats to the embed
                embed.add_field(name="Riot ID", value=riot_id or "N/A", inline=False)
                embed.add_field(name="Player Rank", value=player_rank, inline=False)
                embed.add_field(name="Participation Points", value=player_stats[3], inline=True)
                embed.add_field(name="Games Played", value=player_stats[7], inline=True)
                embed.add_field(name="Wins", value=player_stats[4], inline=True)
                embed.add_field(name="MVPs", value=player_stats[5], inline=True)
                embed.add_field(name="Win Rate", value=f"{player_stats[8] * 100:.0f}%" if player_stats[8] is not None else "N/A", inline=True)

                await interaction.response.send_message(embed=embed, ephemeral=True)

                # Prepare player data dictionary to pass to update_excel
                player_data = {
                    "DiscordID": player_stats[0],
                    "DiscordUsername": player_stats[1],
                    "PlayerRiotID": player_stats[2],
                    "Participation": player_stats[3],
                    "Wins": player_stats[4],
                    "MVPs": player_stats[5],
                    "ToxicityPoints": player_stats[6],
                    "GamesPlayed": player_stats[7],
                    "WinRate": player_stats[8],
                    "PlayerTier": player_stats[10],
                    "PlayerRank": player_rank,
                    "RolePreference": player_stats[12]
                }

                # Update the Excel sheet in a non-blocking manner
                await asyncio.to_thread(update_excel, str(player.id), player_data, sheet_name)

                await interaction.followup.send(f"Player stats for {player.display_name} have been updated in the Excel sheet '{sheet_name}'.", ephemeral=True)
            else:
                await interaction.response.send_message(f"No stats found for {player.display_name}", ephemeral=True)

    except Exception as e:
        # Log the error or handle it appropriately
        print(f"An error occurred: {e}")
        await interaction.response.send_message("An unexpected error occurred while fetching player stats.", ephemeral=True)
        

# riot ID linking command, role preference command, and other code added by Jackson 10/18/2024 - may not interact with other code tied to matchmaking with ranks/tiers right now, so can be changed or removed later.
# Dropdown menu for role preference selection

# Riot ID linking command. This is the first command users should type before using other bot features, as it creates a record for them in the database.
@tree.command(
    name='link',
    description="Link your Riot ID to your Discord account.",
    guild=discord.Object(GUILD)
)
async def link(interaction: discord.Interaction, riot_id: str):
    member = interaction.user

    # Riot ID is in the format 'username#tagline', e.g., 'jacstogs#1234'
    if '#' not in riot_id:
        await interaction.response.send_message(
            "Invalid Riot ID format. Please enter your Riot ID in the format 'username#tagline'.",
            ephemeral=True
        )
        return

    # Split the Riot ID into name and tagline
    summoner_name, tagline = riot_id.split('#', 1)
    summoner_name = summoner_name.strip()
    tagline = tagline.strip()

    # Verify that the Riot ID exists using the Riot API
    api_key = os.getenv("RIOT_API_KEY")
    headers = {"X-Riot-Token": api_key}
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{summoner_name}/{tagline}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    # Riot ID exists, proceed to link it
                    data = await response.json()  # Get the response data

                    # Debugging: Print the data to see what comes back from the API
                    print(f"Riot API response: {data}")

                    async with aiosqlite.connect(DB_PATH) as conn:
                        # Check if the user already exists in the database
                        async with conn.execute("SELECT * FROM PlayerStats WHERE DiscordID = ?", (str(member.id),)) as cursor:
                            result = await cursor.fetchone()

                        if result:
                            # Update the existing record with the new Riot ID
                            await conn.execute(
                                "UPDATE PlayerStats SET PlayerRiotID = ? WHERE DiscordID = ?",
                                (riot_id, str(member.id))
                            )
                        else:
                            # Insert a new record if the user doesn't exist in the database
                            await conn.execute(
                                "INSERT INTO PlayerStats (DiscordID, DiscordUsername, PlayerRiotID) VALUES (?, ?, ?)",
                                (str(member.id), member.display_name, riot_id)
                            )
                        
                        await conn.commit()

                    await interaction.response.send_message(
                        f"Your Riot ID '{riot_id}' has been successfully linked to your Discord account.",
                        ephemeral=True
                    )
                else:
                    # Riot ID does not exist or other error
                    error_msg = await response.text()
                    print(f"Riot API error response: {error_msg}")
                    await interaction.response.send_message(
                        f"The Riot ID '{riot_id}' could not be found. Please double-check and try again.",
                        ephemeral=True
                    )
    except Exception as e:
        print(f"An error occurred while connecting to the Riot API: {e}")
        await interaction.response.send_message(
            "An unexpected error occurred while trying to link your Riot ID. Please try again later.",
            ephemeral=True
        )


@tree.command(
    name='unlink',
    description="Unlink a player's Riot ID and remove their statistics from the database.",
    guild=discord.Object(GUILD)  # Replace GUILD with your actual guild ID
)
@commands.has_permissions(administrator=True)
async def unlink(interaction: discord.Interaction, player: discord.Member):
    try:
        # Store the player to be unlinked for confirmation
        global player_to_unlink
        player_to_unlink = player
        await interaction.response.send_message(f"Type /confirm if you are sure you want to remove {player.display_name}'s record from the bot database.", ephemeral=True)
    
    except commands.MissingPermissions:
        await interaction.response.send_message("You do not have permission to use this command. Only administrators can unlink a player's account.", ephemeral=True)
    
    except Exception as e:
        # Log the error or handle it appropriately
        print(f"An error occurred: {e}")
        await interaction.response.send_message("An unexpected error occurred while unlinking the account.", ephemeral=True)

@tree.command(
    name='confirm',
    description="Confirm the removal of a player's statistics from the database.",
    guild=discord.Object(GUILD)  # Replace GUILD with your actual guild ID
)
@commands.has_permissions(administrator=True)
async def confirm(interaction: discord.Interaction):
    global player_to_unlink
    try:
        if player_to_unlink:
            # Check if the user exists in the database
            async with aiosqlite.connect(DB_PATH) as conn:
                async with conn.execute("SELECT * FROM PlayerStats WHERE DiscordID = ?", (str(player_to_unlink.id),)) as cursor:
                    player_stats = await cursor.fetchone()

                if player_stats:
                    # Delete user from the database
                    await conn.execute("DELETE FROM PlayerStats WHERE DiscordID = ?", (str(player_to_unlink.id),))
                    await conn.commit()
                    await interaction.response.send_message(f"{player_to_unlink.display_name}'s Riot ID and statistics have been successfully unlinked and removed from the database.", ephemeral=True)
                    player_to_unlink = None
                else:
                    await interaction.response.send_message(f"No statistics found for {player_to_unlink.display_name}. Make sure the account is linked before attempting to unlink.", ephemeral=True)
        else:
            await interaction.response.send_message("No player unlink request found. Please use /unlink first.", ephemeral=True)
    
    except commands.MissingPermissions:
        await interaction.response.send_message("You do not have permission to use this command. Only administrators can confirm the unlinking of a player's account.", ephemeral=True)
    
    except Exception as e:
        # Log the error or handle it appropriately
        print(f"An error occurred: {e}")
        await interaction.response.send_message("An unexpected error occurred while confirming the unlinking of the account.", ephemeral=True)



# Role preference command
class RolePreferenceView(discord.ui.View):
    def __init__(self, member_id, initial_values):
        super().__init__(timeout=60)
        self.member_id = member_id
        self.values = initial_values  # Use the initial preferences from the database
        self.embed_message = None  # Track the embed message to edit later
        roles = ["Top", "Jungle", "Mid", "Bot", "Support"]
        for role in roles:
            self.add_item(RolePreferenceDropdown(role, self))  # Pass the view to the dropdown

    async def update_embed_message(self, interaction):
        # Create an embed to display role preferences
        embed = discord.Embed(title="Role Preferences", color=0xffc629)
        for role, value in self.values.items():
            embed.add_field(name=role, value=f"Preference: {value}", inline=False)

        # Send or edit the ephemeral embed message with the updated preferences
        if self.embed_message is None:
            self.embed_message = await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await self.embed_message.edit(embed=embed)


class RolePreferenceDropdown(discord.ui.Select):
    def __init__(self, role, parent_view: RolePreferenceView):
        self.role = role
        self.parent_view = parent_view  # Reference to the parent view
        options = [
            discord.SelectOption(label=str(i), value=str(i)) for i in range(1, 6)
        ]
        super().__init__(
            placeholder=f"Select your matchmaking priority for {role}",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        # Update the selected value in the parent view's `values` dictionary
        self.parent_view.values[self.role] = int(self.values[0])

        # Concatenate the role preferences into a single string
        role_pref_string = ''.join(str(self.parent_view.values[role]) for role in ["Top", "Jungle", "Mid", "Bot", "Support"])

        # Update the database with the new role preferences
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(
                "UPDATE PlayerStats SET RolePreference = ? WHERE DiscordID = ?",
                (role_pref_string, str(self.parent_view.member_id))
            )
            await conn.commit()

        # Acknowledge interaction
        await interaction.response.defer()  # Acknowledge the interaction without updating the message

        # Update the role preferences embed
        await self.parent_view.update_embed_message(interaction)


@tree.command(
    name='rolepreference',
    description="Set your role preferences for matchmaking.",
    guild=discord.Object(GUILD)
)
async def rolepreference(interaction: discord.Interaction):
    member = interaction.user

    # Check if the user has the Player or Volunteer role
    if not any(role.name in ["Player", "Volunteer"] for role in member.roles):
        await interaction.response.send_message("You must have the Player or Volunteer role to set role preferences.", ephemeral=True)
        return

    # Check if the user is in the database and retrieve their current preferences
    async with aiosqlite.connect(DB_PATH) as conn:
        async with conn.execute("SELECT RolePreference FROM PlayerStats WHERE DiscordID = ?", (str(member.id),)) as cursor:
            user_data = await cursor.fetchone()

        if not user_data:
            await interaction.response.send_message("You need to link your Riot ID using /link before setting role preferences.", ephemeral=True)
            return

    # Convert the existing role preferences into a dictionary
    role_pref_string = user_data[0]
    initial_values = {
        "Top": int(role_pref_string[0]),
        "Jungle": int(role_pref_string[1]),
        "Mid": int(role_pref_string[2]),
        "Bot": int(role_pref_string[3]),
        "Support": int(role_pref_string[4])
    }

    # Create the view with initial values and send initial response
    view = RolePreferenceView(member.id, initial_values)
    await interaction.response.send_message(
        "Please select your roles in order of preference, with 1 being the most preferred:", 
        view=view,
        ephemeral=True
    )



# code to calculate and update winrate in database
async def update_win_rate(discord_id):
    async with await get_db_connection() as conn:
        async with conn.execute("SELECT Wins, GamesPlayed FROM PlayerStats WHERE DiscordID = ?", (discord_id,)) as cursor:
            result = await cursor.fetchone()
    if result:
        wins, games_played = result
        win_rate = (wins / games_played) * 100 if games_played > 0 else 0
        await conn.execute("UPDATE PlayerStats SET WinRate = ? WHERE DiscordID = ?", (win_rate, discord_id))
        await conn.commit()




# end of aforementioned code added by Jackson



# preference weight for ranks in matchmaking
def get_preference_weight(tier):
    tier_weights = {
        "UNRANKED": 0,
        "IRON": 1,
        "BRONZE": 2,
        "SILVER": 3,
        "GOLD": 4,
        "PLATINUM": 5,
        "EMERALD": 6,
        "DIAMOND": 7,
        "MASTER": 8,
        "GRANDMASTER": 9,
        "CHALLENGER": 10
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
    
# Function to update Discord username in the database if it's been changed
async def update_username(player: discord.Member):
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            # Fetch the player's current data from the database
            async with conn.execute("SELECT DiscordUsername FROM PlayerStats WHERE DiscordID=?", (str(player.id),)) as cursor:
                player_stats = await cursor.fetchone()

            # If player exists in the database and the username is outdated, update it
            if player_stats:
                stored_username = player_stats[0]
                current_username = player.display_name

                if stored_username != current_username:
                    await conn.execute(
                        "UPDATE PlayerStats SET DiscordUsername = ? WHERE DiscordID = ?",
                        (current_username, str(player.id))
                    )
                    await conn.commit()
                    print(f"Updated username in database for {player.id} from '{stored_username}' to '{current_username}'.")

    except Exception as e:
        # Log the error or handle it appropriately
        print(f"An error occurred while updating username: {e}")


async def update_points(members):
    async with aiosqlite.connect(DB_PATH) as conn:
        not_found_users = []
        updated_users = []

        # Iterate through all members with Player or Volunteer roles
        for member in members:
            async with conn.execute("SELECT Participation, GamesPlayed FROM PlayerStats WHERE DiscordID = ?", (str(member.id),)) as cursor:
                result = await cursor.fetchone()

            if result:
                participation, games_played = result

                # Check if the member has the Player or Volunteer role
                if any(role.name == "Player" for role in member.roles):
                    # Update both Participation and GamesPlayed for Players
                    await conn.execute(
                        "UPDATE PlayerStats SET Participation = ?, GamesPlayed = ? WHERE DiscordID = ?",
                        (participation + 1, games_played + 1, str(member.id))
                    )
                    updated_users.append(member.display_name)
                elif any(role.name == "Volunteer" for role in member.roles):
                    # Update only Participation for Volunteers
                    await conn.execute(
                        "UPDATE PlayerStats SET Participation = ? WHERE DiscordID = ?",
                        (participation + 1, str(member.id))
                    )
                    updated_users.append(member.display_name)
            else:
                # Add users who are not found in the database to the list
                not_found_users.append(member.display_name)

        await conn.commit()

    return {"success": updated_users, "not_found": not_found_users}
    
async def update_toxicity(member):
    async with aiosqlite.connect(DB_PATH) as conn:
        # Attempt to find the user in the PlayerStats table
        async with conn.execute("SELECT ToxicityPoints FROM PlayerStats WHERE DiscordID = ?", (str(member.id),)) as cursor:
            result = await cursor.fetchone()

        if result:
            toxicity_points = result[0]
            # Increment the ToxicityPoints and update TotalPoints accordingly
            await conn.execute(
                """
                UPDATE PlayerStats 
                SET ToxicityPoints = ?, TotalPoints = (Participation + Wins - ?)
                WHERE DiscordID = ?
                """,
                (toxicity_points + 1, toxicity_points + 1, str(member.id))
            )
            await conn.commit()
            return True  # Successfully updated user

        return False  # User not found

async def check_winners_in_db(winners):
    not_found_users = []
    async with aiosqlite.connect(DB_PATH) as conn:
        for winner in winners:
            # Check if the player exists in the database
            async with conn.execute("SELECT Wins, GamesPlayed FROM PlayerStats WHERE DiscordID = ?", (str(winner.id),)) as cursor:
                result = await cursor.fetchone()

            if not result:
                # Add to not found list
                not_found_users.append(winner)
    
async def update_wins(winners):
    async with aiosqlite.connect(DB_PATH) as conn:
        for winner in winners:
            # Since we already checked for existence, we can directly update
            async with conn.execute("SELECT Wins, GamesPlayed FROM PlayerStats WHERE DiscordID = ?", (str(winner.id),)) as cursor:
                result = await cursor.fetchone()
                if result:
                    wins, games_played = result
                    # Update the Wins and GamesPlayed for the player
                    await conn.execute(
                        "UPDATE PlayerStats SET Wins = ?, GamesPlayed = ? WHERE DiscordID = ?",
                        (wins + 1, games_played + 1, str(winner.id))
                    )

        await conn.commit()

#Command to start check-in
@tree.command(
    name = 'checkin',
    description = 'Initiate tournament check-in',
    guild = discord.Object(GUILD))
async def checkin(interaction: discord.Interaction):
    player = interaction.user
    
    # Upon checking in, update the player's Discord username in the database if it has been changed
    await update_username(player)
    
    view = CheckinButtons()
    await interaction.response.send_message('Check-in for the tournament has started! You have 15 minutes to check in.', view = view)

#Command to start volunteer
@tree.command(
    name = 'volunteer',
    description = 'Initiate check for volunteers',
    guild = discord.Object(GUILD))
async def volunteer(interaction: discord.Interaction):
    player = interaction.user
    
    # Upon volunteering to sit out for a round, update the player's Discord username in the database if it has been changed.
    # This may be redundant if users are eventually restricted from volunteering before they've checked in.
    await update_username(player)
    
    view = volunteerButtons()
    await interaction.response.send_message('The Volunteer check has started! You have 15 minutes to volunteer if you wish to sit out.', view = view)

@tree.command(
    name='toxicity',
    description='Give a user a point of toxicity (subtracting 1 from their total League inhouse points).',
    guild=discord.Object(GUILD)
)
@commands.has_permissions(administrator=True)
async def toxicity(interaction: discord.Interaction, member: discord.Member):
    try:
        # Defer the response to prevent interaction timeout
        await interaction.response.defer(ephemeral=True)

        # Update the toxicity points in the database
        found_user = await update_toxicity(member)

        if found_user:
            await interaction.followup.send(f"{member.display_name}'s toxicity points have been updated.")
        else:
            await interaction.followup.send(f"{member.display_name} could not be found in the database.")
    except commands.MissingPermissions:
        await interaction.response.send_message("You do not have permission to use this command. Only administrators can give toxicity points.", ephemeral=True)
    except Exception as e:
        print(f'An error occurred: {e}')
        await interaction.followup.send("An unexpected error occurred while updating toxicity points.", ephemeral=True)

@tree.command(
    name='wins',
    description="Updates the number of wins for each player on a winning team.",
    guild=discord.Object(GUILD)
)
@commands.has_permissions(administrator=True)
async def wins(interaction: discord.Interaction, player_1: discord.Member, player_2: discord.Member, player_3: discord.Member, player_4: discord.Member, player_5: discord.Member):
    try:
        winners = [player_1, player_2, player_3, player_4, player_5]
        await interaction.response.defer(ephemeral=True)

        not_found_users = await check_winners_in_db(winners)

        if not_found_users:
            missing_users = ", ".join([user.display_name for user in not_found_users])
            await interaction.followup.send(f"The following players could not be found in the database, so no wins were updated: \n{missing_users}")
        else:
            await update_wins(winners)
            await interaction.followup.send("All winners' 'win' points have been updated.")

    except commands.MissingPermissions:
        await interaction.response.send_message("You do not have permission to use this command. Only administrators can update players' wins.", ephemeral=True)

    except Exception as e:
        print(f'An error occurred: {e}')
        await interaction.followup.send("An error occurred while updating wins.", ephemeral=True)

       
# Slash command to remove all users from the Player and Volunteer roles.
@tree.command(
    name='clear',
    description='Remove all users from Player and Volunteer roles.',
    guild=discord.Object(GUILD)
)
async def remove(interaction: discord.Interaction):
    try:
        player = get(interaction.guild.roles, name='Player')
        volunteer = get(interaction.guild.roles, name='Volunteer')

        # Acknowledge the interaction to avoid timeouts.
        await interaction.response.defer(ephemeral=True)

        permission_issue = False

        # Iterate through all members and attempt to remove roles
        for user in interaction.guild.members:
            try:
                if player in user.roles:
                    await user.remove_roles(player)
                if volunteer in user.roles:
                    await user.remove_roles(volunteer)
            except discord.Forbidden:
                # If a permission error occurs, set the flag
                permission_issue = True
                print(f"Could not remove roles from {user.display_name}. Check role hierarchy.")

        # Prepare the response message
        if permission_issue:
            response_message = (
                "Attempted to remove Player and Volunteer roles from all users.\n"
                "Some users could not be updated due to role hierarchy or missing permissions."
            )
        else:
            response_message = "All users have been successfully removed from Player and Volunteer roles."

        # Send the follow-up message to the user
        await interaction.followup.send(response_message, ephemeral=True)

    except Exception as e:
        print(f'An error occurred: {e}')
        await interaction.followup.send("An unexpected error occurred while removing roles from users.", ephemeral=True)

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
    description='Give participation points to all players and volunteers.',
    guild=discord.Object(GUILD)
)
@commands.has_permissions(administrator=True)
async def points(interaction: discord.Interaction):
    try:
        # Finds all players and volunteers in Discord, adds them to respective lists
        player_role = get(interaction.guild.roles, name='Player')
        volunteer_role = get(interaction.guild.roles, name='Volunteer')

        players_and_volunteers = [
            member for member in interaction.guild.members
            if player_role in member.roles or volunteer_role in member.roles
        ]

        await interaction.response.defer(ephemeral=True)

        # Update points for all players and volunteers
        update_result = await update_points(players_and_volunteers)

        # Send followup messages
        if update_result["success"]:
            updated_users = ', '.join(update_result["success"])
            await interaction.followup.send(f"Participation points have been updated for the following users: {updated_users}.", ephemeral=True)
            print(f"Participation points have been updated for the following users: {updated_users}")
        
        if update_result["not_found"]:
            not_found_users = ', '.join(update_result["not_found"])
            await interaction.followup.send(f"The following users were not found in the database: {not_found_users}.", ephemeral=True)
            print(f"The following users were not found in the database: {not_found_users}")
            
    except commands.MissingPermissions:
        await interaction.response.send_message("You do not have permission to use this command. Only administrators can update players' participation points.", ephemeral=True)
        
    except Exception as e:
        print(f'An error occurred: {e}')
        await interaction.followup.send("An unexpected error occurred while updating participation points.", ephemeral=True)


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

def has_roles(team, required_roles):
    # Create a set of roles present in the team
    team_roles = {player.role for player in team}
    # Check if all required roles are in the team_roles set
    return all(role in team_roles for role in required_roles)

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
    if has_roles(team, ["top", "jungle", "mid", "bot", "support"]):
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



# Below: some randomization code Daniel was messing around with

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
# end of Daniel's randomization code



# code for MVP voting command/functions added by Jackson -- updated morning of 10/18/2024
# Dict that tracks votes after someone initiates an MVP voting session with /votemvp
votes = defaultdict(int)
has_voted = set()  # Tracks players who've already voted
voting_in_progress = False  # Checks if an MVP voting session is already running
mvp_updates_today = 0  # Track the number of MVP updates today (max 3 per day)

# Start an MVP voting period
@tasks.loop(count=1)
async def start_voting(initial_message: discord.Message):
    global voting_in_progress, mvp_updates_today
    voting_in_progress = True

    # Send countdown warnings
    await asyncio.sleep(120)  # Wait for 2 minutes
    await initial_message.channel.send("There are only **3 minutes** remaining for MVP voting!", ephemeral=False)
    
    await asyncio.sleep(60)  # Wait for 1 minute
    await initial_message.channel.send("There are only **2 minutes** remaining for MVP voting!", ephemeral=False)
    
    await asyncio.sleep(60)  # Wait for 1 minute
    await initial_message.channel.send("There is only **1 minute** remaining for MVP voting!", ephemeral=False)

    await asyncio.sleep(60)  # Wait for the final minute to end

    async with await get_db_connection() as conn:
        # Calculate MVP based on votes
        if votes:
            max_votes = max(votes.values())
            mvp_candidates = [player for player, count in votes.items() if count == max_votes]
            
            # Update MVPs in the database
            for mvp in mvp_candidates:
                await conn.execute("UPDATE PlayerStats SET MVPs = MVPs + 1 WHERE DiscordUsername = ?", (mvp,))
            await conn.commit()

            # Prepare MVP result message
            if len(mvp_candidates) == 1:
                await initial_message.channel.send(f"🎉 {mvp_candidates[0]} has been voted the MVP of this round! 🎉", ephemeral=False)
            else:
                mvp_list = ", ".join(mvp_candidates)
                await initial_message.channel.send(f"🎉 The MVP(s) with the highest votes are: {mvp_list}. 🎉", ephemeral=False)

            mvp_updates_today += 1
        else:
            await initial_message.channel.send("No votes were cast. No MVP this round.", ephemeral=False)
    
    votes.clear()
    has_voted.clear()
    voting_in_progress = False

# /votemvp command
@tree.command(
    name='votemvp',
    description='Vote for the MVP of your match',
    guild=discord.Object(GUILD)
)
async def votemvp(interaction: discord.Interaction, player: discord.Member):
    global voting_in_progress, mvp_updates_today
    member = interaction.user

    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            # Ensure the user has linked their Riot ID
            async with conn.execute("SELECT PlayerRiotID FROM PlayerStats WHERE DiscordID = ?", (str(member.id),)) as cursor:
                linked_account = await cursor.fetchone()
            if not linked_account or not linked_account[0]:
                await interaction.response.send_message("You must link your Riot ID before participating in MVP voting. Use `/link` to link your account.", ephemeral=True)
                return

            # Ensure voting is not exceeding the 3 MVP updates limit per day
            if mvp_updates_today >= 3:
                await interaction.response.send_message("The maximum number of MVP votes for today has been reached.", ephemeral=True)
                return

            # Ensure the user has the Player or Volunteer role
            if not any(role.name in ["Player", "Volunteer"] for role in member.roles):
                await interaction.response.send_message("You do not have the necessary role to vote.", ephemeral=True)
                return

            # Register the vote
            votes[player.display_name] += 1
            has_voted.add(member.id)

            # Notify everyone about the vote, mentioning both parties without notifications
            allowed_mentions = discord.AllowedMentions(users=False)
            await interaction.response.send_message(
                f"{member.mention} has voted for {player.mention}.",
                allowed_mentions=allowed_mentions,
                ephemeral=False
            )

            # If there's no voting session currently active, initiate one
            if not voting_in_progress:
                # Get Player and Volunteer roles
                player_role = discord.utils.get(interaction.guild.roles, name="Player")
                volunteer_role = discord.utils.get(interaction.guild.roles, name="Volunteer")
                if not player_role or not volunteer_role:
                    await interaction.followup.send("Player or Volunteer roles are not configured properly.", ephemeral=True)
                    return

                # Mention Player and Volunteer roles
                mentions = f"{player_role.mention} {volunteer_role.mention}"
                
                # Set allowed_mentions to explicitly mention roles
                allowed_mentions_roles = discord.AllowedMentions(roles=True)

                # Send voting initiation message with role mentions to everyone
                initial_message = await interaction.followup.send(
                    f"MVP voting has started! You have 5 minutes to vote using `/votemvp [username]`. {mentions}",
                    allowed_mentions=allowed_mentions_roles,
                    ephemeral=False
                )

                # Start the voting session loop
                start_voting.start(initial_message)

    except Exception as e:
        print(f"An error occurred: {e}")
        await interaction.response.send_message("An unexpected error occurred while processing your vote.", ephemeral=True)

@tree.command(
    name='viewvotes',
    description='View the current MVP votes for the ongoing voting session.',
    guild=discord.Object(GUILD)  # Replace GUILD with your actual guild ID
)
async def viewvotes(interaction: discord.Interaction):
    global voting_in_progress
    if not voting_in_progress:
        await interaction.response.send_message("No voting session is currently active.", ephemeral=True)
        return

    # Create an embed to show the current votes
    embed = discord.Embed(title="🗳️ MVP Votes", color=0xffc629)

    # Add a field for each player who has received votes
    for player, count in votes.items():
        voters = [name for name in votes if votes[name] == count]
        voters_list = ', '.join(voters) if voters else "No votes yet"
        embed.add_field(name=player, value=f"Votes: {count}\n{voters_list}", inline=False)
    
    # Calculate remaining time in voting session
    remaining_time = start_voting.next_iteration - discord.utils.utcnow()
    minutes, seconds = divmod(int(remaining_time.total_seconds()), 60)
    embed.set_footer(text=f"Time remaining: {minutes} minutes and {seconds} seconds")

    await interaction.response.send_message(embed=embed, ephemeral=False)


# Admin command to cancel the voting session
@tree.command(
    name='cancelvoting',
    description='Cancel the current MVP voting session. (Admin Only)',
    guild=discord.Object(GUILD)
)
@commands.has_permissions(administrator=True)
async def cancelvoting(interaction: discord.Interaction):
    global voting_in_progress, votes, has_voted

    if voting_in_progress:
        start_voting.cancel()  # Cancel the ongoing voting loop
        voting_in_progress = False
        votes.clear()
        has_voted.clear()
        await interaction.response.send_message("The MVP voting session has been cancelled, and all votes have been discarded.", ephemeral=False)
    else:
        await interaction.response.send_message("There is no voting session currently active to cancel.", ephemeral=True)

# Admin command to finish the voting session immediately
@tree.command(
    name='finishvoting',
    description='Finish the current MVP voting session and award the MVP. (Admin Only)',
    guild=discord.Object(GUILD)
)
@commands.has_permissions(administrator=True)
async def finishvoting(interaction: discord.Interaction):
    if voting_in_progress:
        await finish_voting(interaction)
    else:
        await interaction.response.send_message("There is no voting session currently active to finish.", ephemeral=True)

# Function to finish voting and determine MVP
async def finish_voting(interaction):
    global voting_in_progress, mvp_updates_today, votes, has_voted

    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            # Calculate MVP based on votes
            if votes:
                max_votes = max(votes.values())
                mvp_candidates = [player for player, count in votes.items() if count == max_votes]
                
                # Update MVPs in the database
                for mvp in mvp_candidates:
                    await conn.execute("UPDATE PlayerStats SET MVPs = MVPs + 1 WHERE DiscordUsername = ?", (mvp,))
                await conn.commit()

                # Prepare MVP result message
                if len(mvp_candidates) == 1:
                    await interaction.channel.send(f"🎉 {mvp_candidates[0]} has been voted the MVP of this round! 🎉")
                else:
                    mvp_list = ", ".join(mvp_candidates)
                    await interaction.channel.send(f"🎉 The MVP(s) with the highest votes are: {mvp_list}. 🎉")

                mvp_updates_today += 1
            else:
                await interaction.channel.send("No votes were cast. No MVP this round.")

    except Exception as e:
        print(f"An error occurred while finishing voting: {e}")
        await interaction.channel.send("An error occurred while processing the MVP votes.")

    finally:
        votes.clear()
        has_voted.clear()
        voting_in_progress = False


#end of mvp section

#help command section

# /help command with pagination
@tree.command(
    name='help',
    description='Get help for bot commands',
    guild=discord.Object(GUILD)
)
async def help_command(interaction: discord.Interaction):
    pages = [
        discord.Embed(title="Help - Page 1", description="**/link [riot_id]** - Link your Riot ID to your Discord account."),
        discord.Embed(title="Help - Page 2", description="**/rolepreference** - Set your role preferences for matchmaking."),
        discord.Embed(title="Help - Page 3", description="**/checkin** - Initiate tournament check-in."),
        discord.Embed(title="Help - Page 4", description="**/volunteer** - Volunteer to sit out of the current match."),
        discord.Embed(title="Help - Page 5", description="**/wins [player_1] [player_2] [player_3] [player_4] [player_5]** - Add a win for the specified players."),
        discord.Embed(title="Help - Page 6", description="**/toxicity [discord_username]** - Give a user a point of toxicity."),
        discord.Embed(title="Help - Page 7", description="**/clear** - Remove all users from Player and Volunteer roles."),
        discord.Embed(title="Help - Page 8", description="**/players** - Find all players and volunteers currently enrolled in the game."),
        discord.Embed(title="Help - Page 9", description="**/points** - Update participation points in the spreadsheet."),
        discord.Embed(title="Help - Page 10", description="**/matchmake [match_number]** - Form teams for all players enrolled in the game."),
        discord.Embed(title="Help - Page 11", description="**/votemvp [username]** - Vote for the MVP of your match."),
    ]

    current_page = 0

    class HelpView(discord.ui.View):
        def __init__(self, *, timeout=180):
            super().__init__(timeout=timeout)
            self.message = None

        async def update_message(self, interaction: discord.Interaction):
            await interaction.response.defer()  # Defer the response to prevent timeout error
            if self.message:
                await self.message.edit(embed=pages[current_page], view=self)

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
        async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
            nonlocal current_page
            if current_page > 0:
                current_page -= 1
                await self.update_message(interaction)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
        async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
            nonlocal current_page
            if current_page < len(pages) - 1:
                current_page += 1
                await self.update_message(interaction)

    view = HelpView()
    initial_response = await interaction.response.send_message(embed=pages[current_page], view=view, ephemeral=True)
    view.message = await initial_response



#logging.getLogger('discord.gateway').addFilter(GatewayEventFilter())
#starts the bot
client.run(TOKEN)