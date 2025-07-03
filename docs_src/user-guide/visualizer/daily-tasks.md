# Daily Tasks with the Visualizer

Common workflows and tasks you'll perform regularly with the AI Agent Workflow visualizer.

## Project Management

### Start Working on a Project
1. **Launch the system**: `aw start`
2. **Open visualizer**: `aw web`
3. **Select project**: Choose from dropdown
4. **Check status**: Use `/state` command to see current workflow

### Register a New Project
1. **Register project**: `aw register-project /path/to/project "ProjectName"`
2. **Switch to project**: Select in visualizer dropdown
3. **Initialize workflow**: `/epic "Initial setup"`

### Monitor Multiple Projects
1. **Start multi-project mode**: `aw multi-project-start`
2. **Open visualizer**: Navigate to web interface
3. **Switch between projects**: Use dropdown to monitor different projects
4. **Check overall status**: `aw multi-project-status`

## Development Workflow

### Create New Epic
1. **Define epic**: `/epic "Feature description"`
2. **Watch state change**: Monitor diagram for epic creation
3. **View epic details**: Click on epic node in diagram

### Add Stories to Backlog
1. **Add story**: `/backlog add_story "Story description"`
2. **Prioritize**: `/backlog prioritize`
3. **View backlog**: `/backlog view`

### Sprint Management
1. **Plan sprint**: `/sprint plan`
2. **Start sprint**: `/sprint start`
3. **Monitor progress**: Watch state diagram updates
4. **Check status**: `/sprint status`

### Request Changes
1. **Review code**: Check files in project
2. **Request changes**: `/request_changes "Specific feedback"`
3. **Monitor updates**: Watch for agent responses

## Monitoring and Debugging

### Check System Health
1. **System status**: `aw health`
2. **Web interface status**: `aw web-status`
3. **Project status**: `/state` in chat

### Debug Issues
1. **Check logs**: Look at browser console for errors
2. **Restart components**: 
   - Web interface: `aw web-stop && aw web`
   - Orchestrator: `aw restart`
3. **Clear cache**: Hard refresh browser (Ctrl+F5)

### Performance Monitoring
1. **Check metrics**: Monitor response times in chat
2. **Resource usage**: `aw info` for system information
3. **Project health**: Use state diagram to identify bottlenecks

## Multi-User Collaboration

### Join Existing Project
1. **Get project path**: From team member
2. **Register locally**: `aw register-project /path/to/project`
3. **Sync state**: Open visualizer and check current epic/sprint

### Coordinate Work
1. **Check current work**: `/state` to see what others are doing
2. **Update progress**: Use appropriate commands to update status
3. **Communicate**: Use chat interface for coordination

## Best Practices

### Regular Checks
- Check `/state` at the start of each work session
- Monitor state diagram during development
- Use `/backlog view` to stay focused on priorities

### Efficient Command Use
- Learn key slash commands: `/epic`, `/backlog`, `/sprint`, `/state`
- Use tab completion where available
- Keep commands concise but descriptive

### Troubleshooting Prevention
- Hard refresh browser when switching between projects
- Restart web interface if experiencing lag
- Keep orchestrator running during active development

## Quick Reference

| Task | Command | Visual Indicator |
|------|---------|------------------|
| Check status | `/state` | State diagram position |
| Create epic | `/epic "description"` | New epic node appears |
| Add story | `/backlog add_story "story"` | Backlog counter updates |
| Start sprint | `/sprint start` | State transitions to sprint |
| Request changes | `/request_changes "feedback"` | PR review indicators |
| Switch project | Use dropdown | Diagram and chat context change |