# MkDocs Color Scheme Integration Guide

## Overview

This guide explains how to integrate the 10 professional color schemes with interactive theme selector into your MkDocs Material documentation site.

## Files Created

1. **`stylesheets/color-schemes.css`** - Complete CSS with all 10 color schemes
2. **`js/theme-selector.js`** - Interactive theme selector JavaScript
3. **`theme-integration-guide.md`** - This integration guide

## Integration Steps

### Step 1: Update mkdocs.yml

Add the new CSS and JavaScript files to your `mkdocs.yml`:

```yaml
extra_css:
  - stylesheets/extra.css
  - stylesheets/color-schemes.css  # Add this line

extra_javascript:
  - https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js
  - https://polyfill.io/v3/polyfill.min.js?features=es6
  - https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js
  - js/mermaid-zoom.js
  - js/theme-selector.js  # Add this line
```

### Step 2: Optional Configuration

The theme selector works automatically, but you can customize it:

```javascript
// Disable auto-initialization (in your own JS file)
window.disableAutoThemeSelector = true;

// Manual initialization with custom options
document.addEventListener('DOMContentLoaded', () => {
  window.themeSelector = new ThemeSelector();
  
  // Set a specific default theme
  window.themeSelector.setTheme('github');
  
  // Listen for theme changes
  document.addEventListener('themeChanged', (event) => {
    console.log('Theme changed to:', event.detail.themeId);
  });
});
```

## Color Schemes

### 1. GitHub Professional (Default)
- **Primary**: #0969da (Blue)
- **Background**: #ffffff (White)  
- **Text**: #1f2328 (Dark Gray)
- **Accent**: #0969da (Blue)
- **Description**: Clean, professional, developer-focused

### 2. GitLab Orange
- **Primary**: #fc6d26 (Orange)
- **Background**: #ffffff (White)
- **Text**: #303030 (Dark Gray)
- **Accent**: #fca326 (Light Orange)
- **Description**: Warm, energetic, collaboration-focused

### 3. Vercel Minimalist
- **Primary**: #000000 (Black)
- **Background**: #ffffff (White)
- **Text**: #000000 (Black)
- **Accent**: #0070f3 (Blue)
- **Description**: Ultra-clean, modern, high-contrast

### 4. Linear Purple
- **Primary**: #5e6ad2 (Purple)
- **Background**: #ffffff (White)
- **Text**: #0f0f23 (Very Dark Blue)
- **Accent**: #a855f7 (Light Purple)
- **Description**: Modern, sophisticated, productivity-focused

### 5. Stripe Blue
- **Primary**: #635bff (Indigo)
- **Background**: #ffffff (White)
- **Text**: #0a2540 (Navy)
- **Accent**: #00d4aa (Teal)
- **Description**: Professional, trustworthy, financial-grade

### 6. Nord Arctic
- **Primary**: #5e81ac (Steel Blue)
- **Background**: #eceff4 (Light Gray)
- **Text**: #2e3440 (Dark Gray)
- **Accent**: #88c0d0 (Light Blue)
- **Description**: Cool, calm, developer-friendly

### 7. Dracula Dark
- **Primary**: #bd93f9 (Purple)
- **Background**: #282a36 (Dark Gray)
- **Text**: #f8f8f2 (Light Gray)
- **Accent**: #ff79c6 (Pink)
- **Description**: Vibrant, dark, code-focused

### 8. Solarized Light
- **Primary**: #268bd2 (Blue)
- **Background**: #fdf6e3 (Cream)
- **Text**: #657b83 (Gray)
- **Accent**: #859900 (Green)
- **Description**: Balanced, easy on eyes, academic

### 9. Material Design Classic
- **Primary**: #3f51b5 (Indigo)
- **Background**: #ffffff (White)
- **Text**: #212121 (Dark Gray)
- **Accent**: #ff4081 (Pink)
- **Description**: Google's Material Design, consistent, familiar

### 10. Sunset Gradient (Custom)
- **Primary**: #ff6b6b (Coral)
- **Background**: #ffffff (White)
- **Text**: #2c3e50 (Dark Blue)
- **Accent**: #4ecdc4 (Teal)
- **Description**: Vibrant, modern, eye-catching gradient
- **Special**: Features gradient backgrounds on header and navigation

## Features

### Accessibility
- Full keyboard navigation support
- Screen reader announcements
- High contrast mode support
- Focus management
- ARIA labels and roles

### Responsive Design
- Mobile-optimized interface
- Touch-friendly controls
- Adaptive positioning
- Reduced motion support

### Performance
- CSS custom properties for instant theme switching
- Smooth transitions with hardware acceleration
- Minimal JavaScript footprint
- Efficient DOM manipulation

### Persistence
- Automatic theme preference saving
- System theme detection
- Manual override capability
- Cross-session persistence

## Usage Examples

### Basic Usage
The theme selector appears automatically in the top-right corner of your documentation. Users can:
1. Click the "Themes" button
2. Browse the color preview
3. Select their preferred theme
4. Theme persists across page loads

### Programmatic Control
```javascript
// Get current theme
const currentTheme = window.themeSelector.getCurrentTheme();

// Set specific theme
window.themeSelector.setTheme('dracula');

// Get all available themes
const themes = window.themeSelector.getThemes();

// Listen for theme changes
document.addEventListener('themeChanged', (event) => {
  const { themeId, theme } = event.detail;
  console.log(`Theme changed to ${theme.name}: ${theme.description}`);
});
```

### Custom Theme Integration
To add your own theme, extend the CSS:

```css
[data-theme="custom"] {
  --md-primary-fg-color: #your-primary-color;
  --md-primary-fg-color--light: #your-primary-color-light;
  --md-primary-fg-color--dark: #your-primary-color-dark;
  --md-accent-fg-color: #your-accent-color;
  /* ... other custom properties */
}
```

Then update the JavaScript themes array in `theme-selector.js`.

## Troubleshooting

### Theme Not Applying
1. Ensure CSS file is loaded after MkDocs Material CSS
2. Check browser console for JavaScript errors
3. Verify `data-theme` attribute is set on `<html>` element

### Selector Not Appearing
1. Confirm JavaScript file is loaded
2. Check for conflicting CSS that might hide the selector
3. Verify no JavaScript errors preventing initialization

### Mobile Issues
1. The selector automatically adapts to mobile screens
2. On very small screens, it becomes full-width
3. Touch targets are optimized for mobile interaction

### Performance Issues
1. All transitions can be disabled with `prefers-reduced-motion`
2. Theme switching uses CSS custom properties for efficiency
3. JavaScript is optimized for minimal DOM manipulation

## Browser Support

- Modern browsers (Chrome 80+, Firefox 75+, Safari 13+, Edge 80+)
- CSS custom properties required
- localStorage for persistence (graceful fallback)
- matchMedia for system theme detection (optional)

## License

This theme system is part of the AI Agent TDD-Scram Workflow documentation and follows the same license as the main project.