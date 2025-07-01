# ♿ Accessibility Implementation Guide

## Overview

The TDD State Machine Visualizer has been enhanced with comprehensive accessibility features to ensure WCAG 2.1 AA compliance and provide an excellent experience for all users, including those using assistive technologies.

## 🎯 Accessibility Features Implemented

### 1. Keyboard Navigation & Shortcuts

#### Global Keyboard Shortcuts
- **Alt+K** - Focus project search/selector
- **Alt+C** - Toggle chat panel visibility
- **Alt+H** - Show keyboard shortcuts help
- **Alt+T** - Toggle high contrast mode
- **Alt+M** - Toggle reduced motion mode
- **Alt+S** - Focus search input
- **Alt+1** - Focus main content area
- **Alt+2** - Focus chat panel
- **Alt+3** - Focus status bar
- **F1** - Show comprehensive accessibility help
- **Escape** - Close dialogs, clear autocomplete, return focus

#### Navigation Controls
- **Tab** - Navigate forward through interactive elements
- **Shift+Tab** - Navigate backward through interactive elements
- **Arrow Keys** - Navigate within component groups (tabs, lists, grids)
- **Enter/Space** - Activate buttons and interactive elements
- **Home/End** - Jump to first/last item in groups

#### Project Tab Navigation
- **Arrow Left/Right** - Navigate between project tabs
- **Home** - Jump to first project tab
- **End** - Jump to last project tab
- **Enter/Space** - Switch to selected project

### 2. ARIA Labels & Semantic HTML

#### Landmark Roles
```html
<body role="application" aria-label="TDD State Machine Visualizer Application">
<header role="banner" aria-label="Application header">
<main role="main" aria-label="Visualization dashboard">
<nav role="navigation" aria-label="Project navigation">
<section role="region" aria-label="State machine visualizations">
<aside role="complementary" aria-label="Chat interface">
```

#### Interactive Elements
- All buttons have descriptive `aria-label` attributes
- Form controls are properly labeled with `aria-labelledby` and `aria-describedby`
- Status information uses `aria-live` regions for dynamic updates
- Project tabs implement full tablist/tab/tabpanel pattern

#### State Information
- Connection status: `aria-live="polite"` for non-urgent updates
- Error messages: `aria-live="assertive"` for immediate attention
- Workflow state changes: Announced via live regions
- TDD cycle updates: Automatically announced to screen readers

### 3. Screen Reader Support

#### Live Region Announcements
- Workflow state changes: "Workflow state changed to SPRINT_ACTIVE"
- Connection status: "Connected to server" / "Disconnected from server"
- New chat messages: "New message from [username]: [content]"
- Project switching: "Switched to [project name] project"
- TDD cycle updates: "TDD cycles updated: [count] active cycles"

#### Screen Reader Only Content
```css
.sr-only {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  white-space: nowrap !important;
  border: 0 !important;
}
```

#### Context Descriptions
- Detailed descriptions for state diagrams
- Help text for form inputs
- Status explanations for complex UI elements

### 4. Focus Management

#### Visual Focus Indicators
```css
button:focus,
input:focus,
[tabindex]:focus {
  outline: 3px solid #4CAF50 !important;
  outline-offset: 2px !important;
  box-shadow: 0 0 0 1px rgba(76, 175, 80, 0.3) !important;
}
```

#### Focus Trapping
- Modal dialogs trap focus within their boundaries
- Autocomplete menus maintain proper focus flow
- Chat panel focus management for mobile overlay mode

#### Focus History
- Tracks last 10 focused elements
- Escape key returns to previous focus
- Smart focus restoration after modal closure

### 5. User Preferences & Adaptation

#### High Contrast Mode
- **Toggle**: Alt+T or preference detection
- **Effect**: 150% contrast filter applied
- **Persistence**: Saved to localStorage
- **Auto-detection**: Respects `prefers-contrast: high`

#### Reduced Motion Mode
- **Toggle**: Alt+M or preference detection
- **Effect**: Disables animations and transitions
- **Persistence**: Saved to localStorage
- **Auto-detection**: Respects `prefers-reduced-motion: reduce`

#### System Preference Detection
```javascript
// Automatically detect and apply user preferences
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const highContrast = window.matchMedia('(prefers-contrast: high)').matches;
```

### 6. Mobile & Touch Accessibility

#### Touch Targets
- Minimum 44px x 44px touch targets on mobile
- Proper spacing between interactive elements
- Touch-friendly gesture support

#### Mobile Navigation
- Project dropdown for narrow screens
- Swipe-friendly chat panel
- Optimized keyboard for mobile devices

### 7. Chat Interface Accessibility

#### Command Autocomplete
- Full `listbox`/`option` ARIA pattern
- Keyboard navigation with Arrow Up/Down
- Active descendant management
- Screen reader announcements for suggestions

#### Message Navigation
- Each message is focusable with Tab
- Messages have descriptive aria-labels
- Timestamp and sender information included
- Reaction buttons are keyboard accessible

#### Input Enhancement
```html
<textarea aria-label="Type your message here" 
          aria-describedby="chat-input-help">
<div id="chat-input-help" class="sr-only">
  Type your message and press Enter to send
</div>
```

## 🛠️ Implementation Details

### JavaScript API

#### AccessibilityManager Class
```javascript
// Create accessibility manager
const accessibilityManager = AccessibilityManager.create();

// Announce to screen readers
accessibilityManager.announce('Status updated', 'polite');

// Integrate with existing components
accessibilityManager.integrateWithVisualizer(window.visualizer);
```

#### Public Methods
- `announce(message, priority)` - Announce text to screen readers
- `toggleHighContrast()` - Toggle high contrast mode
- `toggleReducedMotion()` - Toggle reduced motion mode
- `focusElement(selector)` - Focus specific element
- `showKeyboardHelp()` - Display keyboard shortcuts

### CSS Classes

#### Utility Classes
- `.sr-only` - Screen reader only content
- `.focus-visible` - Enhanced focus indicators
- `.keyboard-focused` - Keyboard navigation state
- `.high-contrast-mode` - High contrast styling
- `.reduced-motion-mode` - Reduced motion styling

#### Component Enhancement
- `.project-tab[aria-selected="true"]` - Active tab styling
- `.chat-message:focus` - Focused message highlighting
- `.status-indicator[data-status]` - Status-specific colors

## 🧪 Testing & Validation

### Accessibility Testing

#### Test File
Open `test_accessibility.html` to validate all accessibility features:
- Keyboard navigation patterns
- ARIA implementation
- Focus management
- User preference toggles
- Screen reader compatibility

#### Manual Testing Checklist
- [ ] All functionality available via keyboard
- [ ] Focus indicators clearly visible
- [ ] Screen reader announcements working
- [ ] High contrast mode functional
- [ ] Reduced motion preferences respected
- [ ] Skip links operational
- [ ] Form labels properly associated
- [ ] Error messages descriptive

#### Automated Testing
```bash
# Install accessibility testing tools
npm install -g axe-cli pa11y

# Run automated accessibility audits
axe-cli http://localhost:5000
pa11y http://localhost:5000
```

### Browser Testing

#### Screen Reader Testing
- **NVDA** (Windows) - Primary testing
- **JAWS** (Windows) - Secondary testing
- **VoiceOver** (macOS) - Safari testing
- **TalkBack** (Android) - Mobile testing

#### Keyboard Testing
- Tab navigation flow
- Arrow key navigation in components
- Keyboard shortcuts functionality
- Focus trap testing in modals

## 📋 WCAG 2.1 AA Compliance

### Principle 1: Perceivable

#### 1.1 Text Alternatives
- ✅ All images have alt text
- ✅ Decorative images marked appropriately
- ✅ Complex diagrams have detailed descriptions

#### 1.2 Time-based Media
- ✅ No auto-playing audio content
- ✅ Video content would include captions (if implemented)

#### 1.3 Adaptable
- ✅ Semantic HTML structure
- ✅ Proper heading hierarchy (h1 → h2 → h3)
- ✅ Information not conveyed by color alone
- ✅ Content reflows properly at 200% zoom

#### 1.4 Distinguishable
- ✅ Color contrast ratio ≥ 4.5:1 for normal text
- ✅ Color contrast ratio ≥ 3:1 for large text
- ✅ Text resizable up to 200% without loss of functionality
- ✅ No content flashes more than 3 times per second

### Principle 2: Operable

#### 2.1 Keyboard Accessible
- ✅ All functionality available via keyboard
- ✅ No keyboard traps (except intentional modal traps)
- ✅ Focus order is logical and intuitive

#### 2.2 Enough Time
- ✅ No time limits on content interaction
- ✅ Auto-updating content can be paused
- ✅ Session timeouts include warnings

#### 2.3 Seizures and Physical Reactions
- ✅ No content flashes more than 3 times per second
- ✅ Motion animations respect user preferences

#### 2.4 Navigable
- ✅ Skip links provided for main content areas
- ✅ Page titled appropriately
- ✅ Focus order follows logical sequence
- ✅ Link purposes clear from context
- ✅ Multiple navigation methods available

#### 2.5 Input Modalities
- ✅ Touch targets minimum 44x44 pixels
- ✅ Click/tap functionality available via keyboard
- ✅ Drag operations have keyboard alternatives

### Principle 3: Understandable

#### 3.1 Readable
- ✅ Page language specified (lang="en")
- ✅ Language changes marked when they occur
- ✅ Complex terminology explained

#### 3.2 Predictable
- ✅ Focus changes don't trigger context changes
- ✅ Navigation consistent across pages
- ✅ Interactive elements behave predictably

#### 3.3 Input Assistance
- ✅ Form errors identified and described
- ✅ Labels and instructions provided for inputs
- ✅ Error suggestions offered when possible

### Principle 4: Robust

#### 4.1 Compatible
- ✅ Valid HTML markup
- ✅ Proper ARIA implementation
- ✅ Compatible with assistive technologies

## 🚀 Quick Start Guide

### For Developers

1. **Include Accessibility Script**:
```html
<script src="js/accessibility-enhancements.js"></script>
```

2. **Initialize on Page Load**:
```javascript
document.addEventListener('DOMContentLoaded', () => {
  if (window.AccessibilityManager) {
    window.AccessibilityManager.announce('Application loaded and ready');
  }
});
```

3. **Add ARIA Labels**:
```html
<button aria-label="Close dialog" onclick="closeModal()">×</button>
<div role="status" aria-live="polite" id="status-region"></div>
```

### For Users

1. **Keyboard Navigation**:
   - Use Tab to navigate through interactive elements
   - Use arrow keys within component groups
   - Press Escape to close dialogs or return focus

2. **Screen Reader Users**:
   - All content is properly labeled and described
   - Status changes are announced automatically
   - Use skip links to jump to main content areas

3. **Customization**:
   - Press Alt+T for high contrast mode
   - Press Alt+M to reduce motion
   - Press Alt+H for keyboard shortcut help

## 🔧 Configuration Options

### Accessibility Settings
```javascript
// Configure announcement preferences
AccessibilityManager.setAnnouncementLevel('verbose'); // 'brief', 'normal', 'verbose'

// Configure keyboard shortcuts
AccessibilityManager.enableShortcuts(true);

// Set focus management style
AccessibilityManager.setFocusStyle('enhanced'); // 'standard', 'enhanced'
```

### Integration with Existing Code
```javascript
// Enhance existing visualizer with accessibility
if (window.visualizer && window.AccessibilityManager) {
  window.AccessibilityManager.integrateWithVisualizer(window.visualizer);
}
```

## 📞 Support & Resources

### Documentation
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Screen Reader Testing](https://webaim.org/articles/screenreader_testing/)

### Testing Tools
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [WAVE Browser Extension](https://wave.webaim.org/extension/)
- [Color Contrast Analyzer](https://www.tpgi.com/color-contrast-checker/)

### Feedback
If you encounter accessibility issues or have suggestions for improvement, please open an issue with:
- Browser and version
- Assistive technology used (if applicable)
- Description of the issue
- Steps to reproduce

---

This implementation ensures that the TDD State Machine Visualizer is accessible to all users, regardless of their abilities or the assistive technologies they use.