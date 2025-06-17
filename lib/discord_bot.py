"""
Discord Bot for AI Agent TDD-Scrum Workflow

Primary Human-In-The-Loop (HITL) interface for command execution,
state visualization, and workflow coordination through Discord.
"""

import os
import logging
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands

# Add scripts directory to Python path for orchestrator import
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class StateView(discord.ui.View):
    """Interactive view for state machine visualization"""
    
    def __init__(self, orchestrator: Orchestrator, project_name: str = "default"):
        super().__init__(timeout=300)
        self.orchestrator = orchestrator
        self.project_name = project_name
    
    @discord.ui.button(label="Allowed Commands", style=discord.ButtonStyle.primary, emoji="📋")
    async def show_allowed_commands(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show commands allowed in current state"""
        result = await self.orchestrator.handle_command("/state", self.project_name)
        if result["success"]:
            allowed_commands = result["state_info"]["allowed_commands"]
            commands_text = "\n".join(f"• `{cmd}`" for cmd in allowed_commands)
            
            embed = discord.Embed(
                title="🎛️ Allowed Commands",
                description=f"Commands available in current state:\n\n{commands_text}",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ Failed to get state info", ephemeral=True)
    
    @discord.ui.button(label="State Diagram", style=discord.ButtonStyle.secondary, emoji="📊")
    async def show_state_diagram(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show state machine diagram"""
        result = await self.orchestrator.handle_command("/state", self.project_name)
        if result["success"]:
            diagram = result["mermaid_diagram"]
            
            embed = discord.Embed(
                title="🔄 State Machine Diagram",
                description=f"```mermaid\n{diagram}\n```",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ Failed to get diagram", ephemeral=True)
    
    @discord.ui.button(label="Project Status", style=discord.ButtonStyle.success, emoji="📈")
    async def show_project_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show detailed project status"""
        result = await self.orchestrator.handle_command("/sprint status", self.project_name)
        if result["success"]:
            embed = discord.Embed(
                title=f"📊 Project Status: {self.project_name}",
                color=discord.Color.green()
            )
            embed.add_field(name="Total Tasks", value=result.get("total_tasks", 0), inline=True)
            embed.add_field(name="Completed", value=result.get("completed_tasks", 0), inline=True)
            embed.add_field(name="Failed", value=result.get("failed_tasks", 0), inline=True)
            embed.add_field(name="Current State", value=result.get("current_state", "Unknown"), inline=False)
            embed.add_field(name="Pending Approvals", value=result.get("pending_approvals", 0), inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ Failed to get project status", ephemeral=True)


class WorkflowBot(commands.Bot):
    """
    Discord bot for AI Agent TDD-Scrum Workflow management.
    
    Provides slash commands for workflow control, state visualization,
    and Human-In-The-Loop approval processes.
    """
    
    def __init__(self, orchestrator: Orchestrator):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            description="AI Agent TDD-Scrum Workflow Bot"
        )
        
        self.orchestrator = orchestrator
        self.project_channels: Dict[str, int] = {}  # project_name -> channel_id
        
    async def setup_hook(self):
        """Setup hook called when bot is ready"""
        logger.info("Setting up Discord bot commands...")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        
        # Create project channels if they don't exist
        await self._ensure_project_channels()
    
    async def _ensure_project_channels(self):
        """Ensure project-specific channels exist"""
        for guild in self.guilds:
            hostname = os.getenv("HOSTNAME", "localhost")
            
            for project_name in self.orchestrator.projects.keys():
                channel_name = f"{hostname}-{project_name}"
                
                # Check if channel exists
                existing_channel = discord.utils.get(guild.channels, name=channel_name)
                if not existing_channel:
                    try:
                        channel = await guild.create_text_channel(
                            name=channel_name,
                            topic=f"AI Agent workflow for project: {project_name}"
                        )
                        self.project_channels[project_name] = channel.id
                        logger.info(f"Created channel: {channel_name}")
                    except Exception as e:
                        logger.error(f"Failed to create channel {channel_name}: {e}")
                else:
                    self.project_channels[project_name] = existing_channel.id
                    logger.info(f"Found existing channel: {channel_name}")
    
    async def _get_project_from_channel(self, channel_id: int) -> Optional[str]:
        """Get project name from channel ID"""
        for project_name, proj_channel_id in self.project_channels.items():
            if proj_channel_id == channel_id:
                return project_name
        return "default"
    
    async def _send_notification(self, project_name: str, message: str, embed: Optional[discord.Embed] = None):
        """Send notification to project channel"""
        channel_id = self.project_channels.get(project_name)
        if channel_id:
            channel = self.get_channel(channel_id)
            if channel:
                await channel.send(message, embed=embed)
    
    @app_commands.command(name="epic", description="Define a new high-level initiative")
    @app_commands.describe(description="Epic description")
    async def epic_command(self, interaction: discord.Interaction, description: str):
        """Handle /epic command"""
        await interaction.response.defer()
        
        project_name = await self._get_project_from_channel(interaction.channel_id)
        result = await self.orchestrator.handle_command(
            "/epic", project_name, description=description
        )
        
        if result["success"]:
            embed = discord.Embed(
                title="📝 Epic Created",
                description=description,
                color=discord.Color.green()
            )
            embed.add_field(
                name="Proposed Stories",
                value="\n".join(f"• {story}" for story in result.get("stories", [])),
                inline=False
            )
            embed.add_field(name="Next Step", value=result.get("next_step", ""), inline=False)
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ {result.get('error', 'Unknown error')}")
    
    @app_commands.command(name="approve", description="Approve proposed stories or tasks")
    @app_commands.describe(items="Comma-separated list of item IDs to approve")
    async def approve_command(self, interaction: discord.Interaction, items: str = ""):
        """Handle /approve command"""
        await interaction.response.defer()
        
        project_name = await self._get_project_from_channel(interaction.channel_id)
        item_ids = [item.strip() for item in items.split(",") if item.strip()] if items else []
        
        result = await self.orchestrator.handle_command(
            "/approve", project_name, item_ids=item_ids
        )
        
        if result["success"]:
            embed = discord.Embed(
                title="✅ Items Approved",
                description=f"Approved {len(result.get('approved_items', []))} items",
                color=discord.Color.green()
            )
            if result.get("approved_items"):
                embed.add_field(
                    name="Approved Items",
                    value="\n".join(f"• {item}" for item in result["approved_items"]),
                    inline=False
                )
            embed.add_field(name="Next Step", value=result.get("next_step", ""), inline=False)
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ {result.get('error', 'Unknown error')}")
    
    @app_commands.command(name="sprint", description="Sprint lifecycle management")
    @app_commands.describe(
        action="Sprint action to perform",
        items="Items for sprint planning (comma-separated)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="plan", value="plan"),
        app_commands.Choice(name="start", value="start"),
        app_commands.Choice(name="status", value="status"),
        app_commands.Choice(name="pause", value="pause"),
        app_commands.Choice(name="resume", value="resume"),
    ])
    async def sprint_command(self, interaction: discord.Interaction, action: str, items: str = ""):
        """Handle /sprint commands"""
        await interaction.response.defer()
        
        project_name = await self._get_project_from_channel(interaction.channel_id)
        command = f"/sprint {action}"
        
        kwargs = {}
        if items and action == "plan":
            kwargs["story_ids"] = [item.strip() for item in items.split(",") if item.strip()]
        
        result = await self.orchestrator.handle_command(command, project_name, **kwargs)
        
        if result["success"]:
            if action == "status":
                embed = discord.Embed(
                    title="📊 Sprint Status",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Total Tasks", value=result.get("total_tasks", 0), inline=True)
                embed.add_field(name="Completed", value=result.get("completed_tasks", 0), inline=True)
                embed.add_field(name="Failed", value=result.get("failed_tasks", 0), inline=True)
                embed.add_field(name="Current State", value=result.get("current_state", ""), inline=False)
                embed.add_field(name="Pending Approvals", value=result.get("pending_approvals", 0), inline=True)
            else:
                embed = discord.Embed(
                    title=f"🏃 Sprint {action.title()}",
                    description=result.get("message", ""),
                    color=discord.Color.green()
                )
                if result.get("next_step"):
                    embed.add_field(name="Next Step", value=result["next_step"], inline=False)
            
            await interaction.followup.send(embed=embed)
        else:
            error_message = result.get("error", "Unknown error")
            hint = result.get("hint", "")
            
            embed = discord.Embed(
                title="❌ Command Failed",
                description=error_message,
                color=discord.Color.red()
            )
            if hint:
                embed.add_field(name="Suggestion", value=hint, inline=False)
            if result.get("current_state"):
                embed.add_field(name="Current State", value=result["current_state"], inline=False)
            
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="backlog", description="Manage product and sprint backlog")
    @app_commands.describe(
        action="Backlog action to perform",
        description="Story description or item details",
        feature="Feature ID for new stories",
        priority="Priority level for stories"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="view", value="view"),
            app_commands.Choice(name="add_story", value="add_story"),
            app_commands.Choice(name="prioritize", value="prioritize"),
        ],
        priority=[
            app_commands.Choice(name="top", value="top"),
            app_commands.Choice(name="high", value="high"),
            app_commands.Choice(name="medium", value="medium"),
            app_commands.Choice(name="low", value="low"),
        ]
    )
    async def backlog_command(self, interaction: discord.Interaction, action: str, 
                            description: str = "", feature: str = "", priority: str = ""):
        """Handle /backlog commands"""
        await interaction.response.defer()
        
        project_name = await self._get_project_from_channel(interaction.channel_id)
        command = f"/backlog {action}"
        
        kwargs = {}
        if description:
            kwargs["description"] = description
        if feature:
            kwargs["feature"] = feature
        if priority:
            kwargs["priority"] = priority
        
        result = await self.orchestrator.handle_command(command, project_name, **kwargs)
        
        if result["success"]:
            if action == "view":
                embed = discord.Embed(
                    title=f"📋 {result.get('backlog_type', 'Product').title()} Backlog",
                    color=discord.Color.blue()
                )
                items = result.get("items", [])
                if items:
                    for item in items[:10]:  # Limit to 10 items
                        embed.add_field(
                            name=f"{item.get('id', 'N/A')} - {item.get('priority', 'N/A').upper()}",
                            value=item.get('title', 'No title'),
                            inline=False
                        )
                else:
                    embed.description = "No items in backlog"
            else:
                embed = discord.Embed(
                    title=f"📝 Backlog {action.replace('_', ' ').title()}",
                    description=result.get("message", ""),
                    color=discord.Color.green()
                )
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ {result.get('error', 'Unknown error')}")
    
    @app_commands.command(name="state", description="View current workflow state and available commands")
    async def state_command(self, interaction: discord.Interaction):
        """Handle /state command with interactive view"""
        await interaction.response.defer()
        
        project_name = await self._get_project_from_channel(interaction.channel_id)
        result = await self.orchestrator.handle_command("/state", project_name)
        
        if result["success"]:
            state_info = result["state_info"]
            project_status = result["project_status"]
            
            embed = discord.Embed(
                title="🎛️ Workflow State",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Current State",
                value=f"`{state_info['current_state']}`",
                inline=True
            )
            embed.add_field(
                name="Project Mode",
                value=project_status["orchestration_mode"],
                inline=True
            )
            embed.add_field(
                name="Active Tasks",
                value=project_status["active_tasks"],
                inline=True
            )
            embed.add_field(
                name="Pending Approvals",
                value=project_status["pending_approvals"],
                inline=True
            )
            
            # Create interactive view
            view = StateView(self.orchestrator, project_name)
            
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.followup.send(f"❌ {result.get('error', 'Unknown error')}")
    
    @app_commands.command(name="request_changes", description="Request changes during sprint review")
    @app_commands.describe(description="Description of requested changes")
    async def request_changes_command(self, interaction: discord.Interaction, description: str):
        """Handle /request_changes command"""
        await interaction.response.defer()
        
        project_name = await self._get_project_from_channel(interaction.channel_id)
        result = await self.orchestrator.handle_command(
            "/request_changes", project_name, description=description
        )
        
        if result["success"]:
            embed = discord.Embed(
                title="🔄 Changes Requested",
                description=description,
                color=discord.Color.orange()
            )
            embed.add_field(name="Next Step", value=result.get("next_step", ""), inline=False)
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ {result.get('error', 'Unknown error')}")
    
    @app_commands.command(name="suggest_fix", description="Suggest fix for blocked task")
    @app_commands.describe(description="Fix suggestion for blocked task")
    async def suggest_fix_command(self, interaction: discord.Interaction, description: str):
        """Handle /suggest_fix command"""
        await interaction.response.defer()
        
        project_name = await self._get_project_from_channel(interaction.channel_id)
        result = await self.orchestrator.handle_command(
            "/suggest_fix", project_name, description=description
        )
        
        if result["success"]:
            embed = discord.Embed(
                title="🔧 Fix Suggested",
                description=description,
                color=discord.Color.green()
            )
            embed.add_field(name="Next Step", value=result.get("next_step", ""), inline=False)
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ {result.get('error', 'Unknown error')}")
    
    @app_commands.command(name="skip_task", description="Skip currently blocked task")
    async def skip_task_command(self, interaction: discord.Interaction):
        """Handle /skip_task command"""
        await interaction.response.defer()
        
        project_name = await self._get_project_from_channel(interaction.channel_id)
        result = await self.orchestrator.handle_command("/skip_task", project_name)
        
        if result["success"]:
            embed = discord.Embed(
                title="⏭️ Task Skipped",
                description=result.get("message", ""),
                color=discord.Color.yellow()
            )
            embed.add_field(name="Next Step", value=result.get("next_step", ""), inline=False)
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ {result.get('error', 'Unknown error')}")
    
    @app_commands.command(name="feedback", description="Provide sprint feedback and complete retrospective")
    @app_commands.describe(description="Sprint feedback and retrospective notes")
    async def feedback_command(self, interaction: discord.Interaction, description: str):
        """Handle /feedback command"""
        await interaction.response.defer()
        
        project_name = await self._get_project_from_channel(interaction.channel_id)
        result = await self.orchestrator.handle_command(
            "/feedback", project_name, description=description
        )
        
        if result["success"]:
            embed = discord.Embed(
                title="📝 Sprint Feedback Recorded",
                description=description,
                color=discord.Color.green()
            )
            embed.add_field(name="Next Step", value=result.get("next_step", ""), inline=False)
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ {result.get('error', 'Unknown error')}")
    
    @app_commands.command(name="project", description="Project management commands")
    @app_commands.describe(
        action="Action to perform (register)",
        path="Path to the project repository",
        name="Optional project name (defaults to directory name)"
    )
    async def project_command(self, interaction: discord.Interaction, action: str, path: str, name: str = ""):
        """Handle /project command"""
        await interaction.response.defer()
        
        if action.lower() == "register":
            result = await self._handle_project_register(path, name, interaction.guild)
            
            if result["success"]:
                embed = discord.Embed(
                    title="📁 Project Registered",
                    description=f"Project registered successfully",
                    color=discord.Color.green()
                )
                embed.add_field(name="Project Name", value=result["project_name"], inline=True)
                embed.add_field(name="Path", value=result["path"], inline=True)
                embed.add_field(name="Channel", value=result["channel"], inline=True)
                embed.add_field(name="Next Step", value=result.get("next_step", ""), inline=False)
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ {result.get('error', 'Unknown error')}")
        else:
            await interaction.followup.send(f"❌ Unknown project action: {action}")
    
    async def _handle_project_register(self, path: str, name: str, guild: discord.Guild) -> Dict[str, Any]:
        """Handle project registration"""
        try:
            # Validate path exists and is a git repository
            from pathlib import Path
            project_path = Path(path).resolve()
            
            if not project_path.exists():
                return {
                    "success": False,
                    "error": f"Path does not exist: {path}"
                }
            
            if not (project_path / ".git").exists():
                return {
                    "success": False,
                    "error": f"Path is not a git repository: {path}"
                }
            
            # Determine project name
            project_name = name if name else project_path.name
            
            # Check for existing project
            if project_name in self.orchestrator.projects:
                return {
                    "success": False,
                    "error": f"Project already registered: {project_name}"
                }
            
            # Check for existing Discord channel
            hostname = os.getenv("HOSTNAME", "localhost")
            channel_name = f"{hostname}-{project_name}"
            existing_channel = discord.utils.get(guild.channels, name=channel_name)
            
            if existing_channel:
                return {
                    "success": False,
                    "error": f"Channel already exists: {channel_name}. This might indicate the project is already being worked on."
                }
            
            # Initialize project storage and structure
            from project_storage import ProjectStorage
            storage = ProjectStorage(str(project_path))
            
            if not storage.initialize_project():
                return {
                    "success": False,
                    "error": "Failed to initialize project structure"
                }
            
            # Create Discord channel
            try:
                channel = await guild.create_text_channel(
                    name=channel_name,
                    topic=f"AI Agent workflow for project: {project_name}"
                )
                self.project_channels[project_name] = channel.id
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to create Discord channel: {e}"
                }
            
            # Add project to orchestrator
            from orchestrator import Project, OrchestrationMode
            from state_machine import StateMachine
            
            new_project = Project(
                name=project_name,
                path=project_path,
                orchestration_mode=OrchestrationMode.BLOCKING,
                state_machine=StateMachine(),
                active_tasks=[],
                pending_approvals=[],
                storage=storage
            )
            
            self.orchestrator.projects[project_name] = new_project
            
            return {
                "success": True,
                "project_name": project_name,
                "path": str(project_path),
                "channel": f"#{channel_name}",
                "next_step": f"Project initialized! Use commands in #{channel_name} to manage this project."
            }
            
        except Exception as e:
            logger.error(f"Error registering project: {e}")
            return {
                "success": False,
                "error": f"Failed to register project: {e}"
            }


async def run_discord_bot():
    """Run the Discord bot"""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error("DISCORD_BOT_TOKEN environment variable not set")
        return
    
    # Initialize orchestrator
    orchestrator = Orchestrator()
    
    # Initialize bot
    bot = WorkflowBot(orchestrator)
    
    try:
        # Start orchestrator in background
        orchestrator_task = asyncio.create_task(orchestrator.run())
        
        # Start Discord bot
        await bot.start(token)
        
    except KeyboardInterrupt:
        logger.info("Shutting down Discord bot...")
    finally:
        # Cleanup
        orchestrator.stop()
        await bot.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(run_discord_bot())