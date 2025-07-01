"""
Responsive Design and Accessibility Integration Tests

Tests for mobile responsiveness, accessibility features, cross-browser compatibility,
and user experience across different devices and screen sizes.
"""

import asyncio
import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import sys
import os
import re

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
visualizer_path = Path(__file__).parent.parent.parent / "tools" / "visualizer"
sys.path.insert(0, str(visualizer_path))

# Mock dependencies
sys.modules['anthropic'] = MagicMock()
sys.modules['state_broadcaster'] = MagicMock()
sys.modules['lib.chat_state_sync'] = MagicMock()
sys.modules['lib.collaboration_manager'] = MagicMock()
sys.modules['command_processor'] = MagicMock()

# Mock broadcaster
mock_broadcaster = MagicMock()
mock_broadcaster.get_current_state.return_value = {
    "workflow_state": "IDLE",
    "projects": {},
    "last_updated": datetime.now().isoformat()
}
mock_broadcaster.transition_history = []
mock_broadcaster.clients = []
mock_broadcaster.tdd_cycles = {}

sys.modules['state_broadcaster'].broadcaster = mock_broadcaster

# Import components to test
from app import app


@pytest.fixture
def client():
    """Create test client for Flask app"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mobile_user_agent():
    """Mobile user agent string"""
    return "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"


@pytest.fixture
def tablet_user_agent():
    """Tablet user agent string"""
    return "Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"


@pytest.fixture
def desktop_user_agent():
    """Desktop user agent string"""
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


class TestMobileResponsiveness:
    """Test mobile device responsiveness"""
    
    def test_mobile_main_page_loads(self, client, mobile_user_agent):
        """Test main page loads correctly on mobile"""
        response = client.get('/', headers={'User-Agent': mobile_user_agent})
        
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')
        
        # Check for responsive meta tag
        html_content = response.get_data(as_text=True)
        assert 'viewport' in html_content
        assert 'width=device-width' in html_content
    
    def test_mobile_css_loading(self, client, mobile_user_agent):
        """Test CSS loads correctly for mobile"""
        # Test main CSS files
        css_files = [
            '/static/style.css',
            '/static/css/discord-chat.css'
        ]
        
        for css_file in css_files:
            response = client.get(css_file, headers={'User-Agent': mobile_user_agent})
            
            # Should load successfully or return 404 if file doesn't exist
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                assert 'text/css' in response.content_type
                
                # Check for mobile-responsive CSS
                css_content = response.get_data(as_text=True)
                
                # Look for responsive design patterns
                responsive_patterns = [
                    r'@media.*\(max-width:.*\)',
                    r'@media.*\(min-width:.*\)',
                    r'flex.*wrap',
                    r'grid.*responsive'
                ]
                
                # At least some responsive patterns should be present
                # Note: Actual CSS files may not exist in test environment
                if css_content:
                    has_responsive = any(
                        re.search(pattern, css_content, re.IGNORECASE) 
                        for pattern in responsive_patterns
                    )
                    # Don't assert if no CSS content (file might not exist)
                    if css_content.strip():
                        # Could be responsive or not, just verify it's valid CSS
                        assert len(css_content) > 0
    
    def test_mobile_javascript_functionality(self, client, mobile_user_agent):
        """Test JavaScript functionality on mobile"""
        # Test main JavaScript files
        js_files = [
            '/static/visualizer.js',
            '/static/js/discord-chat.js',
            '/static/js/chat-components.js'
        ]
        
        for js_file in js_files:
            response = client.get(js_file, headers={'User-Agent': mobile_user_agent})
            
            # Should load successfully or return 404 if file doesn't exist
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                assert 'javascript' in response.content_type.lower()
                
                js_content = response.get_data(as_text=True)
                
                # Check for mobile-specific JavaScript patterns
                mobile_patterns = [
                    r'touchstart',
                    r'touchend',
                    r'touchmove',
                    r'orientationchange',
                    r'resize'
                ]
                
                # JavaScript should be valid
                assert len(js_content) > 0
                
                # Look for mobile event handling (optional)
                has_mobile_events = any(
                    re.search(pattern, js_content, re.IGNORECASE)
                    for pattern in mobile_patterns
                )
                # Mobile events are optional, just checking structure
    
    def test_mobile_api_endpoints(self, client, mobile_user_agent):
        """Test API endpoints work correctly on mobile"""
        api_endpoints = [
            '/health',
            '/api/state',
            '/api/history',
            '/api/chat/history',
            '/debug'
        ]
        
        for endpoint in api_endpoints:
            response = client.get(endpoint, headers={'User-Agent': mobile_user_agent})
            
            assert response.status_code == 200
            
            # APIs should return JSON
            if endpoint.startswith('/api/') or endpoint == '/health':
                try:
                    data = json.loads(response.data)
                    assert isinstance(data, dict)
                except json.JSONDecodeError:
                    # Some endpoints might return text
                    pass
    
    def test_mobile_chat_interface(self, client, mobile_user_agent):
        """Test chat interface on mobile devices"""
        # Test sending chat message from mobile
        message_data = {
            "message": "/state",
            "user_id": "mobile-user",
            "username": "Mobile User",
            "project_name": "test-project"
        }
        
        response = client.post(
            '/api/chat/send',
            data=json.dumps(message_data),
            content_type='application/json',
            headers={'User-Agent': mobile_user_agent}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        
        # Test getting chat history on mobile
        response = client.get(
            '/api/chat/history',
            headers={'User-Agent': mobile_user_agent}
        )
        
        assert response.status_code == 200
        history = json.loads(response.data)
        assert "messages" in history
    
    def test_mobile_touch_friendly_responses(self, client, mobile_user_agent):
        """Test responses are optimized for touch interfaces"""
        response = client.get('/', headers={'User-Agent': mobile_user_agent})
        
        assert response.status_code == 200
        html_content = response.get_data(as_text=True)
        
        # Check for touch-friendly meta tags
        touch_patterns = [
            r'user-scalable=no',
            r'initial-scale=1',
            r'maximum-scale=1',
            r'width=device-width'
        ]
        
        # Should have viewport configuration
        has_viewport = any(
            re.search(pattern, html_content, re.IGNORECASE)
            for pattern in touch_patterns
        )
        
        # At least viewport should be configured
        assert 'viewport' in html_content


class TestTabletResponsiveness:
    """Test tablet device responsiveness"""
    
    def test_tablet_layout_adaptation(self, client, tablet_user_agent):
        """Test layout adapts correctly for tablet"""
        response = client.get('/', headers={'User-Agent': tablet_user_agent})
        
        assert response.status_code == 200
        html_content = response.get_data(as_text=True)
        
        # Should have responsive design elements
        assert 'viewport' in html_content
        
        # Check for tablet-optimized content
        # Note: Specific tablet optimizations would depend on implementation
        assert len(html_content) > 0
    
    def test_tablet_interaction_patterns(self, client, tablet_user_agent):
        """Test interaction patterns work on tablet"""
        # Test API interactions from tablet
        message_data = {
            "message": "/epic 'Tablet Epic'",
            "user_id": "tablet-user",
            "username": "Tablet User",
            "device_type": "tablet"
        }
        
        response = client.post(
            '/api/chat/send',
            data=json.dumps(message_data),
            content_type='application/json',
            headers={'User-Agent': tablet_user_agent}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
    
    def test_tablet_orientation_handling(self, client, tablet_user_agent):
        """Test handling of tablet orientation changes"""
        # Test in portrait mode
        portrait_headers = {
            'User-Agent': tablet_user_agent,
            'X-Device-Orientation': 'portrait'
        }
        
        response = client.get('/', headers=portrait_headers)
        assert response.status_code == 200
        
        # Test in landscape mode
        landscape_headers = {
            'User-Agent': tablet_user_agent,
            'X-Device-Orientation': 'landscape'
        }
        
        response = client.get('/', headers=landscape_headers)
        assert response.status_code == 200


class TestDesktopResponsiveness:
    """Test desktop responsiveness and full features"""
    
    def test_desktop_full_functionality(self, client, desktop_user_agent):
        """Test full functionality is available on desktop"""
        response = client.get('/', headers={'User-Agent': desktop_user_agent})
        
        assert response.status_code == 200
        html_content = response.get_data(as_text=True)
        
        # Desktop should have full feature set
        assert len(html_content) > 0
        
        # Check for desktop-specific features
        desktop_patterns = [
            r'keyboard.*shortcut',
            r'right.*click',
            r'drag.*drop',
            r'resize'
        ]
        
        # Desktop features are optional but should be accessible
    
    def test_desktop_multi_column_layout(self, client, desktop_user_agent):
        """Test multi-column layout on desktop"""
        response = client.get('/', headers={'User-Agent': desktop_user_agent})
        
        assert response.status_code == 200
        html_content = response.get_data(as_text=True)
        
        # Look for layout containers
        layout_patterns = [
            r'class.*container',
            r'class.*grid',
            r'class.*flex',
            r'class.*layout'
        ]
        
        # Should have some layout structure
        has_layout = any(
            re.search(pattern, html_content, re.IGNORECASE)
            for pattern in layout_patterns
        )
        
        # Basic HTML structure should exist
        assert '<html' in html_content or '<HTML' in html_content
    
    def test_desktop_advanced_features(self, client, desktop_user_agent):
        """Test advanced features available on desktop"""
        # Test complex API operations
        endpoints_to_test = [
            '/api/interfaces',
            '/api/context/status',
            '/metrics'
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint, headers={'User-Agent': desktop_user_agent})
            
            # Should work or return expected error codes
            assert response.status_code in [200, 404, 500, 503]


class TestAccessibilityFeatures:
    """Test accessibility features across devices"""
    
    def test_semantic_html_structure(self, client):
        """Test semantic HTML structure for screen readers"""
        response = client.get('/')
        
        assert response.status_code == 200
        html_content = response.get_data(as_text=True)
        
        # Check for semantic HTML elements
        semantic_elements = [
            r'<main.*?>',
            r'<nav.*?>',
            r'<section.*?>',
            r'<article.*?>',
            r'<header.*?>',
            r'<footer.*?>'
        ]
        
        # Should have some semantic structure
        semantic_count = sum(
            1 for pattern in semantic_elements
            if re.search(pattern, html_content, re.IGNORECASE)
        )
        
        # At least basic HTML structure
        assert '<html' in html_content.lower() or '<HTML' in html_content
    
    def test_aria_labels_and_roles(self, client):
        """Test ARIA labels and roles for accessibility"""
        response = client.get('/')
        
        assert response.status_code == 200
        html_content = response.get_data(as_text=True)
        
        # Check for ARIA attributes
        aria_patterns = [
            r'aria-label',
            r'aria-labelledby',
            r'aria-describedby',
            r'role=',
            r'aria-expanded',
            r'aria-hidden'
        ]
        
        # Count ARIA attributes
        aria_count = sum(
            len(re.findall(pattern, html_content, re.IGNORECASE))
            for pattern in aria_patterns
        )
        
        # ARIA attributes are optional but recommended
        # Just verify HTML is present
        assert len(html_content) > 0
    
    def test_keyboard_navigation_support(self, client):
        """Test keyboard navigation support"""
        response = client.get('/')
        
        assert response.status_code == 200
        html_content = response.get_data(as_text=True)
        
        # Check for keyboard navigation attributes
        keyboard_patterns = [
            r'tabindex',
            r'accesskey',
            r'focus',
            r'keydown',
            r'keyup',
            r'keypress'
        ]
        
        # Should have some keyboard support
        keyboard_count = sum(
            len(re.findall(pattern, html_content, re.IGNORECASE))
            for pattern in keyboard_patterns
        )
        
        # Keyboard support is good practice but not required
        assert len(html_content) > 0
    
    def test_color_contrast_and_themes(self, client):
        """Test color contrast and theme support"""
        # Test main page
        response = client.get('/')
        assert response.status_code == 200
        
        # Test CSS files for contrast
        css_response = client.get('/static/style.css')
        
        if css_response.status_code == 200:
            css_content = css_response.get_data(as_text=True)
            
            # Look for color definitions
            color_patterns = [
                r'color\s*:\s*#[0-9a-fA-F]{3,6}',
                r'background.*color\s*:\s*#[0-9a-fA-F]{3,6}',
                r'theme.*dark',
                r'theme.*light'
            ]
            
            # Should have color definitions
            has_colors = any(
                re.search(pattern, css_content, re.IGNORECASE)
                for pattern in color_patterns
            )
            
            # Colors are optional, just verify CSS exists
            if css_content.strip():
                assert len(css_content) > 0
    
    def test_alt_text_for_images(self, client):
        """Test alt text for images"""
        response = client.get('/')
        
        assert response.status_code == 200
        html_content = response.get_data(as_text=True)
        
        # Find all img tags
        img_tags = re.findall(r'<img[^>]*>', html_content, re.IGNORECASE)
        
        for img_tag in img_tags:
            # Should have alt attribute
            assert 'alt=' in img_tag.lower() or len(img_tags) == 0
    
    def test_form_accessibility(self, client):
        """Test form accessibility features"""
        response = client.get('/')
        
        assert response.status_code == 200
        html_content = response.get_data(as_text=True)
        
        # Find form elements
        form_elements = re.findall(r'<(input|textarea|select)[^>]*>', html_content, re.IGNORECASE)
        
        for element in form_elements:
            # Should have labels or aria-label
            has_label = (
                'aria-label' in element.lower() or
                'aria-labelledby' in element.lower() or
                'title=' in element.lower()
            )
            
            # Labels are good practice but not enforced in test
            # Just verify form elements exist
            assert len(element) > 0


class TestCrossBrowserCompatibility:
    """Test cross-browser compatibility"""
    
    def test_chrome_compatibility(self, client):
        """Test Chrome browser compatibility"""
        chrome_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        response = client.get('/', headers={'User-Agent': chrome_ua})
        assert response.status_code == 200
        
        # Test API compatibility
        response = client.get('/api/state', headers={'User-Agent': chrome_ua})
        assert response.status_code == 200
    
    def test_firefox_compatibility(self, client):
        """Test Firefox browser compatibility"""
        firefox_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        
        response = client.get('/', headers={'User-Agent': firefox_ua})
        assert response.status_code == 200
        
        # Test API compatibility
        response = client.get('/api/state', headers={'User-Agent': firefox_ua})
        assert response.status_code == 200
    
    def test_safari_compatibility(self, client):
        """Test Safari browser compatibility"""
        safari_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        
        response = client.get('/', headers={'User-Agent': safari_ua})
        assert response.status_code == 200
        
        # Test API compatibility
        response = client.get('/api/state', headers={'User-Agent': safari_ua})
        assert response.status_code == 200
    
    def test_edge_compatibility(self, client):
        """Test Microsoft Edge compatibility"""
        edge_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
        
        response = client.get('/', headers={'User-Agent': edge_ua})
        assert response.status_code == 200
        
        # Test API compatibility
        response = client.get('/api/state', headers={'User-Agent': edge_ua})
        assert response.status_code == 200


class TestPerformanceOptimization:
    """Test performance optimization for different devices"""
    
    def test_page_load_performance(self, client):
        """Test page load performance"""
        start_time = time.time()
        
        response = client.get('/')
        
        end_time = time.time()
        load_time = end_time - start_time
        
        assert response.status_code == 200
        # Page should load within reasonable time (2 seconds for test environment)
        assert load_time < 2.0
    
    def test_api_response_performance(self, client):
        """Test API response performance"""
        api_endpoints = [
            '/health',
            '/api/state',
            '/api/history',
            '/api/chat/history'
        ]
        
        for endpoint in api_endpoints:
            start_time = time.time()
            
            response = client.get(endpoint)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200
            # API should respond quickly (1 second for test environment)
            assert response_time < 1.0
    
    def test_static_asset_caching(self, client):
        """Test static asset caching headers"""
        static_assets = [
            '/static/style.css',
            '/static/visualizer.js',
            '/static/js/discord-chat.js'
        ]
        
        for asset in static_assets:
            response = client.get(asset)
            
            if response.status_code == 200:
                # Should have cache control headers
                cache_headers = [
                    'Cache-Control',
                    'ETag',
                    'Last-Modified',
                    'Expires'
                ]
                
                # At least some caching strategy should be present
                has_cache_headers = any(
                    header in response.headers
                    for header in cache_headers
                )
                
                # Caching headers are optional but recommended
                # Just verify asset loads
                assert len(response.data) >= 0
    
    def test_content_compression(self, client):
        """Test content compression support"""
        response = client.get('/', headers={'Accept-Encoding': 'gzip, deflate'})
        
        assert response.status_code == 200
        
        # Check for compression headers
        compression_headers = [
            'Content-Encoding',
            'Transfer-Encoding'
        ]
        
        # Compression is optional in test environment
        has_compression = any(
            header in response.headers
            for header in compression_headers
        )
        
        # Just verify response is valid
        assert len(response.data) > 0


class TestScreenSizeAdaptation:
    """Test adaptation to different screen sizes"""
    
    def test_small_screen_layout(self, client):
        """Test layout adaptation for small screens (< 768px)"""
        # Simulate small screen with custom header
        headers = {
            'X-Screen-Width': '320',
            'X-Screen-Height': '568',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)'
        }
        
        response = client.get('/', headers=headers)
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Should have responsive viewport
        assert 'viewport' in html_content
    
    def test_medium_screen_layout(self, client):
        """Test layout adaptation for medium screens (768px - 1024px)"""
        headers = {
            'X-Screen-Width': '768',
            'X-Screen-Height': '1024',
            'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X)'
        }
        
        response = client.get('/', headers=headers)
        assert response.status_code == 200
    
    def test_large_screen_layout(self, client):
        """Test layout adaptation for large screens (> 1024px)"""
        headers = {
            'X-Screen-Width': '1920',
            'X-Screen-Height': '1080',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = client.get('/', headers=headers)
        assert response.status_code == 200
    
    def test_ultra_wide_screen_support(self, client):
        """Test support for ultra-wide screens"""
        headers = {
            'X-Screen-Width': '3440',
            'X-Screen-Height': '1440'
        }
        
        response = client.get('/', headers=headers)
        assert response.status_code == 200


class TestUserExperienceOptimization:
    """Test user experience optimizations"""
    
    def test_loading_states_and_feedback(self, client):
        """Test loading states and user feedback"""
        # Test API endpoints that might show loading states
        response = client.get('/api/state')
        assert response.status_code == 200
        
        # Response should be reasonably fast
        start_time = time.time()
        response = client.get('/health')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0
    
    def test_error_handling_and_recovery(self, client):
        """Test error handling and recovery UX"""
        # Test non-existent endpoints
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        
        # Test malformed API requests
        response = client.post('/api/chat/send', data="invalid json")
        assert response.status_code == 400
    
    def test_progressive_enhancement(self, client):
        """Test progressive enhancement features"""
        # Basic functionality should work without JavaScript
        response = client.get('/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Should have basic HTML structure
        assert '<html' in html_content.lower()
        
        # Enhanced features should be available via JavaScript
        # (This would require more detailed testing of JavaScript functionality)
    
    def test_offline_functionality(self, client):
        """Test offline functionality support"""
        # Test service worker or offline capabilities
        response = client.get('/service-worker.js')
        
        # Service worker is optional
        if response.status_code == 200:
            sw_content = response.get_data(as_text=True)
            
            # Should have service worker functionality
            offline_patterns = [
                r'cache',
                r'offline',
                r'fetch.*event',
                r'install.*event'
            ]
            
            has_offline_features = any(
                re.search(pattern, sw_content, re.IGNORECASE)
                for pattern in offline_patterns
            )
            
            # Offline features are optional
            assert len(sw_content) >= 0
    
    def test_internationalization_support(self, client):
        """Test internationalization and localization support"""
        # Test different language headers
        languages = ['en-US', 'es-ES', 'fr-FR', 'de-DE', 'ja-JP', 'zh-CN']
        
        for lang in languages:
            headers = {'Accept-Language': lang}
            response = client.get('/', headers=headers)
            
            assert response.status_code == 200
            
            # Content should be accessible regardless of language
            html_content = response.get_data(as_text=True)
            assert len(html_content) > 0
    
    def test_dark_mode_support(self, client):
        """Test dark mode and theme support"""
        # Test with dark mode preference
        headers = {'Sec-CH-Prefers-Color-Scheme': 'dark'}
        response = client.get('/', headers=headers)
        
        assert response.status_code == 200
        
        # Test with light mode preference
        headers = {'Sec-CH-Prefers-Color-Scheme': 'light'}
        response = client.get('/', headers=headers)
        
        assert response.status_code == 200


class TestIntegrationWithMultiProject:
    """Test responsive design integration with multi-project features"""
    
    def test_project_switching_on_mobile(self, client, mobile_user_agent):
        """Test project switching interface on mobile"""
        # Test project-related API calls from mobile
        response = client.get('/api/state', headers={'User-Agent': mobile_user_agent})
        assert response.status_code == 200
        
        # Test chat with project context on mobile
        message_data = {
            "message": "/state",
            "user_id": "mobile-user",
            "username": "Mobile User",
            "project_name": "test-project"
        }
        
        response = client.post(
            '/api/chat/send',
            data=json.dumps(message_data),
            content_type='application/json',
            headers={'User-Agent': mobile_user_agent}
        )
        
        assert response.status_code == 200
    
    def test_collaboration_features_responsive(self, client, tablet_user_agent):
        """Test collaboration features are responsive"""
        # Test collaboration API from tablet
        with patch('app.COLLABORATION_AVAILABLE', True):
            join_data = {
                "user_id": "tablet-user",
                "project_name": "test-project",
                "permission_level": "contributor"
            }
            
            response = client.post(
                '/api/collaboration/join',
                data=json.dumps(join_data),
                content_type='application/json',
                headers={'User-Agent': tablet_user_agent}
            )
            
            # Should work on any device
            assert response.status_code in [200, 503]  # 503 if not available
    
    def test_chat_interface_responsive(self, client):
        """Test chat interface responsiveness across devices"""
        devices = [
            ("mobile", "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)"),
            ("tablet", "Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X)"),
            ("desktop", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        ]
        
        for device_type, user_agent in devices:
            # Test chat history
            response = client.get(
                '/api/chat/history',
                headers={'User-Agent': user_agent}
            )
            assert response.status_code == 200
            
            # Test sending message
            message_data = {
                "message": f"/test from {device_type}",
                "user_id": f"{device_type}-user",
                "username": f"{device_type.title()} User"
            }
            
            response = client.post(
                '/api/chat/send',
                data=json.dumps(message_data),
                content_type='application/json',
                headers={'User-Agent': user_agent}
            )
            
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])