# Command Reference Template

Use this template for documenting command-line interfaces and Discord commands.

## Page Structure

```markdown
# Command Group Name

Brief description of command group purpose and scope.

## Quick Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `/command1` | Brief description | `/command1 example` |
| `/command2` | Brief description | `/command2 example` |

## Detailed Commands

### 🎯 Command Category 1

**`/command syntax <required> [optional]`**
Clear description of what the command does and when to use it.

**Parameters:**
- `required`: Description, constraints, and valid values
- `optional`: Description and default value if any

**Example:**
```bash
/command example --flag value
```

**Expected Output:**
```
Sample output format
Status information
```

**Use Cases:**
- Scenario 1: When to use this command
- Scenario 2: Common workflow context
- Scenario 3: Advanced usage patterns

**Related Commands:**
- [`/related1`](#related1): Brief description of relationship
- [`/related2`](#related2): Brief description of relationship

---

### 🔧 Command Category 2

[Repeat structure for each command]

## Common Workflows

### Workflow 1: Getting Started
```bash
# Step 1: Initial setup
/setup command

# Step 2: Configuration
/configure --option value

# Step 3: Verification
/status
```

### Workflow 2: Advanced Usage
```bash
# Advanced workflow example
/advanced command --complex-flag
```

## Error Handling

### Common Errors

**Error: "Command not allowed in current state"**
```
Cause: Command called in wrong workflow state
Solution: Check current state with /status
```

**Error: "Invalid parameter value"**
```
Cause: Parameter outside valid range
Solution: Use /help command for valid values
```

## Tips and Best Practices

!!! tip "Pro Tip"
    Use `/status` frequently to understand current system state.

!!! warning "Important"
    Always verify destructive operations before proceeding.

## Related Documentation

- [**→ Getting Started Guide**](../getting-started/quick-start.md)
- [**→ Workflow Sequences**](../user-guide/workflow-sequences.md)
- [**→ Troubleshooting**](../user-guide/troubleshooting.md)
```

## Template Usage Notes

1. **Command Naming**: Use consistent format `/command <required> [optional]`
2. **Examples**: Always include practical, working examples
3. **Error Handling**: Document common errors and solutions
4. **Cross-References**: Link to related commands and workflows
5. **Visual Organization**: Use icons for categories and clear headings
6. **Accessibility**: Ensure screen reader friendly structure