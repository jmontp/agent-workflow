# 📖 User Guide - Complete Reference Documentation

> **Comprehensive user documentation for AI agent workflow system: commands, setup, troubleshooting, and daily usage patterns**

**Complete user documentation** covering daily workflows, Discord commands, CLI operations, troubleshooting, and advanced features for AI-assisted software development.

**Find what you need**: commands reference, setup guides, troubleshooting solutions, workflow examples, integration patterns, performance optimization

## Core Guides

<div class="grid cards" markdown>

-   :material-console:{ .lg .middle } **HITL Commands**

    ---
    
    Complete command reference with examples and usage patterns
    
    [:octicons-arrow-right-24: Commands](hitl-commands.md)

-   :material-state-machine:{ .lg .middle } **State Machine**

    ---
    
    Understanding workflow states and transitions
    
    [:octicons-arrow-right-24: States](state-machine.md)

-   :material-test-tube:{ .lg .middle } **TDD Workflow**

    ---
    
    Test-Driven Development cycle management
    
    [:octicons-arrow-right-24: TDD Guide](tdd-workflow.md)

-   :material-sitemap:{ .lg .middle } **Multi-Project**

    ---
    
    Managing multiple projects simultaneously
    
    [:octicons-arrow-right-24: Multi-Project](multi-project-orchestration.md)

</div>

## New Features

<div class="grid cards" markdown>

-   :material-robot:{ .lg .middle } **Agent Interface Management**

    ---
    
    Switch between Claude Code, Anthropic API, and Mock interfaces
    
    [:octicons-arrow-right-24: Interface Guide](agent-interface-management.md)

-   :material-brain:{ .lg .middle } **Context Management**

    ---
    
    Optimize context processing with FANCY, SIMPLE, and AUTO modes
    
    [:octicons-arrow-right-24: Context Guide](context-management.md)

-   :material-monitor:{ .lg .middle } **Web Portal**

    ---
    
    Enhanced web interface with real-time monitoring
    
    [:octicons-arrow-right-24: Portal Guide](ui-portal-guide.md)

-   :material-chart-line:{ .lg .middle } **Performance Monitoring**

    ---
    
    Monitor and optimize system performance
    
    [:octicons-arrow-right-24: Performance Guide](performance-monitoring.md)

</div>

## Reference Guides

<div class="grid cards" markdown>

-   :material-cog:{ .lg .middle } **Project Setup**

    ---
    
    Configure projects for AI agent orchestration
    
    [:octicons-arrow-right-24: Setup](project-setup.md)

-   :material-graph:{ .lg .middle } **Workflow Sequences**

    ---
    
    Common workflow patterns and sequences
    
    [:octicons-arrow-right-24: Sequences](workflow-sequences.md)

-   :material-terminal:{ .lg .middle } **CLI Reference**

    ---
    
    Command-line interface documentation
    
    [:octicons-arrow-right-24: CLI](cli-reference.md)

-   :material-account:{ .lg .middle } **User Profile**

    ---
    
    Customize your workflow preferences
    
    [:octicons-arrow-right-24: Profile](user-profile.md)

</div>

## Advanced Topics

- **[Testing](testing.md)** - Quality assurance and test strategies
- **[Performance Optimization](performance-optimization.md)** - System tuning and optimization
- **[Integration Examples](integration-examples.md)** - Real-world integration patterns
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[FAQ](faq.md)** - Frequently asked questions

## Daily Usage Patterns

### Starting a New Sprint

1. Define epic with `/epic "Epic description"`
2. Plan sprint with `/sprint plan`
3. Start execution with `/sprint start`
4. Monitor progress with `/state`

### Managing TDD Cycles

1. View all cycles with `/tdd overview`
2. Check specific story with `/tdd status STORY-ID`
3. Review cycle quality with `/tdd review_cycle STORY-ID`
4. Monitor metrics with `/tdd metrics`

### Human-In-The-Loop Control

- Use `/approve` to approve pending tasks
- Use `/request_changes` to provide feedback
- Use `/state` for interactive system inspection

## Getting Help

!!! tip "Quick Help"
    - Use `/state` in Discord to see available commands
    - Check command syntax with `/help <command>`
    - Review workflow examples in [Sequences](workflow-sequences.md)