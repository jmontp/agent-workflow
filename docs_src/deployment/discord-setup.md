# Discord Setup

Complete guide to setting up Discord for the AI Agent TDD-Scrum workflow system.

## Overview

The Discord bot provides the primary Human-In-The-Loop interface for controlling the orchestrator and AI agents. This guide walks through the complete setup process.

## Step 1: Create Discord Application

### 1.1 Access Developer Portal

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Enter a name: `AI Agent Workflow` (or your preferred name)
4. Click **"Create"**

### 1.2 Configure Application

1. **General Information** tab:
   - Add a description: "AI Agent TDD-Scrum workflow orchestrator"
   - Upload an icon (optional)
   - Add tags: "productivity", "development" (optional)

2. **OAuth2** tab:
   - Copy the **Client ID** (you'll need this later)

## Step 2: Create Bot

### 2.1 Bot Configuration

1. Navigate to the **"Bot"** tab
2. Click **"Add Bot"**
3. Confirm by clicking **"Yes, do it!"**

### 2.2 Bot Settings

Configure the following settings:

**Public Bot:** ❌ Disabled (keep private)
**Requires OAuth2 Code Grant:** ❌ Disabled
**Presence Intent:** ✅ Enabled
**Server Members Intent:** ✅ Enabled  
**Message Content Intent:** ✅ Enabled

### 2.3 Get Bot Token

1. In the **Token** section, click **"Reset Token"**
2. Copy the token immediately (you won't see it again)
3. Store securely - this is your `DISCORD_BOT_TOKEN`

**Security Note:** Never share your bot token publicly or commit it to version control.

## Step 3: Bot Permissions

### 3.1 Required Permissions

The bot needs these permissions:
- **Send Messages** - Basic communication
- **Use Slash Commands** - Primary command interface
- **Embed Links** - Rich message formatting
- **Read Message History** - Context awareness
- **Manage Threads** - Organize discussions
- **Create Public Threads** - Project discussions

### 3.2 Calculate Permission Integer

Permission integer: `2147484736`

Or use the Discord Permissions Calculator:
1. Go to [Discord Permissions Calculator](https://discordapi.com/permissions.html)
2. Select the permissions listed above
3. Copy the generated integer

## Step 4: Invite Bot to Server

### 4.1 Generate Invite URL

Using OAuth2 URL Generator in the Developer Portal:

1. **OAuth2** → **URL Generator**
2. **Scopes:** Select `bot` and `applications.commands`
3. **Bot Permissions:** Select required permissions (or paste permission integer)
4. Copy the generated URL

### 4.2 Alternative Invite URL

Replace `YOUR_CLIENT_ID` with your actual Client ID:

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=2147484736&scope=bot%20applications.commands
```

### 4.3 Complete Invitation

1. Open the invite URL in your browser
2. Select the Discord server for testing
3. Click **"Continue"**
4. Verify permissions and click **"Authorize"**
5. Complete any CAPTCHA if prompted

## Step 5: Environment Configuration

### 5.1 Set Environment Variable

**Linux/Mac:**
```bash
export DISCORD_BOT_TOKEN="your_bot_token_here"
echo 'export DISCORD_BOT_TOKEN="your_bot_token_here"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
$env:DISCORD_BOT_TOKEN="your_bot_token_here"
[System.Environment]::SetEnvironmentVariable("DISCORD_BOT_TOKEN", "your_bot_token_here", "User")
```

**Windows (Command Prompt):**
```cmd
set DISCORD_BOT_TOKEN=your_bot_token_here
setx DISCORD_BOT_TOKEN "your_bot_token_here"
```

### 5.2 Using .env File (Development)

Create a `.env` file in your project root:

```bash
# .env
DISCORD_BOT_TOKEN=your_bot_token_here
ANTHROPIC_API_KEY=your_anthropic_key  # Optional
GITHUB_TOKEN=your_github_token        # Optional
```

Add to `.gitignore`:
```bash
echo ".env" >> .gitignore
```

## Step 6: Test Bot Connection

### 6.1 Start the Bot

```bash
# From project root
python lib/discord_bot.py
```

### 6.2 Verify Connection

Look for these success messages:
```
INFO - Discord bot started successfully
INFO - Slash commands registered
INFO - Bot is ready and listening for commands
```

### 6.3 Test Commands

In your Discord server, try these commands:

```
/state
/epic "Test epic creation"
```

If the bot responds, your setup is successful!

## Step 7: Production Configuration

### 7.1 Server Setup

For production deployment:

1. **Create a dedicated Discord server** for the workflow
2. **Set up project-specific channels** (auto-created by bot)
3. **Configure user roles** and permissions
4. **Set up logging channels** for monitoring

### 7.2 Channel Organization

The bot automatically creates channels with this pattern:
- `hostname-projectname-general` - Main project discussion
- `hostname-projectname-alerts` - System notifications
- `hostname-projectname-logs` - Detailed operation logs

### 7.3 User Management

Grant appropriate permissions:
- **Workflow Manager:** Full access to all commands
- **Developer:** Access to project-specific commands
- **Observer:** Read-only access to status commands

## Troubleshooting

### Common Issues

**Bot doesn't appear online:**
- Verify bot token is correct
- Check network connectivity
- Ensure intents are enabled in Developer Portal

**Slash commands not appearing:**
- Wait up to 1 hour for global command registration
- Try in a different server to test guild vs global commands
- Check bot permissions in server settings

**Bot responds with "Unknown interaction":**
- Restart the bot application
- Verify slash command registration in logs
- Check Discord API status

**Permission errors:**
- Verify bot has required permissions in server
- Check channel-specific permission overrides
- Ensure bot role is positioned correctly in hierarchy

### Debug Commands

Test bot functionality:

```bash
# Test Discord connection only
python -c "
import discord
import os
client = discord.Client()
@client.event
async def on_ready():
    print(f'Connected as {client.user}')
    await client.close()
client.run(os.environ['DISCORD_BOT_TOKEN'])
"

# Test slash command registration
python scripts/test-discord-commands.py
```

### Log Analysis

Monitor these log files:
- `logs/discord-bot.log` - Bot operation logs
- `logs/orchestrator.log` - System coordination logs
- `logs/agents/*.log` - Individual agent logs

## Security Best Practices

### Token Management

- **Never commit tokens** to version control
- **Use environment variables** for production
- **Rotate tokens regularly** (quarterly recommended)
- **Limit bot scope** to necessary servers only

### Server Security

- **Enable 2FA** for server administrators
- **Audit permissions** regularly
- **Monitor bot activity** through logs
- **Use private servers** for sensitive projects

### Access Control

- **Restrict command access** using Discord roles
- **Monitor user activity** in workflow channels
- **Log all workflow decisions** for audit trails
- **Regular security reviews** of bot permissions

## Advanced Configuration

### Custom Command Prefix

To use traditional prefix commands alongside slash commands:

```python
# In lib/discord_bot.py
@bot.command(name='status')
async def status_command(ctx):
    await ctx.send("Bot is running!")
```

### Webhook Integration

For external system integration:

```python
# Webhook setup for external notifications
webhook_url = "https://discord.com/api/webhooks/..."
async def send_webhook_notification(message):
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json={"content": message})
```

### Custom Embeds

For rich message formatting:

```python
import discord

embed = discord.Embed(
    title="Sprint Status",
    description="Current sprint progress",
    color=0x00ff00
)
embed.add_field(name="Stories Complete", value="3/5", inline=True)
embed.add_field(name="Time Remaining", value="2 days", inline=True)
await ctx.send(embed=embed)
```

Your Discord bot is now ready to orchestrate AI agents through an intuitive chat interface!