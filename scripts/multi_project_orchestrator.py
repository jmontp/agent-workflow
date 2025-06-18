#!/usr/bin/env python3
"""
Multi-Project Orchestrator

Unified entry point for multi-project AI-assisted development orchestration.
Manages multiple projects simultaneously with resource allocation, security,
monitoring, and cross-project intelligence.
"""

import asyncio
import argparse
import logging
import signal
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import json

# Add lib to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from lib.multi_project_config import (
    MultiProjectConfigManager, ProjectConfig, GlobalOrchestratorConfig,
    ProjectPriority, ProjectStatus, ResourceLimits
)
from lib.global_orchestrator import GlobalOrchestrator
from lib.resource_scheduler import ResourceScheduler, ResourceQuota, SchedulingStrategy
from lib.cross_project_intelligence import CrossProjectIntelligence
from lib.multi_project_security import MultiProjectSecurity, AccessLevel, IsolationMode
from lib.multi_project_monitoring import MultiProjectMonitoring, MonitoringTarget
from lib.multi_project_discord_bot import MultiProjectDiscordBot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiProjectOrchestrator:
    """
    Main orchestrator class that coordinates all multi-project systems.
    
    Integrates configuration management, resource scheduling, security,
    monitoring, intelligence, and Discord bot into a unified system.
    """
    
    def __init__(
        self,
        config_path: str = "orch-config.yaml",
        enable_security: bool = True,
        enable_monitoring: bool = True,
        enable_intelligence: bool = True,
        enable_discord: bool = False,
        debug: bool = False
    ):
        """
        Initialize multi-project orchestrator.
        
        Args:
            config_path: Path to configuration file
            enable_security: Whether to enable security features
            enable_monitoring: Whether to enable monitoring
            enable_intelligence: Whether to enable cross-project intelligence
            enable_discord: Whether to enable Discord bot
            debug: Enable debug logging
        """
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        self.config_path = Path(config_path)
        self.enable_security = enable_security
        self.enable_monitoring = enable_monitoring
        self.enable_intelligence = enable_intelligence
        self.enable_discord = enable_discord
        
        # Initialize components
        self.config_manager: Optional[MultiProjectConfigManager] = None
        self.global_orchestrator: Optional[GlobalOrchestrator] = None
        self.resource_scheduler: Optional[ResourceScheduler] = None
        self.security: Optional[MultiProjectSecurity] = None
        self.monitoring: Optional[MultiProjectMonitoring] = None
        self.intelligence: Optional[CrossProjectIntelligence] = None
        self.discord_bot: Optional[MultiProjectDiscordBot] = None
        
        # Runtime state
        self.running = False
        self.startup_complete = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Multi-project orchestrator initialized")
    
    async def start(self) -> None:
        """Start the multi-project orchestrator"""
        logger.info("Starting multi-project orchestrator...")
        
        try:
            # 1. Initialize configuration
            await self._initialize_configuration()
            
            # 2. Initialize resource scheduler
            await self._initialize_resource_scheduler()
            
            # 3. Initialize security (if enabled)
            if self.enable_security:
                await self._initialize_security()
            
            # 4. Initialize monitoring (if enabled)
            if self.enable_monitoring:
                await self._initialize_monitoring()
            
            # 5. Initialize intelligence (if enabled)
            if self.enable_intelligence:
                await self._initialize_intelligence()
            
            # 6. Initialize global orchestrator
            await self._initialize_global_orchestrator()
            
            # 7. Initialize Discord bot (if enabled)
            if self.enable_discord:
                await self._initialize_discord_bot()
            
            # 8. Start all systems
            await self._start_all_systems()
            
            # 9. Setup project integrations
            await self._setup_project_integrations()
            
            self.running = True
            self.startup_complete = True
            
            logger.info("✅ Multi-project orchestrator started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start multi-project orchestrator: {str(e)}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the multi-project orchestrator"""
        if not self.running:
            return
        
        logger.info("Stopping multi-project orchestrator...")
        self.running = False
        
        # Stop systems in reverse order
        systems = [
            ("Discord bot", self.discord_bot),
            ("Global orchestrator", self.global_orchestrator),
            ("Intelligence system", self.intelligence),
            ("Monitoring system", self.monitoring),
            ("Resource scheduler", self.resource_scheduler)
        ]
        
        for name, system in systems:
            if system:
                try:
                    logger.debug(f"Stopping {name}...")
                    await system.stop()
                    logger.debug(f"✅ {name} stopped")
                except Exception as e:
                    logger.error(f"❌ Error stopping {name}: {str(e)}")
        
        # Save configurations
        if self.config_manager:
            try:
                self.config_manager.save_configuration()
            except Exception as e:
                logger.error(f"Failed to save configuration: {str(e)}")
        
        logger.info("✅ Multi-project orchestrator stopped")
    
    async def register_project(
        self,
        name: str,
        path: str,
        priority: ProjectPriority = ProjectPriority.NORMAL,
        **kwargs
    ) -> bool:
        """
        Register a new project in the orchestration system.
        
        Args:
            name: Project name
            path: Project path
            priority: Project priority
            **kwargs: Additional project configuration
            
        Returns:
            True if registered successfully, False otherwise
        """
        if not self.config_manager:
            logger.error("Configuration manager not initialized")
            return False
        
        try:
            # Register with config manager
            project_config = self.config_manager.register_project(
                name=name,
                path=path,
                priority=priority,
                **kwargs
            )
            
            # Register with resource scheduler
            if self.resource_scheduler:
                self.resource_scheduler.register_project(project_config)
            
            # Setup monitoring
            if self.monitoring:
                target = MonitoringTarget(
                    target_id=name,
                    target_type="project",
                    name=name
                )
                self.monitoring.register_target(target)
            
            # Setup security isolation
            if self.security:
                self.security.setup_project_isolation(name)
            
            logger.info(f"✅ Registered project: {name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register project {name}: {str(e)}")
            return False
    
    async def discover_and_register_projects(self, search_paths: List[str]) -> int:
        """
        Discover and register projects in specified paths.
        
        Args:
            search_paths: Paths to search for projects
            
        Returns:
            Number of projects registered
        """
        if not self.config_manager:
            logger.error("Configuration manager not initialized")
            return 0
        
        discovered = self.config_manager.discover_projects(search_paths)
        registered_count = 0
        
        for project_info in discovered:
            name = project_info["name"]
            path = project_info["path"]
            
            # Skip if already registered
            if name in self.config_manager.projects:
                logger.debug(f"Project {name} already registered, skipping")
                continue
            
            # Determine priority based on project type
            priority = ProjectPriority.NORMAL
            if project_info.get("type") == "orch_existing":
                priority = ProjectPriority.HIGH  # Existing orchestrated projects get high priority
            
            success = await self.register_project(name, path, priority)
            if success:
                registered_count += 1
        
        logger.info(f"Discovered {len(discovered)} projects, registered {registered_count}")
        return registered_count
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "orchestrator": {
                "running": self.running,
                "startup_complete": self.startup_complete,
                "config_path": str(self.config_path),
                "enabled_features": {
                    "security": self.enable_security,
                    "monitoring": self.enable_monitoring,
                    "intelligence": self.enable_intelligence,
                    "discord": self.enable_discord
                }
            }
        }
        
        # Get status from each component
        if self.global_orchestrator:
            try:
                status["global_orchestrator"] = await self.global_orchestrator.get_global_status()
            except Exception as e:
                status["global_orchestrator"] = {"error": str(e)}
        
        if self.resource_scheduler:
            try:
                status["resource_scheduler"] = self.resource_scheduler.get_scheduling_status()
            except Exception as e:
                status["resource_scheduler"] = {"error": str(e)}
        
        if self.security:
            try:
                status["security"] = self.security.get_security_status()
            except Exception as e:
                status["security"] = {"error": str(e)}
        
        if self.monitoring:
            try:
                status["monitoring"] = self.monitoring.get_monitoring_status()
            except Exception as e:
                status["monitoring"] = {"error": str(e)}
        
        if self.intelligence:
            try:
                status["intelligence"] = {
                    "patterns": self.intelligence.get_pattern_summary(),
                    "insights": self.intelligence.get_insight_summary(),
                    "transfers": self.intelligence.get_knowledge_transfer_summary()
                }
            except Exception as e:
                status["intelligence"] = {"error": str(e)}
        
        return status
    
    async def run_interactive_shell(self) -> None:
        """Run interactive shell for system management"""
        logger.info("Starting interactive shell (type 'help' for commands)")
        
        while self.running:
            try:
                command = input("multi-orch> ").strip()
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                if cmd == "help":
                    await self._show_help()
                elif cmd == "status":
                    await self._cmd_status(args)
                elif cmd == "projects":
                    await self._cmd_projects(args)
                elif cmd == "register":
                    await self._cmd_register(args)
                elif cmd == "discover":
                    await self._cmd_discover(args)
                elif cmd == "start":
                    await self._cmd_start_project(args)
                elif cmd == "stop":
                    await self._cmd_stop_project(args)
                elif cmd == "optimize":
                    await self._cmd_optimize(args)
                elif cmd == "insights":
                    await self._cmd_insights(args)
                elif cmd == "exit" or cmd == "quit":
                    break
                else:
                    print(f"Unknown command: {cmd}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Command error: {str(e)}")
    
    # Private initialization methods
    
    async def _initialize_configuration(self) -> None:
        """Initialize configuration management"""
        logger.debug("Initializing configuration management...")
        
        self.config_manager = MultiProjectConfigManager(str(self.config_path))
        
        # Validate configuration
        issues = self.config_manager.validate_configuration()
        if issues:
            logger.warning(f"Configuration validation issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        
        logger.debug("✅ Configuration management initialized")
    
    async def _initialize_resource_scheduler(self) -> None:
        """Initialize resource scheduler"""
        logger.debug("Initializing resource scheduler...")
        
        global_config = self.config_manager.global_config
        
        # Setup total system resources
        total_resources = ResourceQuota(
            cpu_cores=float(global_config.global_cpu_cores),
            memory_mb=global_config.global_memory_limit_gb * 1024,
            max_agents=global_config.max_total_agents,
            disk_mb=global_config.global_disk_limit_gb * 1024,
            network_bandwidth_mbps=1000.0  # Default 1Gbps
        )
        
        # Determine strategy
        strategy_map = {
            "fair_share": SchedulingStrategy.FAIR_SHARE,
            "priority_based": SchedulingStrategy.PRIORITY_BASED,
            "dynamic": SchedulingStrategy.DYNAMIC
        }
        strategy = strategy_map.get(
            global_config.resource_allocation_strategy,
            SchedulingStrategy.DYNAMIC
        )
        
        self.resource_scheduler = ResourceScheduler(
            total_resources=total_resources,
            strategy=strategy,
            rebalance_interval=global_config.resource_rebalance_interval_seconds
        )
        
        logger.debug("✅ Resource scheduler initialized")
    
    async def _initialize_security(self) -> None:
        """Initialize security system"""
        logger.debug("Initializing security system...")
        
        self.security = MultiProjectSecurity(
            storage_path=str(Path(self.config_manager.global_config.global_state_path) / "security"),
            enable_audit_logging=self.config_manager.global_config.enable_audit_logging,
            default_isolation_mode=IsolationMode.PROCESS
        )
        
        # Create default admin user if no users exist
        if not self.security.users:
            logger.info("Creating default admin user...")
            self.security.create_user(
                username="admin",
                email="admin@localhost",
                password="changeme123",
                global_access_level=AccessLevel.OWNER
            )
            logger.warning("⚠️  Default admin user created with password 'changeme123' - please change this!")
        
        logger.debug("✅ Security system initialized")
    
    async def _initialize_monitoring(self) -> None:
        """Initialize monitoring system"""
        logger.debug("Initializing monitoring system...")
        
        self.monitoring = MultiProjectMonitoring(
            storage_path=str(Path(self.config_manager.global_config.global_state_path) / "monitoring"),
            enable_prometheus=True,
            enable_grafana=False,
            websocket_port=8765
        )
        
        logger.debug("✅ Monitoring system initialized")
    
    async def _initialize_intelligence(self) -> None:
        """Initialize cross-project intelligence"""
        logger.debug("Initializing cross-project intelligence...")
        
        self.intelligence = CrossProjectIntelligence(
            storage_path=str(Path(self.config_manager.global_config.global_state_path) / "intelligence")
        )
        
        logger.debug("✅ Cross-project intelligence initialized")
    
    async def _initialize_global_orchestrator(self) -> None:
        """Initialize global orchestrator"""
        logger.debug("Initializing global orchestrator...")
        
        self.global_orchestrator = GlobalOrchestrator(self.config_manager)
        
        # Integrate with other systems
        if self.resource_scheduler:
            self.global_orchestrator.resource_scheduler = self.resource_scheduler
        
        logger.debug("✅ Global orchestrator initialized")
    
    async def _initialize_discord_bot(self) -> None:
        """Initialize Discord bot"""
        logger.debug("Initializing Discord bot...")
        
        discord_token = os.getenv("DISCORD_BOT_TOKEN")
        if not discord_token:
            logger.warning("⚠️  DISCORD_BOT_TOKEN not set, Discord bot disabled")
            self.enable_discord = False
            return
        
        self.discord_bot = MultiProjectDiscordBot(
            config_manager=self.config_manager,
            global_orchestrator=self.global_orchestrator,
            resource_scheduler=self.resource_scheduler
        )
        
        logger.debug("✅ Discord bot initialized")
    
    async def _start_all_systems(self) -> None:
        """Start all initialized systems"""
        logger.debug("Starting all systems...")
        
        # Start systems in dependency order
        systems = [
            ("Resource scheduler", self.resource_scheduler),
            ("Security system", self.security),
            ("Monitoring system", self.monitoring),
            ("Intelligence system", self.intelligence),
            ("Global orchestrator", self.global_orchestrator),
            ("Discord bot", self.discord_bot)
        ]
        
        for name, system in systems:
            if system:
                try:
                    logger.debug(f"Starting {name}...")
                    await system.start()
                    logger.debug(f"✅ {name} started")
                except Exception as e:
                    logger.error(f"❌ Failed to start {name}: {str(e)}")
                    raise
        
        logger.debug("✅ All systems started")
    
    async def _setup_project_integrations(self) -> None:
        """Setup integrations for existing projects"""
        logger.debug("Setting up project integrations...")
        
        for project_name, project_config in self.config_manager.projects.items():
            try:
                # Register with resource scheduler
                if self.resource_scheduler:
                    self.resource_scheduler.register_project(project_config)
                
                # Setup monitoring
                if self.monitoring:
                    target = MonitoringTarget(
                        target_id=project_name,
                        target_type="project",
                        name=project_name
                    )
                    self.monitoring.register_target(target)
                
                # Setup security isolation
                if self.security:
                    self.security.setup_project_isolation(project_name)
                
                logger.debug(f"✅ Integrated project: {project_name}")
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to integrate project {project_name}: {str(e)}")
        
        logger.debug("✅ Project integrations complete")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False
        
        # Create task to stop the orchestrator
        asyncio.create_task(self.stop())
    
    # Interactive shell commands
    
    async def _show_help(self) -> None:
        """Show help for interactive commands"""
        help_text = """
Available commands:
  help                    - Show this help message
  status [component]      - Show system status
  projects                - List all projects
  register <name> <path>  - Register a new project
  discover <paths...>     - Discover and register projects
  start <project>         - Start a project orchestrator
  stop <project>          - Stop a project orchestrator
  optimize                - Run resource optimization
  insights                - Show cross-project insights
  exit/quit               - Exit the shell
        """
        print(help_text)
    
    async def _cmd_status(self, args: List[str]) -> None:
        """Handle status command"""
        component = args[0] if args else None
        
        try:
            status = await self.get_system_status()
            
            if component:
                if component in status:
                    print(json.dumps(status[component], indent=2))
                else:
                    print(f"Unknown component: {component}")
            else:
                # Show summary
                print("🎛️  Multi-Project Orchestrator Status")
                print(f"Running: {status['orchestrator']['running']}")
                print(f"Startup Complete: {status['orchestrator']['startup_complete']}")
                
                if "global_orchestrator" in status:
                    go_status = status["global_orchestrator"]
                    if "global_orchestrator" in go_status:
                        print(f"Projects: {go_status['global_metrics']['total_projects']}")
                        print(f"Active: {go_status['global_metrics']['active_projects']}")
                
        except Exception as e:
            print(f"Error getting status: {str(e)}")
    
    async def _cmd_projects(self, args: List[str]) -> None:
        """Handle projects command"""
        try:
            projects = self.config_manager.list_projects()
            
            if not projects:
                print("No projects registered")
                return
            
            print("📋 Registered Projects:")
            for project in projects:
                status_emoji = {
                    ProjectStatus.ACTIVE: "🟢",
                    ProjectStatus.PAUSED: "🟡",
                    ProjectStatus.MAINTENANCE: "🔧",
                    ProjectStatus.ARCHIVED: "📦",
                    ProjectStatus.INITIALIZING: "🔄"
                }.get(project.status, "⚪")
                
                priority_emoji = {
                    ProjectPriority.CRITICAL: "🔴",
                    ProjectPriority.HIGH: "🟠",
                    ProjectPriority.NORMAL: "🟡",
                    ProjectPriority.LOW: "🟢"
                }.get(project.priority, "⚪")
                
                print(f"  {status_emoji} {project.name} ({priority_emoji} {project.priority.value})")
                print(f"    Path: {project.path}")
                print(f"    Status: {project.status.value}")
                
        except Exception as e:
            print(f"Error listing projects: {str(e)}")
    
    async def _cmd_register(self, args: List[str]) -> None:
        """Handle register command"""
        if len(args) < 2:
            print("Usage: register <name> <path>")
            return
        
        name, path = args[0], args[1]
        
        try:
            success = await self.register_project(name, path)
            if success:
                print(f"✅ Registered project: {name}")
            else:
                print(f"❌ Failed to register project: {name}")
        except Exception as e:
            print(f"Error registering project: {str(e)}")
    
    async def _cmd_discover(self, args: List[str]) -> None:
        """Handle discover command"""
        search_paths = args if args else ["."]
        
        try:
            count = await self.discover_and_register_projects(search_paths)
            print(f"✅ Registered {count} projects from discovery")
        except Exception as e:
            print(f"Error discovering projects: {str(e)}")
    
    async def _cmd_start_project(self, args: List[str]) -> None:
        """Handle start project command"""
        if not args:
            print("Usage: start <project>")
            return
        
        project_name = args[0]
        
        try:
            if self.global_orchestrator:
                success = await self.global_orchestrator.start_project(project_name)
                if success:
                    print(f"✅ Started project: {project_name}")
                else:
                    print(f"❌ Failed to start project: {project_name}")
            else:
                print("Global orchestrator not available")
        except Exception as e:
            print(f"Error starting project: {str(e)}")
    
    async def _cmd_stop_project(self, args: List[str]) -> None:
        """Handle stop project command"""
        if not args:
            print("Usage: stop <project>")
            return
        
        project_name = args[0]
        
        try:
            if self.global_orchestrator:
                success = await self.global_orchestrator.stop_project(project_name)
                if success:
                    print(f"✅ Stopped project: {project_name}")
                else:
                    print(f"❌ Failed to stop project: {project_name}")
            else:
                print("Global orchestrator not available")
        except Exception as e:
            print(f"Error stopping project: {str(e)}")
    
    async def _cmd_optimize(self, args: List[str]) -> None:
        """Handle optimize command"""
        try:
            if self.resource_scheduler:
                result = await self.resource_scheduler.optimize_allocation()
                print("🔧 Resource Optimization Results:")
                print(f"  Time: {result['optimization_time']:.2f}s")
                print(f"  Changes: {len(result['changes_made'])}")
                print(f"  Strategy: {result['strategy_used']}")
                
                if result['changes_made']:
                    print("  Changes made:")
                    for change in result['changes_made'][:5]:  # Show first 5
                        print(f"    - {change}")
            else:
                print("Resource scheduler not available")
        except Exception as e:
            print(f"Error running optimization: {str(e)}")
    
    async def _cmd_insights(self, args: List[str]) -> None:
        """Handle insights command"""
        try:
            if self.intelligence:
                insights = await self.intelligence.generate_cross_project_insights()
                print(f"🧠 Cross-Project Insights ({len(insights)} found):")
                
                for insight in insights[:5]:  # Show first 5
                    print(f"  📊 {insight.title}")
                    print(f"     {insight.description}")
                    print(f"     Confidence: {insight.confidence:.1%}")
                    print()
            else:
                print("Intelligence system not available")
        except Exception as e:
            print(f"Error getting insights: {str(e)}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Project AI Orchestration System"
    )
    
    # Configuration options
    parser.add_argument(
        "--config", "-c",
        default="orch-config.yaml",
        help="Configuration file path"
    )
    
    # Feature toggles
    parser.add_argument(
        "--no-security",
        action="store_true",
        help="Disable security features"
    )
    parser.add_argument(
        "--no-monitoring",
        action="store_true",
        help="Disable monitoring"
    )
    parser.add_argument(
        "--no-intelligence",
        action="store_true",
        help="Disable cross-project intelligence"
    )
    parser.add_argument(
        "--enable-discord",
        action="store_true",
        help="Enable Discord bot"
    )
    
    # Operation modes
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive shell mode"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon (no interactive shell)"
    )
    
    # Project management
    parser.add_argument(
        "--discover",
        nargs="+",
        metavar="PATH",
        help="Discover and register projects in specified paths"
    )
    parser.add_argument(
        "--register",
        nargs=2,
        metavar=("NAME", "PATH"),
        help="Register a specific project"
    )
    
    # Debug options
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status and exit"
    )
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = MultiProjectOrchestrator(
        config_path=args.config,
        enable_security=not args.no_security,
        enable_monitoring=not args.no_monitoring,
        enable_intelligence=not args.no_intelligence,
        enable_discord=args.enable_discord,
        debug=args.debug
    )
    
    try:
        # Start the orchestrator
        await orchestrator.start()
        
        # Handle project registration
        if args.register:
            name, path = args.register
            await orchestrator.register_project(name, path)
        
        # Handle project discovery
        if args.discover:
            await orchestrator.discover_and_register_projects(args.discover)
        
        # Handle status query
        if args.status:
            status = await orchestrator.get_system_status()
            print(json.dumps(status, indent=2, default=str))
            return
        
        # Run in appropriate mode
        if args.daemon:
            logger.info("Running in daemon mode (Ctrl+C to stop)")
            try:
                while orchestrator.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutdown signal received")
        elif args.interactive or not any([args.register, args.discover, args.status]):
            # Default to interactive mode
            await orchestrator.run_interactive_shell()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Orchestrator error: {str(e)}")
        sys.exit(1)
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())