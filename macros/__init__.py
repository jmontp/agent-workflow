"""
MkDocs macros for AI Agent TDD-Scrum Workflow documentation.
Provides dynamic content generation and template functions.
"""

def define_env(env):
    """
    This is the hook for defining variables, macros and filters
    for the mkdocs-macros plugin.
    """
    
    @env.macro
    def feature_badge(status):
        """Generate a feature status badge"""
        status_colors = {
            "stable": "green",
            "beta": "orange", 
            "alpha": "red",
            "planned": "blue",
            "deprecated": "gray"
        }
        color = status_colors.get(status.lower(), "gray")
        return f'<span class="badge badge-{color}">{status.title()}</span>'
    
    @env.macro
    def command_example(command, description=""):
        """Generate a formatted command example"""
        return f"""
```bash
{command}
```
{description}
"""
    
    @env.macro
    def api_endpoint(method, path, description=""):
        """Generate API endpoint documentation"""
        method_colors = {
            "GET": "blue",
            "POST": "green", 
            "PUT": "orange",
            "DELETE": "red",
            "PATCH": "purple"
        }
        color = method_colors.get(method.upper(), "gray")
        return f"""
<div class="api-endpoint">
    <span class="http-method method-{color.lower()}">{method.upper()}</span>
    <code class="api-path">{path}</code>
    {f'<p class="api-description">{description}</p>' if description else ''}
</div>
"""
    
    @env.macro
    def architecture_diagram(title, description=""):
        """Generate architecture diagram placeholder"""
        return f"""
!!! info "{title}"
    {description}
    
    ```mermaid
    graph TD
        A[Component A] --> B[Component B]
        B --> C[Component C]
        C --> A
    ```
"""
    
    @env.macro
    def workflow_sequence(title, steps):
        """Generate workflow sequence diagram"""
        sequence = f"""
!!! note "{title}"
    ```mermaid
    sequenceDiagram
        participant U as User
        participant D as Discord Bot
        participant O as Orchestrator
        participant A as Agent
"""
        for i, step in enumerate(steps, 1):
            sequence += f"        U->>D: {step}\n"
            if i < len(steps):
                sequence += f"        D->>O: Process Command\n"
                sequence += f"        O->>A: Execute Task\n"
                sequence += f"        A-->>O: Task Result\n"
                sequence += f"        O-->>D: Response\n"
                sequence += f"        D-->>U: Feedback\n"
        
        sequence += "    ```"
        return sequence
    
    @env.macro
    def state_machine_diagram():
        """Generate state machine diagram"""
        return """
```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> BACKLOG_READY: /epic or /backlog
    BACKLOG_READY --> SPRINT_PLANNED: /sprint plan
    SPRINT_PLANNED --> SPRINT_ACTIVE: /sprint start
    SPRINT_ACTIVE --> SPRINT_REVIEW: /sprint complete
    SPRINT_REVIEW --> IDLE: /sprint retrospective
    
    SPRINT_ACTIVE --> PAUSED: /sprint pause
    PAUSED --> SPRINT_ACTIVE: /sprint resume
    
    note right of IDLE
        Initial state - ready for configuration
    end note
    
    note right of BACKLOG_READY
        Epics defined, stories ready
    end note
    
    note right of SPRINT_PLANNED
        Sprint planned, ready to start
    end note
    
    note right of SPRINT_ACTIVE
        Active development in progress
    end note
```
"""
    
    @env.macro
    def tech_stack_badges():
        """Generate technology stack badges"""
        return """
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![Discord.py](https://img.shields.io/badge/Discord.py-2.3+-7289DA?style=flat-square&logo=discord)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react)
![Material-UI](https://img.shields.io/badge/Material--UI-5+-0081CB?style=flat-square&logo=material-ui)
![MkDocs](https://img.shields.io/badge/MkDocs-Material-526CFE?style=flat-square&logo=markdown)
"""
    
    @env.macro 
    def installation_tabs():
        """Generate installation instruction tabs"""
        return """
=== "pip install"
    ```bash
    pip install -r requirements.txt
    ```

=== "conda install"
    ```bash
    conda env create -f environment.yml
    conda activate agent-workflow
    ```

=== "Docker"
    ```bash
    docker build -t agent-workflow .
    docker run -p 8000:8000 agent-workflow
    ```
"""

    @env.macro
    def quick_start_checklist():
        """Generate quick start checklist"""
        return """
- [ ] Clone the repository
- [ ] Install dependencies  
- [ ] Configure environment variables
- [ ] Set up Discord bot token
- [ ] Run the orchestrator
- [ ] Test with `/project register`
- [ ] Create your first epic with `/epic`
- [ ] Plan your first sprint with `/sprint plan`
"""

    # Add project variables to the global environment
    env.variables['project_name'] = "AI Agent TDD-Scrum Workflow"
    env.variables['github_repo'] = "https://github.com/jmontp/agent-workflow"
    env.variables['docs_url'] = "https://jmontp.github.io/agent-workflow/"