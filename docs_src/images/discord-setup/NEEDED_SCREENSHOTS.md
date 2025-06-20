# Discord Setup Screenshots Needed

This file tracks all screenshots that need to be created for the Discord setup documentation.

## Summary

**Total screenshots needed: 15**

## Required Screenshots List

### Initial Setup (4 screenshots)

1. **developer-mode.png**
   - Location: Discord Settings > Advanced tab
   - Content: Developer Mode toggle switch being enabled
   - Purpose: Shows users how to enable Developer Mode for copying IDs

2. **developer-portal.png**
   - Location: Discord Developer Portal homepage
   - Content: Main page with "New Application" button visible
   - Purpose: Entry point for bot creation process

3. **create-application.png**
   - Location: New Application creation dialog
   - Content: Name field with "AI Agent Workflow" entered, Create button
   - Purpose: Shows the application creation step

4. **application-settings.png**
   - Location: General Information page
   - Content: Description field filled, tags added, Save Changes button
   - Purpose: Demonstrates application configuration

### Bot Configuration (4 screenshots)

5. **add-bot.png**
   - Location: Bot section in Developer Portal
   - Content: "Add Bot" button and confirmation dialog
   - Purpose: Shows bot creation process

6. **bot-token.png**
   - Location: Bot configuration page, Token section
   - Content: Reset Token and Copy buttons (token partially obscured)
   - Security: MUST obscure/blur the actual token
   - Purpose: Shows where to get bot token

7. **bot-intents.png**
   - Location: Privileged Gateway Intents section
   - Content: All three intents enabled (Presence, Server Members, Message Content)
   - Purpose: Shows required intent configuration

8. **permissions.png**
   - Location: OAuth2 > URL Generator
   - Content: Bot permissions checkboxes for text, channel management, thread permissions
   - Purpose: Shows permission selection process

### Server Setup (1 screenshot)

9. **bot-authorization.png**
   - Location: Browser OAuth2 authorization page
   - Content: Server selection dropdown, permission summary, Authorize button
   - Purpose: Shows bot invitation process

### Command Examples (6 screenshots)

10. **state-command.png**
    - Location: Discord chat
    - Content: /state command execution with bot response showing workflow state
    - Purpose: Demonstrates basic command usage

11. **epic-command.png**
    - Location: Discord chat
    - Content: /epic command with example description and bot's proposed user stories
    - Purpose: Shows epic creation process

12. **project-register.png**
    - Location: Discord chat
    - Content: Successful /project register command with path and confirmation
    - Purpose: Shows project registration

13. **sprint-status.png**
    - Location: Discord chat
    - Content: Sprint status embed with progress bars, story list, metrics
    - Purpose: Demonstrates sprint monitoring

14. **tdd-status.png**
    - Location: Discord chat
    - Content: TDD cycle status embed with current phase, test results, next steps
    - Purpose: Shows TDD workflow visualization

15. **state-interactive.png**
    - Location: Discord chat
    - Content: /state response with interactive buttons (Allowed Commands, State Diagram, Project Status)
    - Purpose: Shows interactive UI elements

## Screenshot Guidelines

### Privacy & Security
- Blur/redact any real tokens, IDs, or sensitive data
- Use demo/test servers only
- Replace real project paths with generic examples

### Visual Quality
- Minimum resolution: 1920x1080
- Clear, readable text
- Consistent Discord theme (preferably dark mode)
- Add arrows/highlights for important elements

### File Requirements
- Format: PNG for clarity
- Max file size: 500KB per image
- Dimensions: Max 1200px wide for documentation

## Creation Priority

High Priority (Core setup flow):
1. developer-portal.png
2. bot-token.png
3. bot-intents.png
4. permissions.png
5. bot-authorization.png

Medium Priority (Usage examples):
6. state-command.png
7. epic-command.png
8. project-register.png

Low Priority (Additional features):
9. All remaining screenshots

## Alternative Options

Until screenshots are created, consider:
1. Creating simple wireframe mockups
2. Using annotated diagrams
3. Adding more detailed text descriptions
4. Creating a video walkthrough instead

## Notes

- The existing README.md in this directory contains additional guidelines
- Screenshots should match the visual style of the documentation
- Consider creating animated GIFs for multi-step processes
- All screenshots should be optimized before adding to documentation