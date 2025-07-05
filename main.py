# type: ignore

import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import json
import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
import random
import sqlite3
from typing import Dict, Optional

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

Token = os.getenv("TOKEN")

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

def init_db():
    conn = sqlite3.connect("challenges.db")
    c = conn.cursor()
    
    c.execute("""CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0, streak INTEGER DEFAULT 0, 
                 last_completion TEXT, total_completions INTEGER DEFAULT 0)""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS challenges
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 challenge TEXT, category TEXT, 
                 submitted_by INTEGER, approved BOOLEAN DEFAULT 0)""")
    
    conn.commit()
    conn.close()

init_db()

def get_user(user_id: int) -> Optional[Dict]:
    conn = sqlite3.connect("challenges.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return {
            "user_id": user[0],
            "xp": user[1],
            "streak": user[2],
            "last_completion": user[3],
            "total_completions": user[4]
        }
    return None

def update_user(user_id: int, xp: int = 0, completion: bool = False):
    conn = sqlite3.connect("challenges.db")
    c = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    user = get_user(user_id)
    
    if user:
        if completion and user["last_completion"] == today:
            conn.close()
            return
        
        new_xp = user["xp"] + xp
        new_total = user["total_completions"] + (1 if completion else 0)
        
        if completion:
            last_date = datetime.strptime(user["last_completion"], "%Y-%m-%d") if user["last_completion"] else None
            streak = user["streak"]
            
            if last_date and (datetime.now() - last_date).days == 1:
                streak += 1
            elif last_date and (datetime.now() - last_date).days > 1:
                streak = 1
            else:
                streak = 1 if not last_date else streak
                
            c.execute("""UPDATE users SET 
                         xp = ?, streak = ?, last_completion = ?, total_completions = ?
                         WHERE user_id = ?""",
                      (new_xp, streak, today, new_total, user_id))
        else:
            c.execute("""UPDATE users SET xp = ? WHERE user_id = ?""",
                      (new_xp, user_id))
    else:
        streak = 1 if completion else 0
        c.execute("""INSERT INTO users (user_id, xp, streak, last_completion, total_completions)
                     VALUES (?, ?, ?, ?, ?)""",
                  (user_id, xp, streak, today if completion else None, 1 if completion else 0))
    
    conn.commit()
    conn.close()
    
def get_api_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('AI_API_KEY')}"
    }

categories = ["Fitness", "Art", "Photography", "Creativity", "Design", "Adventure", "Travel", "Sports", "Gaming", "Innovation", "DIY"]

def generate_ai_challenge(category: str = None):
    url = os.getenv("AI_API_URL")
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "Respond ONLY with valid JSON: {\"challenge\": \"text\", \"category\": \"category_name\"}"
            },
            {
                "role": "user",
                "content": f"Generate a fun challenge in category: {category or random.choice(categories)}"
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=get_api_headers())
        if response.status_code == 200:
            content = json.loads(response.json()["choices"][0]["message"]["content"])
            return content
    except:
        return None

@tree.command(name="setup", description="Set up challenge channels")
@app_commands.describe(challenge_channel="Channel where challenges will be posted", response_channel="Channel for user responses", suggestion_channel="Channel for challenge suggestions")
async def setup(interaction: discord.Interaction, 
                challenge_channel: discord.TextChannel, 
                response_channel: discord.TextChannel,
                suggestion_channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need admin permissions to use this command.", ephemeral=True)
        return
    
    config = {
        "challenge_channel": challenge_channel.id,
        "response_channel": response_channel.id,
        "suggestion_channel": suggestion_channel.id
    }
    
    with open("config.json", "w") as f:
        json.dump(config, f)
    
    await interaction.response.send_message(
        f"Challenges will be posted in {challenge_channel.mention}\n"
        f"Responses in {response_channel.mention}\n"
        f"Suggestions in {suggestion_channel.mention}",
        ephemeral=True
    )

@tree.command(name="challenge", description="Force generate a new challenge")
@app_commands.describe(category="Optional category for the challenge")
async def get_challenge(interaction: discord.Interaction, category: str = None):
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        response_channel = bot.get_channel(config["response_channel"])
    except:
        response_channel = None
    
    challenge = generate_ai_challenge(category)
    if not challenge:
        await interaction.response.send_message("❌ Failed to generate challenge. Try again later.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🎯 Daily Challenge",
        description=challenge["challenge"],
        color=discord.Color.blurple()
    )
    embed.add_field(name="Category", value=challenge["category"])
    
    if response_channel:
        embed.add_field(
            name="How to Complete",
            value=f"1. Post your response in {response_channel.mention}\n"
                  f"2. Use `/complete` when done",
            inline=False
        )
    
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="complete", description="Mark today's challenge as completed")
async def complete_challenge(interaction: discord.Interaction):
    user = interaction.user
    user_data = get_user(user.id)
    today = datetime.now().strftime("%Y-%m-%d")

    if user_data and user_data["last_completion"] == today:
        embed = discord.Embed(
            title="⏭️ Already Completed",
            description="You've already completed today's challenge!",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    update_user(user.id, xp=10, completion=True)
    user_data = get_user(user.id)

    embed = discord.Embed(
        title="✅ Challenge Completed!",
        description=f"{user.mention} earned **10 XP**!\nStreak: {user_data['streak']} days",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@tree.command(name="profile", description="Check your challenge progress")
async def profile(interaction: discord.Interaction):
    user_data = get_user(interaction.user.id)
    if not user_data:
        await interaction.response.send_message("You haven't completed any challenges yet!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"{interaction.user.display_name}'s Challenge Profile",
        color=discord.Color.blue()
    )
    embed.add_field(name="XP", value=user_data["xp"])
    embed.add_field(name="Current Streak", value=f"{user_data['streak']} days")
    embed.add_field(name="Total Completions", value=user_data["total_completions"])
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="leaderboard", description="Show top challenge participants")
async def leaderboard(interaction: discord.Interaction):
    conn = sqlite3.connect("challenges.db")
    c = conn.cursor()
    c.execute("SELECT user_id, xp, streak FROM users ORDER BY xp DESC LIMIT 10")
    top_users = c.fetchall()
    conn.close()
    
    if not top_users:
        await interaction.response.send_message("No challenge data yet!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🏆 Challenge Leaderboard",
        description="Top participants by XP",
        color=discord.Color.gold()
    )
    
    for i, (user_id, xp, streak) in enumerate(top_users, 1):
        user = await bot.fetch_user(user_id)
        embed.add_field(
            name=f"{i}. {user.display_name}",
            value=f"XP: {xp} | Streak: {streak} days",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="suggest", description="Suggest a new challenge")
@app_commands.describe(challenge="Your challenge idea", category="Category for your challenge")
async def suggest_challenge(interaction: discord.Interaction, challenge: str, category: str):
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except:
        await interaction.response.send_message("❌ Channels haven't been set up yet.", ephemeral=True)
        return
    
    conn = sqlite3.connect("challenges.db")
    c = conn.cursor()
    c.execute("""INSERT INTO challenges (challenge, category, submitted_by)
                 VALUES (?, ?, ?)""",
              (challenge, category, interaction.user.id))
    challenge_id = c.lastrowid
    conn.commit()
    conn.close()
    
    suggestion_channel = bot.get_channel(config["suggestion_channel"])
    if suggestion_channel:
        embed = discord.Embed(
            title=f"New Challenge Suggestion (#{challenge_id})",
            description=challenge,
            color=discord.Color.orange()
        )
        embed.add_field(name="Category", value=category)
        embed.add_field(name="Submitted By", value=interaction.user.mention)
        embed.set_footer(text=f"Use /approve {challenge_id} to approve this suggestion")
        
        await suggestion_channel.send(embed=embed)
    
    await interaction.response.send_message(
        f"✅ Your challenge has been submitted (ID: {challenge_id})!",
        ephemeral=True
    )

@tree.command(name="approve", description="Approve a user-submitted challenge (Admin only)")
@app_commands.describe(
    challenge_id="ID of the challenge to approve"
)
async def approve_challenge(interaction: discord.Interaction, challenge_id: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need admin permissions to use this command.", ephemeral=True)
        return
    
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except:
        await interaction.response.send_message("❌ Channels haven't been set up yet.", ephemeral=True)
        return
    
    conn = sqlite3.connect("challenges.db")
    c = conn.cursor()
    c.execute("UPDATE challenges SET approved = 1 WHERE id = ?", (challenge_id,))
    conn.commit()
    conn.close()
    
    await interaction.response.send_message(
        f"✅ Challenge #{challenge_id} has been approved!",
        ephemeral=True
    )

@tasks.loop(hours=24)
async def post_daily_challenge():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        
        channel = bot.get_channel(config["challenge_channel"])
        response_channel = bot.get_channel(config["response_channel"])
        if not channel or not response_channel:
            return
        
        conn = sqlite3.connect("challenges.db")
        c = conn.cursor()
        c.execute("SELECT * FROM challenges WHERE approved = 1 ORDER BY RANDOM() LIMIT 1")
        user_challenge = c.fetchone()
        
        if user_challenge:
            challenge = {
                "challenge": user_challenge[1],
                "category": user_challenge[2]
            }
            submitter = await bot.fetch_user(user_challenge[3])
            credit = f"\n\n*Submitted by {submitter.mention}*"

            c.execute("DELETE FROM challenges WHERE id = ?", (user_challenge[0],))
            conn.commit()
        else:
            challenge = generate_ai_challenge()
            credit = ""

        conn.close()
        
        if not challenge:
            return
        
        embed = discord.Embed(
            title="🌟 Daily Challenge",
            description=f"{challenge['challenge']}{credit}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Category", value=challenge["category"])
        embed.add_field(
            name="How to Participate",
            value=f"1. Post your response in {response_channel.mention}\n"
                  f"2. Use `/complete` to mark it as done",
            inline=False
        )
        
        await channel.send(embed=embed)
    except Exception as e:
        print(f"Error posting daily challenge: {e}")

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")
    
    now = datetime.now()
    next_run = now.replace(hour=12, minute=0, second=0)
    if now > next_run:
        next_run += timedelta(days=1)
    
    delay = (next_run - now).total_seconds()
    await asyncio.sleep(delay)
    post_daily_challenge.start()

bot.run(Token)