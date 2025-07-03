"""
Unified Discord Bot for AI Agent TDD-Scrum Workflow

Comprehensive Discord interface combining single-project and multi-project 
management capabilities with Human-In-The-Loop (HITL) workflow coordination.
"""

import os
import logging
import asyncio
import json
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks
from discord import app_commands

# Import from agent_workflow package
from ...core.orchestrator import Orchestrator, OrchestrationMode, ProjectConfig
from ...core.models import ProjectData
from ...core.state_machine import StateMachine
from ...core.storage import ProjectStorage

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


class DiscordClient(commands.Bot):
    """
    Unified Discord client for AI Agent TDD-Scrum Workflow management.
    
    Supports both single-project and multi-project modes with comprehensive
    slash commands, project-specific channels, and Human-In-The-Loop workflows.
    """
    
    def __init__(
        self, 
        orchestrator: Orchestrator,
        multi_project_mode: bool = False,
        command_prefix: str = "!",
        **kwargs
    ):
        """
        Initialize Discord client.
        
        Args:
            orchestrator: Orchestrator instance for workflow management
            multi_project_mode: Enable multi-project features
            command_prefix: Command prefix for text commands
        """
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix=command_prefix,
            intents=intents,
            description="AI Agent TDD-Scrum Workflow Bot",
            **kwargs
        )
        
        self.orchestrator = orchestrator
        self.multi_project_mode = multi_project_mode
        
        # Channel management
        self.guild_id: Optional[int] = None
        self.project_channels: Dict[str, int] = {}  # project_name -> channel_id
        self.global_channel_id: Optional[int] = None
        self.admin_channel_id: Optional[int] = None
        
        # Multi-project features
        if multi_project_mode:
            self.active_project_contexts: Dict[int, str] = {}  # user_id -> project_name
            self.alert_subscribers: Dict[str, Set[int]] = {}  # project_name -> set of user_ids
            self.monitoring_enabled = True
        
        logger.info(f"Discord client initialized (multi_project_mode: {multi_project_mode})")
    
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
        
        # Initialize guild structure
        await self._initialize_guild_structure()
        
        # Start monitoring tasks for multi-project mode
        if self.multi_project_mode:
            if not self.status_monitor.is_running():
                self.status_monitor.start()
            if not self.alert_monitor.is_running():
                self.alert_monitor.start()
    
    async def on_guild_join(self, guild):
        """Handle bot joining a guild"""
        logger.info(f"Joined guild: {guild.name} ({guild.id})")
        await self._setup_guild_channels(guild)
    
    async def _initialize_guild_structure(self):
        """Initialize guild structure with channels"""
        if not self.guilds:
            logger.warning("Bot is not in any guilds")
            return
        
        guild = self.guilds[0]  # Use first guild
        self.guild_id = guild.id
        
        await self._setup_guild_channels(guild)
    
    async def _setup_guild_channels(self, guild):
        """Setup channels for project management"""
        # Create category for orchestration
        category_name = "🤖 AI Orchestration"
        category = discord.utils.get(guild.categories, name=category_name)
        
        if not category:
            category = await guild.create_category(category_name)
        
        if self.multi_project_mode:
            # Create global orchestration channel
            global_channel_name = "global-orchestration"
            global_channel = discord.utils.get(guild.channels, name=global_channel_name)
            
            if not global_channel:
                global_channel = await guild.create_text_channel(
                    global_channel_name,
                    category=category,
                    topic="Global multi-project orchestration and monitoring"
                )
            
            self.global_channel_id = global_channel.id
            
            # Create admin channel
            admin_channel_name = "orchestration-admin"
            admin_channel = discord.utils.get(guild.channels, name=admin_channel_name)
            
            if not admin_channel:
                admin_channel = await guild.create_text_channel(
                    admin_channel_name,
                    category=category,
                    topic="Administrative commands and system alerts"
                )
            
            self.admin_channel_id = admin_channel.id
        
        # Create project-specific channels
        await self._ensure_project_channels(guild, category)
    
    async def _ensure_project_channels(self, guild, category=None):
        """Ensure project-specific channels exist"""
        hostname = os.getenv("HOSTNAME", "localhost")
        
        for project_name in self.orchestrator.projects.keys():
            if self.multi_project_mode:
                channel_name = f"proj-{project_name.lower().replace('_', '-')}"
            else:
                channel_name = f"{hostname}-{project_name}"
            
            # Check if channel exists
            existing_channel = discord.utils.get(guild.channels, name=channel_name)
            if not existing_channel:
                try:
                    channel = await guild.create_text_channel(
                        name=channel_name,
                        category=category,
                        topic=f"AI Agent workflow for project: {project_name}"
                    )
                    self.project_channels[project_name] = channel.id
                    logger.info(f"Created channel: {channel_name}")
                    
                    # Send welcome message
                    if self.multi_project_mode:
                        embed = discord.Embed(
                            title=f"Project Channel: {project_name}",
                            description=f"Welcome to the dedicated channel for project **{project_name}**!\n\nUse project-specific commands here or set this as your active project context in other channels.",
                            color=discord.Color.blue()
                        )
                        await channel.send(embed=embed)
                        
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
    
    def _get_active_project(self, user_id: int) -> Optional[str]:
        """Get active project for a user (multi-project mode only)"""
        if not self.multi_project_mode:
            return None
        return self.active_project_contexts.get(user_id)
    
    async def _check_admin_permission(self, ctx) -> bool:
        """Check if user has admin permission"""
        if ctx.author.guild_permissions.administrator:
            return True
        
        embed = discord.Embed(
            title="Permission Denied",
            description="This command requires administrator permissions",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return False
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human readable string"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    # ===== SLASH COMMANDS =====
    
    # --- Epic Management ---
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
    
    # --- Approval Commands ---
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
    
    # --- Sprint Management ---
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
    
    # --- Backlog Management ---
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
    async def backlog_command(
        self, 
        interaction: discord.Interaction, 
        action: str, 
        description: str = "", 
        feature: str = "", 
        priority: str = ""
    ):
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
    
    # --- State Inspection ---
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
    
    # --- Change and Fix Management ---
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
    
    # --- Feedback and Retrospective ---
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
    
    # --- TDD Commands ---
    @app_commands.command(name="tdd", description="Test-Driven Development cycle management")
    @app_commands.describe(
        action="TDD action to perform",
        story_id="Story ID to start TDD cycle for (required for start)",
        task_description="Description for new TDD task"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="start", value="start"),
        app_commands.Choice(name="status", value="status"),
        app_commands.Choice(name="next", value="next"),
        app_commands.Choice(name="abort", value="abort"),
        app_commands.Choice(name="logs", value="logs"),
        app_commands.Choice(name="overview", value="overview"),
        app_commands.Choice(name="design", value="design"),
        app_commands.Choice(name="test", value="test"),
        app_commands.Choice(name="code", value="code"),
        app_commands.Choice(name="refactor", value="refactor"),
        app_commands.Choice(name="commit", value="commit"),
        app_commands.Choice(name="run_tests", value="run_tests"),
    ])
    async def tdd_command(
        self, 
        interaction: discord.Interaction, 
        action: str, 
        story_id: str = "", 
        task_description: str = ""
    ):
        """Handle /tdd commands"""
        await interaction.response.defer()
        
        project_name = await self._get_project_from_channel(interaction.channel_id)
        command = f"/tdd {action}"
        
        kwargs = {}
        if story_id:
            kwargs["story_id"] = story_id
        if task_description:
            kwargs["task_description"] = task_description
        
        result = await self.orchestrator.handle_command(command, project_name, **kwargs)
        
        if result["success"]:
            # Handle different TDD command responses
            if action == "status":
                embed = discord.Embed(title="🔬 TDD Status", color=discord.Color.blue())
                cycle_info = result.get("cycle_info", {})
                if cycle_info:
                    embed.add_field(name="Cycle ID", value=cycle_info.get("cycle_id", "None"), inline=True)
                    embed.add_field(name="Story ID", value=cycle_info.get("story_id", "None"), inline=True)
                    embed.add_field(name="Current State", value=cycle_info.get("current_state", "None"), inline=True)
                    embed.add_field(name="Progress", value=cycle_info.get("progress", "0/0"), inline=True)
                    embed.add_field(name="Test Runs", value=cycle_info.get("total_test_runs", 0), inline=True)
                    embed.add_field(name="Refactors", value=cycle_info.get("total_refactors", 0), inline=True)
                    
                    if cycle_info.get("current_task_id"):
                        embed.add_field(name="Current Task", value=cycle_info["current_task_id"], inline=False)
                else:
                    embed.add_field(name="Status", value="No active TDD cycle", inline=False)
                
                if result.get("allowed_commands"):
                    commands_text = ", ".join(f"`{cmd}`" for cmd in result["allowed_commands"])
                    embed.add_field(name="Available Commands", value=commands_text, inline=False)
                
                if result.get("next_suggested"):
                    embed.add_field(name="Suggested Next", value=f"`{result['next_suggested']}`", inline=False)
                    
            elif action == "overview":
                embed = discord.Embed(title="📈 TDD Overview Dashboard", color=discord.Color.purple())
                overview_info = result.get("overview_info", {})
                if overview_info:
                    embed.add_field(name="Active Cycles", value=overview_info.get("active_cycles", 0), inline=True)
                    embed.add_field(name="Completed Cycles", value=overview_info.get("completed_cycles", 0), inline=True)
                    embed.add_field(name="Total Test Runs", value=overview_info.get("total_test_runs", 0), inline=True)
                    embed.add_field(name="Average Coverage", value=f"{overview_info.get('average_coverage', 0):.1f}%", inline=True)
                    embed.add_field(name="Total Refactors", value=overview_info.get("total_refactors", 0), inline=True)
                    embed.add_field(name="Success Rate", value=f"{overview_info.get('success_rate', 0):.1f}%", inline=True)
                    
                    active_stories = overview_info.get("active_stories", [])
                    if active_stories:
                        stories_text = "\n".join(f"• {story}" for story in active_stories[:5])
                        embed.add_field(name="Active Stories", value=stories_text, inline=False)
                else:
                    embed.add_field(name="Status", value="No TDD activity found", inline=False)
                    
            else:
                embed = discord.Embed(
                    title=f"🔬 TDD {action.title()}",
                    description=result.get("message", ""),
                    color=discord.Color.green()
                )
                if result.get("current_state"):
                    embed.add_field(name="Current State", value=result["current_state"], inline=True)
                if result.get("next_suggested"):
                    embed.add_field(name="Suggested Next", value=f"`{result['next_suggested']}`", inline=True)
            
            if result.get("next_step"):
                embed.add_field(name="Next Step", value=result["next_step"], inline=False)
            
            await interaction.followup.send(embed=embed)
        else:
            error_message = result.get("error", "Unknown error")
            hint = result.get("hint", "")
            
            embed = discord.Embed(
                title="❌ TDD Command Failed",
                description=error_message,
                color=discord.Color.red()
            )
            if hint:
                embed.add_field(name="Suggestion", value=hint, inline=False)
            if result.get("current_state"):
                embed.add_field(name="Current TDD State", value=result["current_state"], inline=False)
            if result.get("allowed_commands"):
                commands_text = ", ".join(f"`{cmd}`" for cmd in result["allowed_commands"])
                embed.add_field(name="Available Commands", value=commands_text, inline=False)
            
            await interaction.followup.send(embed=embed)
    
    # --- Project Management ---
    @app_commands.command(name="project", description="Project management commands")
    @app_commands.describe(
        action="Action to perform (register, switch, status)",
        path="Path to the project repository",
        name="Optional project name (defaults to directory name)"
    )
    async def project_command(
        self, 
        interaction: discord.Interaction, 
        action: str, 
        path: str = "", 
        name: str = ""
    ):
        """Handle /project command"""
        await interaction.response.defer()
        
        if action.lower() == "register":
            if not path:
                await interaction.followup.send("❌ Path is required for registration")
                return
                
            result = await self._handle_project_register(path, name, interaction.guild)
            
            if result["success"]:
                embed = discord.Embed(
                    title="📁 Project Registered",
                    description="Project registered successfully",
                    color=discord.Color.green()
                )
                embed.add_field(name="Project Name", value=result["project_name"], inline=True)
                embed.add_field(name="Path", value=result["path"], inline=True)
                embed.add_field(name="Channel", value=result["channel"], inline=True)
                embed.add_field(name="Next Step", value=result.get("next_step", ""), inline=False)
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ {result.get('error', 'Unknown error')}")
                
        elif action.lower() == "switch" and self.multi_project_mode:
            if not name:
                await interaction.followup.send("❌ Project name is required for switching")
                return
                
            if name not in self.orchestrator.projects:
                embed = discord.Embed(
                    title="Project not found",
                    description=f"Project '{name}' is not registered",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
            
            self.active_project_contexts[interaction.user.id] = name
            
            embed = discord.Embed(
                title="Active Project Set",
                description=f"Active project context set to: **{name}**",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
            
        else:
            await interaction.followup.send(f"❌ Unknown project action: {action}")
    
    async def _handle_project_register(self, path: str, name: str, guild: discord.Guild) -> Dict[str, Any]:
        """Handle project registration"""
        try:
            # Validate path exists and is a git repository
            from pathlib import Path
            project_path = Path(path).resolve()
            
            if not project_path.exists():
                return {"success": False, "error": f"Path does not exist: {path}"}
            
            if not (project_path / ".git").exists():
                return {"success": False, "error": f"Path is not a git repository: {path}"}
            
            # Determine project name
            project_name = name if name else project_path.name
            
            # Check for existing project
            if project_name in self.orchestrator.projects:
                return {"success": False, "error": f"Project already registered: {project_name}"}
            
            # Initialize project storage and structure
            storage = ProjectStorage(str(project_path))
            
            if not storage.initialize_project():
                return {"success": False, "error": "Failed to initialize project structure"}
            
            # Create Discord channel
            hostname = os.getenv("HOSTNAME", "localhost")
            if self.multi_project_mode:
                channel_name = f"proj-{project_name.lower().replace('_', '-')}"
            else:
                channel_name = f"{hostname}-{project_name}"
                
            existing_channel = discord.utils.get(guild.channels, name=channel_name)
            
            if existing_channel:
                return {
                    "success": False,
                    "error": f"Channel already exists: {channel_name}. This might indicate the project is already being worked on."
                }
            
            try:
                channel = await guild.create_text_channel(
                    name=channel_name,
                    topic=f"AI Agent workflow for project: {project_name}"
                )
                self.project_channels[project_name] = channel.id
            except Exception as e:
                return {"success": False, "error": f"Failed to create Discord channel: {e}"}
            
            # Add project to orchestrator
            new_project = ProjectConfig(
                name=project_name,
                path=str(project_path),
                orchestration_mode=OrchestrationMode.BLOCKING
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
            return {"success": False, "error": f"Failed to register project: {e}"}
    
    # ===== MULTI-PROJECT MONITORING (only enabled in multi-project mode) =====
    
    @tasks.loop(minutes=5)
    async def status_monitor(self):
        """Monitor project status and send updates"""
        if not self.multi_project_mode:
            return
            
        try:
            if not self.monitoring_enabled:
                return
            
            # Get status from orchestrator (this would need to be implemented)
            # For now, this is a placeholder
            # status = await self.orchestrator.get_global_status()
            # await self._check_status_changes(status)
            
        except Exception as e:
            logger.error(f"Status monitor error: {str(e)}")
    
    @tasks.loop(minutes=1)
    async def alert_monitor(self):
        """Monitor for alerts and notifications"""
        if not self.multi_project_mode:
            return
            
        try:
            # Check for failed projects and send alerts
            # This would be implemented based on orchestrator capabilities
            pass
            
        except Exception as e:
            logger.error(f"Alert monitor error: {str(e)}")


# Factory functions for backward compatibility
async def run_discord_bot(orchestrator: Orchestrator = None, multi_project_mode: bool = False):
    """Run the Discord bot"""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error("DISCORD_BOT_TOKEN environment variable not set")
        return
    
    # Initialize orchestrator if not provided
    if not orchestrator:
        orchestrator = Orchestrator()
    
    # Initialize bot
    bot = DiscordClient(orchestrator, multi_project_mode=multi_project_mode)
    
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


# Backward compatibility classes
WorkflowBot = DiscordClient
MultiProjectDiscordBot = DiscordClient


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(run_discord_bot())