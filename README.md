# Daily Challenge Discord Bot

A fun and interactive bot that posts daily challenges and tracks user participation with XP rewards and streaks.
(My goal of this project was to learn a bit about SQL)

[Watch Demo Video](https://dailychallengebot.amsky.xyz/demo.mp4)

## Features

- **Daily Challenges**: Automatically posts new challenges every day
- **XP & Rewards**: Earn 10 XP per completed challenge
- **Streaks**: Track consecutive days of completed challenges
- **Leaderboard**: See top participants with `/leaderboard`
- **User Submissions**: Suggest challenges with `/suggest`
- **Admin Controls**: Approve user submissions with `/approve`
- **User Profiles**: Check your stats with `/profile`

## Setup Instructions

### Prerequisites
- Python 3.10+
- Discord bot token

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/c2y5/DailyChallengeBot.git
   cd DailyChallengeBot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file:
   ```ini
   TOKEN=your_discord_bot_token
   AI_API_KEY=your_openai_api_key
   AI_API_URL=https://api.openai.com/v1/chat/completions
   ```

4. Run the bot:
   ```bash
   python main.py
   ```

5. Setup the bot with your server
   ```
   /setup <challenge_channel> <response_channel> <suggestion_channel>
   ```

## Bot Commands

### User Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/challenge [category]` | Get today's challenge | `/challenge Art` |
| `/complete` | Mark challenge as completed | `/complete` |
| `/profile` | View your challenge stats | `/profile` |
| `/leaderboard` | Show top participants | `/leaderboard` |
| `/suggest <challenge> <category>` | Submit a challenge idea | `/suggest "Draw a sunset" Art` |

### Admin Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/setup <challenge_channel> <response_channel> <suggestion_channel>` | Configure bot channels | `/setup #challenges #responses #suggestions` |
| `/approve <challenge_id>` | Approve a user submission | `/approve 42` |

## Customization
- Edit `categories` list in line `109` to change challenge categories
- Modify XP rewards in line `209` function
- Change posting time in line `385`

## License
MIT License - Free to use and modify

---

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## Contributing

Contributions and suggestions are welcome! Please open issues or submit pull requests.
