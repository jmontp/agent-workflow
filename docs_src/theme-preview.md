# Color Scheme Preview

This page demonstrates how all 10 color schemes look with various documentation elements. Use the theme selector in the top-right corner to switch between themes and see how they affect the appearance of different components.

## Theme Overview

The following 10 professional color schemes are available:

!!! info "Theme Selector"
    Look for the **Themes** button in the top-right corner of this page. Click it to browse and select from 10 carefully designed color schemes.

### Available Themes

1. **GitHub Professional** - Clean, professional, developer-focused
2. **GitLab Orange** - Warm, energetic, collaboration-focused  
3. **Vercel Minimalist** - Ultra-clean, modern, high-contrast
4. **Linear Purple** - Modern, sophisticated, productivity-focused
5. **Stripe Blue** - Professional, trustworthy, financial-grade
6. **Nord Arctic** - Cool, calm, developer-friendly
7. **Dracula Dark** - Vibrant, dark, code-focused
8. **Solarized Light** - Balanced, easy on eyes, academic
9. **Material Design Classic** - Google's Material Design, consistent, familiar
10. **Sunset Gradient** - Vibrant, modern, eye-catching gradient

## Documentation Elements Preview

### Typography Hierarchy

# Heading 1
## Heading 2  
### Heading 3
#### Heading 4

Regular paragraph text with **bold text**, *italic text*, and `inline code`. This demonstrates how the color scheme affects readability and hierarchy.

### Code Blocks

```python
def calculate_fibonacci(n):
    """Calculate fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    
    return sequence

# Example usage
result = calculate_fibonacci(10)
print(f"First 10 Fibonacci numbers: {result}")
```

```bash
# Installation commands
pip install agent-workflow
cd /path/to/project
python scripts/orchestrator.py --config config.yaml
```

```yaml
# Configuration example
site_name: AI Agent Workflow
theme:
  name: material
  palette:
    primary: indigo
    accent: indigo
```

### Admonitions

!!! note "Information Note"
    This is how informational admonitions appear in each theme. Notice how the colors adapt to maintain readability and visual hierarchy.

!!! tip "Pro Tip"
    Each theme has been carefully designed with accessibility in mind, ensuring proper contrast ratios and readability.

!!! warning "Important Warning"
    Theme changes are automatically saved to your browser's local storage and will persist across sessions.

!!! danger "Critical Alert"
    Some themes like Dracula are optimized for dark environments, while others like Solarized work well in bright conditions.

!!! success "Success Message"
    The theme selector includes full keyboard navigation and screen reader support for accessibility.

!!! question "FAQ"
    Can't find the theme selector? It should appear as a "Themes" button in the top-right corner of the page.

### Tables

| Theme Name | Primary Color | Background | Best For |
|------------|---------------|------------|----------|
| GitHub | Blue (#0969da) | White | Development docs |
| GitLab | Orange (#fc6d26) | White | Collaborative projects |
| Vercel | Black (#000000) | White | Modern minimalism |
| Linear | Purple (#5e6ad2) | White | Productivity tools |
| Stripe | Indigo (#635bff) | White | Professional services |
| Nord | Steel Blue (#5e81ac) | Light Gray | Developer tools |
| Dracula | Purple (#bd93f9) | Dark Gray | Code-focused content |
| Solarized | Blue (#268bd2) | Cream | Academic writing |
| Material | Indigo (#3f51b5) | White | Google ecosystem |
| Sunset | Coral (#ff6b6b) | White | Creative projects |

### Lists and Navigation

#### Ordered Lists
1. **Theme Selection** - Choose from 10 professional color schemes
2. **Instant Application** - Themes apply immediately without page reload
3. **Persistent Storage** - Your choice is saved across browser sessions
4. **Accessibility** - Full keyboard and screen reader support
5. **Mobile Optimized** - Responsive design for all screen sizes

#### Unordered Lists
- **GitHub Theme**: Perfect for documentation sites and developer tools
- **GitLab Theme**: Great for collaborative projects and team wikis  
- **Vercel Theme**: Ideal for modern, minimalist product documentation
- **Linear Theme**: Excellent for productivity and workflow tools
- **Stripe Theme**: Professional choice for business and financial content

#### Task Lists
- [x] Create 10 distinct color schemes
- [x] Implement interactive theme selector
- [x] Add keyboard navigation support
- [x] Ensure mobile responsiveness
- [x] Include accessibility features
- [ ] Gather user feedback on theme preferences
- [ ] Consider additional theme variations

### Interactive Elements

#### Buttons and Links

[Primary Button](#){ .md-button .md-button--primary }
[Secondary Button](#){ .md-button }

- [Internal Link](./index.md)
- [External Link](https://github.com/jmontp/agent-workflow)
- [Anchor Link](#theme-overview)

#### Blockquotes

> "The best color scheme is the one that enhances readability and doesn't distract from the content. Each of these 10 themes has been carefully designed with that principle in mind."
> 
> — AI Agent Workflow Design Team

### Tabs

=== "Light Themes"

    Most themes use light backgrounds for maximum readability:
    
    - GitHub Professional
    - GitLab Orange  
    - Vercel Minimalist
    - Linear Purple
    - Stripe Blue
    - Material Design
    - Sunset Gradient

=== "Balanced Themes"

    These themes offer unique background colors:
    
    - Nord Arctic (Light gray background)
    - Solarized Light (Cream background)

=== "Dark Themes"

    For low-light environments:
    
    - Dracula Dark (Full dark mode)

### Code with Syntax Highlighting

```javascript
// Theme selector implementation
class ThemeSelector {
  constructor() {
    this.themes = [
      { id: 'github', name: 'GitHub', colors: ['#0969da', '#f6f8fa'] },
      { id: 'gitlab', name: 'GitLab', colors: ['#fc6d26', '#fafafa'] },
      // ... more themes
    ];
    this.init();
  }
  
  applyTheme(themeId) {
    document.documentElement.setAttribute('data-theme', themeId);
    this.saveTheme(themeId);
  }
}
```

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open theme selector | Click "Themes" button |
| Navigate themes | ++arrow-up++ / ++arrow-down++ |
| Select theme | ++enter++ or ++space++ |
| Close selector | ++escape++ |

### Math and Formulas

When using MathJax, formulas adapt to the theme colors:

$$
\sum_{i=1}^{n} i = \frac{n(n+1)}{2}
$$

The color scheme affects the rendering of mathematical expressions to maintain readability.

## Technical Implementation

### CSS Custom Properties

Each theme uses CSS custom properties for instant switching:

```css
[data-theme="github"] {
  --md-primary-fg-color: #0969da;
  --md-default-bg-color: #ffffff;
  --md-default-fg-color: #1f2328;
  /* ... more properties */
}
```

### JavaScript API

The theme selector provides a simple API:

```javascript
// Get current theme
const theme = window.themeSelector.getCurrentTheme();

// Set specific theme
window.themeSelector.setTheme('dracula');

// Listen for changes
document.addEventListener('themeChanged', (event) => {
  console.log('New theme:', event.detail.themeId);
});
```

## Accessibility Features

- **Keyboard Navigation**: Full arrow key navigation in theme selector
- **Screen Reader Support**: Proper ARIA labels and announcements
- **High Contrast**: Support for users with visual impairments  
- **Reduced Motion**: Respects user's motion preferences
- **Focus Management**: Clear focus indicators and logical tab order

## Mobile Experience

The theme selector automatically adapts to mobile devices:

- Touch-optimized controls
- Responsive positioning
- Full-width dropdown on small screens
- Accessible touch targets

## Testing Recommendations

Try switching between themes while viewing:

1. **Text-heavy pages** - Check readability of body text
2. **Code-heavy pages** - Verify syntax highlighting works well
3. **Navigation menus** - Ensure interactive elements are clear
4. **Tables and lists** - Confirm proper contrast and spacing
5. **Dark/light environments** - Test themes in different lighting

---

*This preview page demonstrates all major documentation elements. Use the theme selector to see how each color scheme enhances the reading experience while maintaining professional appearance and accessibility standards.*