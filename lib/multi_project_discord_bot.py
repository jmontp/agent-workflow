"""
Multi-Project Discord Bot

Enhanced Discord interface for managing multiple AI-assisted development projects
with project-specific channels, unified commands, and cross-project insights.
"""

import asyncio
import logging
import discord
from discord.ext import commands, tasks
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import json
import re

from .multi_project_config import MultiProjectConfigManager, ProjectConfig, ProjectStatus, ProjectPriority
from .global_orchestrator import GlobalOrchestrator, OrchestratorStatus
from .resource_scheduler import ResourceScheduler

# Import existing Discord bot components
try:
    from .discord_bot import create_state_visualization_embed, create_status_embed
except ImportError:
    # Fallback implementations
    def create_state_visualization_embed(state_info):
        return discord.Embed(title="State Visualization", description="Visualization not available")
    
    def create_status_embed(status_info):
        return discord.Embed(title="Status", description="Status not available")

logger = logging.getLogger(__name__)


class MultiProjectDiscordBot(commands.Bot):
    """
    Enhanced Discord bot for multi-project orchestration.
    
    Provides project-specific channels, unified command interface,
    cross-project insights, and comprehensive monitoring capabilities.
    """
    
    def __init__(
        self,
        config_manager: MultiProjectConfigManager,
        global_orchestrator: GlobalOrchestrator,
        resource_scheduler: ResourceScheduler,
        command_prefix: str = "/",
        **kwargs
    ):
        """
        Initialize multi-project Discord bot.
        
        Args:
            config_manager: Multi-project configuration manager
            global_orchestrator: Global orchestrator instance
            resource_scheduler: Resource scheduler instance
            command_prefix: Command prefix for Discord commands
        """
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(command_prefix=command_prefix, intents=intents, **kwargs)
        
        self.config_manager = config_manager
        self.global_orchestrator = global_orchestrator
        self.resource_scheduler = resource_scheduler
        
        # Channel management
        self.guild_id: Optional[int] = None
        self.project_channels: Dict[str, int] = {}  # project_name -> channel_id
        self.global_channel_id: Optional[int] = None
        self.admin_channel_id: Optional[int] = None
        
        # Project context for commands
        self.active_project_contexts: Dict[int, str] = {}  # user_id -> project_name
        
        # Monitoring and alerts
        self.alert_subscribers: Dict[str, Set[int]] = {}  # project_name -> set of user_ids
        self.monitoring_enabled = True
        
        # Register event handlers and commands
        self._setup_event_handlers()
        self._setup_commands()
        
        logger.info("Multi-project Discord bot initialized")
    
    async def on_ready(self):
        """Bot ready event handler"""
        logger.info(f"Multi-project Discord bot logged in as {self.user}")
        
        # Initialize guild and channels
        await self._initialize_guild_structure()
        
        # Start monitoring tasks
        if not self.status_monitor.is_running():
            self.status_monitor.start()
        
        if not self.alert_monitor.is_running():
            self.alert_monitor.start()
    
    async def on_guild_join(self, guild):
        """Handle bot joining a guild"""
        logger.info(f"Joined guild: {guild.name} ({guild.id})")
        await self._setup_guild_channels(guild)
    
    def _setup_event_handlers(self):
        """Setup event handlers"""
        
        @self.event
        async def on_command_error(ctx, error):
            """Handle command errors"""
            if isinstance(error, commands.CommandNotFound):
                # Try to suggest similar commands
                similar_commands = self._find_similar_commands(ctx.message.content)
                if similar_commands:
                    embed = discord.Embed(
                        title="Command not found",
                        description=f"Did you mean one of these?\n" + "\n".join(f"• `{cmd}`" for cmd in similar_commands),
                        color=discord.Color.orange()
                    )
                    await ctx.send(embed=embed)
                return
            
            elif isinstance(error, commands.MissingRequiredArgument):
                embed = discord.Embed(
                    title="Missing argument",
                    description=f"Missing required argument: `{error.param.name}`",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Log unexpected errors
            logger.error(f"Command error in {ctx.command}: {str(error)}")
            
            embed = discord.Embed(
                title="Command Error",
                description=f"An error occurred: {str(error)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    def _setup_commands(self):
        """Setup Discord commands"""
        
        # Global commands
        @self.command(name="global_status", aliases=["gstatus"])
        async def global_status(ctx):
            """Show global orchestration status"""
            status = await self.global_orchestrator.get_global_status()
            embed = self._create_global_status_embed(status)
            await ctx.send(embed=embed)
        
        @self.command(name="projects", aliases=["list_projects"])
        async def list_projects(ctx):
            """List all registered projects"""
            projects = self.config_manager.list_projects()
            embed = self._create_projects_list_embed(projects)
            await ctx.send(embed=embed)
        
        @self.command(name="project")
        async def set_active_project(ctx, project_name: str):
            """Set active project context for subsequent commands"""
            if project_name not in self.config_manager.projects:
                embed = discord.Embed(
                    title="Project not found",
                    description=f"Project '{project_name}' is not registered",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            self.active_project_contexts[ctx.author.id] = project_name
            
            embed = discord.Embed(
                title="Active Project Set",
                description=f"Active project context set to: **{project_name}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        
        # Project management commands
        @self.command(name="start_project")
        async def start_project(ctx, project_name: str = None):
            """Start a project orchestrator"""
            project_name = project_name or self._get_active_project(ctx.author.id)
            if not project_name:
                await ctx.send("Please specify a project name or set an active project context")
                return
            
            embed = discord.Embed(
                title="Starting Project",
                description=f"Starting orchestrator for project: **{project_name}**",
                color=discord.Color.blue()
            )
            message = await ctx.send(embed=embed)
            
            success = await self.global_orchestrator.start_project(project_name)
            
            if success:
                embed.description = f"✅ Successfully started project: **{project_name}**"
                embed.color = discord.Color.green()
            else:
                embed.description = f"❌ Failed to start project: **{project_name}**"
                embed.color = discord.Color.red()
            
            await message.edit(embed=embed)
        
        @self.command(name="stop_project")
        async def stop_project(ctx, project_name: str = None):
            """Stop a project orchestrator"""
            project_name = project_name or self._get_active_project(ctx.author.id)
            if not project_name:
                await ctx.send("Please specify a project name or set an active project context")
                return
            
            embed = discord.Embed(
                title="Stopping Project",
                description=f"Stopping orchestrator for project: **{project_name}**",
                color=discord.Color.orange()
            )
            message = await ctx.send(embed=embed)
            
            success = await self.global_orchestrator.stop_project(project_name)
            
            if success:
                embed.description = f"✅ Successfully stopped project: **{project_name}**"
                embed.color = discord.Color.green()
            else:
                embed.description = f"❌ Failed to stop project: **{project_name}**"
                embed.color = discord.Color.red()
            
            await message.edit(embed=embed)
        
        @self.command(name="project_status")
        async def project_status(ctx, project_name: str = None):
            """Show status for a specific project"""
            project_name = project_name or self._get_active_project(ctx.author.id)
            if not project_name:
                await ctx.send("Please specify a project name or set an active project context")
                return
            
            status = await self.global_orchestrator.get_global_status()
            if project_name in status["projects"]:
                project_status = status["projects"][project_name]
                embed = self._create_project_status_embed(project_name, project_status)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Project Not Running",
                    description=f"Project '{project_name}' is not currently running",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
        
        # Resource management commands
        @self.command(name="resources")
        async def resource_status(ctx):
            """Show resource allocation and usage"""
            status = self.resource_scheduler.get_scheduling_status()
            embed = self._create_resource_status_embed(status)
            await ctx.send(embed=embed)
        
        @self.command(name="optimize_resources")
        async def optimize_resources(ctx):
            """Trigger resource optimization"""
            if not await self._check_admin_permission(ctx):
                return
            
            embed = discord.Embed(
                title="Optimizing Resources",
                description="Running resource optimization...",
                color=discord.Color.blue()
            )
            message = await ctx.send(embed=embed)
            
            result = await self.resource_scheduler.optimize_allocation()
            
            embed = self._create_optimization_result_embed(result)
            await message.edit(embed=embed)
        
        # Project registration commands
        @self.command(name="register_project")
        async def register_project(ctx, name: str, path: str):
            """Register a new project"""
            if not await self._check_admin_permission(ctx):
                return
            
            try:
                project_config = self.config_manager.register_project(name, path)
                
                # Create project channel
                await self._create_project_channel(name)
                
                embed = discord.Embed(
                    title="Project Registered",
                    description=f"Successfully registered project: **{name}**\nPath: `{path}`",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                
            except Exception as e:
                embed = discord.Embed(
                    title="Registration Failed",
                    description=f"Failed to register project: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        
        @self.command(name="discover_projects")
        async def discover_projects(ctx, *search_paths):
            """Discover projects in specified paths"""
            if not await self._check_admin_permission(ctx):
                return
            
            if not search_paths:
                search_paths = ["/workspace", "/projects", "."]
            
            discovered = self.config_manager.discover_projects(list(search_paths))
            embed = self._create_discovery_embed(discovered)
            await ctx.send(embed=embed)
        
        # Cross-project insights
        @self.command(name="insights")
        async def cross_project_insights(ctx):
            """Show cross-project insights and patterns"""
            status = await self.global_orchestrator.get_global_status()
            insights = status.get("cross_project_insights", [])
            embed = self._create_insights_embed(insights)
            await ctx.send(embed=embed)
        
        # Alert management
        @self.command(name="subscribe")
        async def subscribe_alerts(ctx, project_name: str = None):
            """Subscribe to alerts for a project"""
            project_name = project_name or self._get_active_project(ctx.author.id)
            if not project_name:
                await ctx.send("Please specify a project name")
                return
            
            if project_name not in self.alert_subscribers:
                self.alert_subscribers[project_name] = set()
            
            self.alert_subscribers[project_name].add(ctx.author.id)
            
            embed = discord.Embed(
                title="Alert Subscription",
                description=f"✅ Subscribed to alerts for project: **{project_name}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        
        @self.command(name="unsubscribe")
        async def unsubscribe_alerts(ctx, project_name: str = None):
            """Unsubscribe from alerts for a project"""
            project_name = project_name or self._get_active_project(ctx.author.id)
            if not project_name:
                await ctx.send("Please specify a project name")
                return
            
            if project_name in self.alert_subscribers:
                self.alert_subscribers[project_name].discard(ctx.author.id)
            
            embed = discord.Embed(
                title="Alert Unsubscription",
                description=f"❌ Unsubscribed from alerts for project: **{project_name}**",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        
        # Help and utility commands
        @self.command(name="help_multi", aliases=["multi_help"])
        async def multi_project_help(ctx):
            """Show help for multi-project commands"""
            embed = self._create_help_embed()
            await ctx.send(embed=embed)
    
    @tasks.loop(minutes=5)
    async def status_monitor(self):
        """Monitor project status and send updates"""
        try:
            if not self.monitoring_enabled:
                return
            
            status = await self.global_orchestrator.get_global_status()
            
            # Check for status changes and send alerts
            await self._check_status_changes(status)
            
        except Exception as e:
            logger.error(f"Status monitor error: {str(e)}")
    
    @tasks.loop(minutes=1)
    async def alert_monitor(self):
        """Monitor for alerts and notifications"""
        try:
            # Check for failed projects
            status = await self.global_orchestrator.get_global_status()
            
            for project_name, project_status in status["projects"].items():
                if project_status["status"] == "crashed":
                    await self._send_project_alert(
                        project_name,
                        "🚨 Project Crashed",
                        f"Project {project_name} has crashed and needs attention",
                        discord.Color.red()
                    )
                elif project_status["error_count"] > 5:
                    await self._send_project_alert(
                        project_name,
                        "⚠️ High Error Count",
                        f"Project {project_name} has {project_status['error_count']} errors",
                        discord.Color.orange()
                    )
            
        except Exception as e:
            logger.error(f"Alert monitor error: {str(e)}")
    
    # Private helper methods
    
    async def _initialize_guild_structure(self):
        """Initialize guild structure with channels"""
        if not self.guilds:
            logger.warning("Bot is not in any guilds")
            return
        
        guild = self.guilds[0]  # Use first guild
        self.guild_id = guild.id
        
        await self._setup_guild_channels(guild)
    
    async def _setup_guild_channels(self, guild):
        """Setup channels for multi-project management"""
        # Create category for orchestration
        category_name = "🤖 AI Orchestration"
        category = discord.utils.get(guild.categories, name=category_name)
        
        if not category:
            category = await guild.create_category(category_name)
        
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
        
        # Create channels for existing projects
        for project_name in self.config_manager.projects.keys():
            await self._create_project_channel(project_name, category)
    
    async def _create_project_channel(self, project_name: str, category=None):
        """Create a channel for a specific project"""
        if not self.guild_id:
            return
        
        guild = self.get_guild(self.guild_id)
        if not guild:
            return
        
        if not category:
            category = discord.utils.get(guild.categories, name="🤖 AI Orchestration")
        
        channel_name = f"proj-{project_name.lower().replace('_', '-')}"
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        
        if existing_channel:
            self.project_channels[project_name] = existing_channel.id
            return existing_channel
        
        channel = await guild.create_text_channel(
            channel_name,
            category=category,
            topic=f"Project-specific orchestration for {project_name}"
        )
        
        self.project_channels[project_name] = channel.id
        
        # Send welcome message
        embed = discord.Embed(
            title=f"Project Channel: {project_name}",
            description=f"Welcome to the dedicated channel for project **{project_name}**!\n\nUse project-specific commands here or set this as your active project context in other channels.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed)
        
        return channel
    
    def _get_active_project(self, user_id: int) -> Optional[str]:
        """Get active project for a user"""
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
    
    def _find_similar_commands(self, message_content: str) -> List[str]:
        """Find similar commands for typos"""
        import difflib
        
        if not message_content.startswith(self.command_prefix):
            return []
        
        command_part = message_content[len(self.command_prefix):].split()[0]
        command_names = [cmd.name for cmd in self.commands]
        
        similar = difflib.get_close_matches(command_part, command_names, n=3, cutoff=0.6)
        return [f"{self.command_prefix}{cmd}" for cmd in similar]
    
    def _create_global_status_embed(self, status: Dict[str, Any]) -> discord.Embed:
        """Create embed for global status"""
        global_status = status["global_orchestrator"]
        metrics = status["global_metrics"]
        
        embed = discord.Embed(
            title="🌐 Global Orchestration Status",
            color=discord.Color.blue()
        )
        
        # Global orchestrator info
        embed.add_field(
            name="Orchestrator",
            value=f"Status: **{global_status['status'].title()}**\nUptime: {self._format_duration(global_status['uptime_seconds'])}",
            inline=True
        )
        
        # Project summary
        embed.add_field(
            name="Projects",
            value=f"Total: **{metrics['total_projects']}**\nActive: **{metrics['active_projects']}**",
            inline=True
        )
        
        # Resource summary
        embed.add_field(
            name="Resources",
            value=f"Agents: **{metrics['total_agents']}**\nMemory: **{metrics['total_memory_usage_mb']:.0f} MB**",
            inline=True
        )
        
        # Performance metrics
        if metrics['total_stories_completed'] > 0:
            embed.add_field(
                name="Performance",
                value=f"Stories: **{metrics['total_stories_completed']}** completed\nAvg Cycle: **{metrics['average_cycle_time_hours']:.1f}h**",
                inline=True
            )
        
        # Cross-project insights
        if metrics['cross_project_insights'] > 0:
            embed.add_field(
                name="Insights",
                value=f"**{metrics['cross_project_insights']}** cross-project patterns identified",
                inline=True
            )
        
        embed.timestamp = datetime.utcnow()
        return embed
    
    def _create_projects_list_embed(self, projects: List[ProjectConfig]) -> discord.Embed:
        """Create embed for projects list"""
        embed = discord.Embed(
            title="📋 Registered Projects",
            color=discord.Color.blue()
        )
        
        if not projects:
            embed.description = "No projects registered yet"
            return embed
        
        # Group by status
        status_groups = {}
        for project in projects:
            status = project.status.value
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(project)
        
        # Add fields for each status
        status_emojis = {
            "active": "🟢",
            "paused": "🟡",
            "maintenance": "🔧",
            "archived": "📦",
            "initializing": "🔄"
        }
        
        for status, projects_in_status in status_groups.items():
            emoji = status_emojis.get(status, "⚪")
            project_list = "\n".join([
                f"• **{p.name}** ({p.priority.value})"
                for p in projects_in_status
            ])
            
            embed.add_field(
                name=f"{emoji} {status.title()} ({len(projects_in_status)})",
                value=project_list,
                inline=False
            )
        
        embed.set_footer(text=f"Total: {len(projects)} projects")
        return embed
    
    def _create_project_status_embed(self, project_name: str, status: Dict[str, Any]) -> discord.Embed:
        """Create embed for project status"""
        embed = discord.Embed(
            title=f"📊 Project Status: {project_name}",
            color=discord.Color.green() if status["status"] == "running" else discord.Color.orange()
        )
        
        # Basic status
        embed.add_field(
            name="Status",
            value=f"**{status['status'].title()}**\nPID: {status['pid']}\nUptime: {self._format_duration(status['uptime_seconds'])}",
            inline=True
        )
        
        # Resource usage
        embed.add_field(
            name="Resources",
            value=f"CPU: **{status['cpu_usage']:.1f}%**\nMemory: **{status['memory_usage']:.0f} MB**\nAgents: **{status['active_agents']}**",
            inline=True
        )
        
        # Sprint info
        if status.get('current_sprint'):
            embed.add_field(
                name="Current Sprint",
                value=f"**{status['current_sprint']}**\nBacklog: {status['backlog_size']} items",
                inline=True
            )
        
        # Error tracking
        if status['error_count'] > 0:
            embed.add_field(
                name="Errors",
                value=f"**{status['error_count']}** errors\nRestarts: **{status['restart_count']}**",
                inline=True
            )
        
        embed.timestamp = datetime.utcnow()
        return embed
    
    def _create_resource_status_embed(self, status: Dict[str, Any]) -> discord.Embed:
        """Create embed for resource status"""
        embed = discord.Embed(
            title="💾 Resource Allocation Status",
            color=discord.Color.purple()
        )
        
        # System utilization
        utilization = status["system_utilization"]
        embed.add_field(
            name="System Utilization",
            value=f"CPU: **{utilization['cpu']:.1%}**\nMemory: **{utilization['memory']:.1%}**\nAgents: **{utilization['agents']:.1%}**",
            inline=True
        )
        
        # Strategy and metrics
        embed.add_field(
            name="Allocation Strategy",
            value=f"**{status['strategy'].replace('_', ' ').title()}**\nActive Projects: **{status['active_projects']}**",
            inline=True
        )
        
        # Performance metrics
        if "performance_metrics" in status:
            metrics = status["performance_metrics"]
            embed.add_field(
                name="Performance",
                value=f"Efficiency: **{metrics.get('average_efficiency', 0):.1%}**\nFragmentation: **{metrics.get('resource_fragmentation', 0):.1%}**",
                inline=True
            )
        
        # Project allocations (top 5)
        projects = list(status["projects"].items())[:5]
        if projects:
            project_info = "\n".join([
                f"• **{name}**: {data['quota']['max_agents']} agents, {data['quota']['memory_mb']} MB"
                for name, data in projects
            ])
            embed.add_field(
                name="Project Allocations",
                value=project_info,
                inline=False
            )
        
        embed.timestamp = datetime.utcnow()
        return embed
    
    def _create_optimization_result_embed(self, result: Dict[str, Any]) -> discord.Embed:
        """Create embed for optimization results"""
        embed = discord.Embed(
            title="⚡ Resource Optimization Results",
            color=discord.Color.green()
        )
        
        # Basic metrics
        embed.add_field(
            name="Optimization",
            value=f"Time: **{result['optimization_time']:.2f}s**\nStrategy: **{result['strategy_used'].replace('_', ' ').title()}**",
            inline=True
        )
        
        # Changes made
        changes = result.get("changes_made", [])
        embed.add_field(
            name="Changes",
            value=f"**{len(changes)}** allocation changes made",
            inline=True
        )
        
        # Improvement metrics
        improvements = result.get("improvement_metrics", {})
        if improvements:
            embed.add_field(
                name="Improvements",
                value=f"Efficiency: **{improvements.get('efficiency_improvement', 0):+.1%}**\nSavings: **{improvements.get('resource_savings', 0):+.1%}**",
                inline=True
            )
        
        # List changes if any
        if changes:
            change_list = "\n".join(f"• {change}" for change in changes[:5])
            if len(changes) > 5:
                change_list += f"\n• ... and {len(changes) - 5} more"
            
            embed.add_field(
                name="Change Details",
                value=change_list,
                inline=False
            )
        
        embed.timestamp = datetime.utcnow()
        return embed
    
    def _create_discovery_embed(self, discovered: List[Dict[str, str]]) -> discord.Embed:
        """Create embed for project discovery results"""
        embed = discord.Embed(
            title="🔍 Project Discovery Results",
            color=discord.Color.blue()
        )
        
        if not discovered:
            embed.description = "No projects discovered in the specified paths"
            return embed
        
        # Group by type
        type_groups = {}
        for project in discovered:
            project_type = project.get("type", "unknown")
            if project_type not in type_groups:
                type_groups[project_type] = []
            type_groups[project_type].append(project)
        
        # Add fields for each type
        type_emojis = {
            "git": "📁",
            "orch_existing": "🤖",
            "unknown": "❓"
        }
        
        for project_type, projects in type_groups.items():
            emoji = type_emojis.get(project_type, "📁")
            project_list = "\n".join([
                f"• **{p['name']}** - `{p['path']}`"
                for p in projects[:5]  # Limit to 5 per type
            ])
            
            if len(projects) > 5:
                project_list += f"\n• ... and {len(projects) - 5} more"
            
            embed.add_field(
                name=f"{emoji} {project_type.replace('_', ' ').title()} ({len(projects)})",
                value=project_list,
                inline=False
            )
        
        embed.set_footer(text=f"Total: {len(discovered)} projects discovered")
        return embed
    
    def _create_insights_embed(self, insights: List[Dict[str, Any]]) -> discord.Embed:
        """Create embed for cross-project insights"""
        embed = discord.Embed(
            title="🧠 Cross-Project Insights",
            color=discord.Color.purple()
        )
        
        if not insights:
            embed.description = "No cross-project insights available yet"
            return embed
        
        # Show recent insights
        for i, insight in enumerate(insights[:5]):
            embed.add_field(
                name=f"Insight {i+1}",
                value=insight.get("description", "No description available"),
                inline=False
            )
        
        if len(insights) > 5:
            embed.set_footer(text=f"Showing 5 of {len(insights)} insights")
        
        return embed
    
    def _create_help_embed(self) -> discord.Embed:
        """Create help embed for multi-project commands"""
        embed = discord.Embed(
            title="🤖 Multi-Project Orchestration Commands",
            description="Commands for managing multiple AI-assisted development projects",
            color=discord.Color.blue()
        )
        
        # Global commands
        embed.add_field(
            name="🌐 Global Commands",
            value=(
                "`/global_status` - Show global orchestration status\n"
                "`/projects` - List all registered projects\n"
                "`/resources` - Show resource allocation and usage\n"
                "`/insights` - Show cross-project insights"
            ),
            inline=False
        )
        
        # Project management
        embed.add_field(
            name="📋 Project Management",
            value=(
                "`/project <name>` - Set active project context\n"
                "`/start_project [name]` - Start a project orchestrator\n"
                "`/stop_project [name]` - Stop a project orchestrator\n"
                "`/project_status [name]` - Show project status"
            ),
            inline=False
        )
        
        # Admin commands
        embed.add_field(
            name="⚙️ Admin Commands",
            value=(
                "`/register_project <name> <path>` - Register new project\n"
                "`/discover_projects [paths...]` - Discover projects\n"
                "`/optimize_resources` - Trigger resource optimization"
            ),
            inline=False
        )
        
        # Alert management
        embed.add_field(
            name="🔔 Alert Management",
            value=(
                "`/subscribe [project]` - Subscribe to project alerts\n"
                "`/unsubscribe [project]` - Unsubscribe from alerts"
            ),
            inline=False
        )
        
        embed.set_footer(text="Use [] for optional parameters, <> for required parameters")
        return embed
    
    async def _send_project_alert(self, project_name: str, title: str, description: str, color: discord.Color):
        """Send alert to subscribers of a project"""
        if project_name not in self.alert_subscribers:
            return
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Project: {project_name}")
        
        # Send to project channel
        if project_name in self.project_channels:
            channel = self.get_channel(self.project_channels[project_name])
            if channel:
                await channel.send(embed=embed)
        
        # Send DMs to subscribers
        for user_id in self.alert_subscribers[project_name]:
            try:
                user = self.get_user(user_id)
                if user:
                    await user.send(embed=embed)
            except discord.Forbidden:
                # User has DMs disabled
                pass
            except Exception as e:
                logger.error(f"Failed to send alert DM to user {user_id}: {str(e)}")
    
    async def _check_status_changes(self, status: Dict[str, Any]):
        """Check for status changes and send notifications"""
        # This would implement change detection and notifications
        # For now, this is a placeholder
        pass
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human readable string"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"