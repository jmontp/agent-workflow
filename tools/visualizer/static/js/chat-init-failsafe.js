/**
 * Failsafe Chat Initialization
 * Ensures Discord chat is properly initialized even with timing issues
 */

(function() {
    'use strict';
    
    let initAttempts = 0;
    const maxAttempts = 10;
    const attemptDelay = 500; // 500ms between attempts
    
    console.log('🛡️ Chat initialization failsafe loaded');
    
    function attemptChatInitialization() {
        initAttempts++;
        console.log(`🔄 Chat init attempt ${initAttempts}/${maxAttempts}`);
        
        // Check if already initialized
        if (window.discordChat && window.discordChat.socket) {
            console.log('✅ Discord chat already initialized');
            return true;
        }
        
        // Check dependencies
        const depsReady = (
            typeof DiscordChat !== 'undefined' &&
            typeof ChatComponents !== 'undefined' &&
            window.visualizer &&
            window.visualizer.socket
        );
        
        if (!depsReady) {
            console.log('⏳ Dependencies not ready:', {
                DiscordChat: typeof DiscordChat !== 'undefined',
                ChatComponents: typeof ChatComponents !== 'undefined',
                visualizer: !!window.visualizer,
                socket: !!(window.visualizer?.socket)
            });
            
            if (initAttempts < maxAttempts) {
                setTimeout(attemptChatInitialization, attemptDelay);
            } else {
                console.error('❌ Failed to initialize chat after', maxAttempts, 'attempts');
            }
            return false;
        }
        
        // Try to initialize
        try {
            console.log('🚀 Attempting to initialize Discord chat...');
            
            // Initialize ChatComponents if needed
            if (!window.chatComponents) {
                window.chatComponents = new ChatComponents();
                console.log('✅ ChatComponents initialized');
            }
            
            // Initialize DiscordChat
            window.discordChat = new DiscordChat(window.visualizer.socket, window.visualizer);
            console.log('✅ DiscordChat initialized successfully');
            
            // Verify initialization
            const elements = {
                input: document.getElementById('chat-input-field'),
                button: document.getElementById('chat-send-btn')
            };
            
            if (elements.input && elements.button) {
                // Force initial state check
                const hasContent = elements.input.value.trim().length > 0;
                elements.button.disabled = !hasContent;
                console.log('✅ Initial button state set:', { disabled: elements.button.disabled });
                
                // Add a test handler to verify events work
                elements.input.addEventListener('input', () => {
                    console.log('📝 Failsafe: Input event detected');
                }, { once: true });
            }
            
            // Integrate with visualizer if function exists
            if (typeof integrateChatWithVisualizer === 'function') {
                integrateChatWithVisualizer();
                console.log('✅ Chat integrated with visualizer');
            }
            
            // Dispatch custom event to signal initialization
            window.dispatchEvent(new CustomEvent('discordChatInitialized', {
                detail: { discordChat: window.discordChat }
            }));
            
            return true;
            
        } catch (error) {
            console.error('❌ Error initializing chat:', error);
            console.error('Stack:', error.stack);
            
            if (initAttempts < maxAttempts) {
                console.log('🔄 Retrying in', attemptDelay, 'ms...');
                setTimeout(attemptChatInitialization, attemptDelay);
            }
            return false;
        }
    }
    
    // Start initialization attempts when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(attemptChatInitialization, 100); // Small delay for other scripts
        });
    } else {
        // DOM already loaded
        setTimeout(attemptChatInitialization, 100);
    }
    
    // Also provide manual initialization function
    window.initializeChatManually = function() {
        console.log('🔧 Manual chat initialization requested');
        initAttempts = 0; // Reset attempts
        return attemptChatInitialization();
    };
    
    // Debug helper
    window.debugChat = function() {
        console.log('🐛 Chat Debug Info:');
        console.log('  discordChat:', window.discordChat);
        console.log('  chatComponents:', window.chatComponents);
        console.log('  visualizer:', window.visualizer);
        
        if (window.discordChat) {
            console.log('  userId:', window.discordChat.userId);
            console.log('  socket:', window.discordChat.socket);
            console.log('  socket connected:', window.discordChat.socket?.connected);
        }
        
        const input = document.getElementById('chat-input-field');
        const button = document.getElementById('chat-send-btn');
        
        console.log('  DOM elements:');
        console.log('    input:', input);
        console.log('    button:', button);
        
        if (input && button) {
            console.log('  Current state:');
            console.log('    input value:', input.value);
            console.log('    button disabled:', button.disabled);
        }
    };
    
})();