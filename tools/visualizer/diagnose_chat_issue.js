// Complete Discord Chat Diagnostic
// Run this in the browser console at http://localhost:5000

console.clear();
console.log("%c🔍 Discord Chat Complete Diagnostic", "font-size: 16px; font-weight: bold; color: #4CAF50");
console.log("=====================================\n");

// Test 1: Check if page loaded correctly
console.log("%c1️⃣ Page Load Check", "font-size: 14px; font-weight: bold");
console.log("Document ready state:", document.readyState);
console.log("Scripts loaded:");
console.log("  • Socket.IO:", typeof io !== 'undefined');
console.log("  • DiscordChat class:", typeof DiscordChat !== 'undefined');
console.log("  • ChatComponents class:", typeof ChatComponents !== 'undefined');
console.log("  • StateVisualizer class:", typeof StateVisualizer !== 'undefined');

// Test 2: Check global instances
console.log("\n%c2️⃣ Global Instances Check", "font-size: 14px; font-weight: bold");
console.log("window.visualizer:", !!window.visualizer);
console.log("window.discordChat:", !!window.discordChat);
console.log("window.chatComponents:", !!window.chatComponents);

if (window.discordChat) {
    console.log("\n📊 DiscordChat instance details:");
    console.log("  • User ID:", window.discordChat.userId);
    console.log("  • Socket exists:", !!window.discordChat.socket);
    console.log("  • Socket connected:", window.discordChat.socket?.connected);
    console.log("  • Socket ID:", window.discordChat.socket?.id);
}

// Test 3: Check DOM elements
console.log("\n%c3️⃣ DOM Elements Check", "font-size: 14px; font-weight: bold");
const elements = {
    input: document.getElementById('chat-input-field'),
    button: document.getElementById('chat-send-btn'),
    messages: document.getElementById('chat-messages'),
    panel: document.getElementById('chat-panel'),
    autocomplete: document.getElementById('chat-autocomplete'),
    typing: document.getElementById('typing-indicators')
};

for (const [name, el] of Object.entries(elements)) {
    console.log(`${el ? '✅' : '❌'} ${name}:`, el ? `found (${el.tagName})` : 'NOT FOUND');
}

// Test 4: Check current state
console.log("\n%c4️⃣ Current State Check", "font-size: 14px; font-weight: bold");
if (elements.input && elements.button) {
    console.log("Input value:", `"${elements.input.value}"`);
    console.log("Button disabled:", elements.button.disabled);
    console.log("Button has click handlers:", getEventListeners ? getEventListeners(elements.button).click?.length || 0 : 'unknown');
    console.log("Input has input handlers:", getEventListeners ? getEventListeners(elements.input).input?.length || 0 : 'unknown');
}

// Test 5: Try to recreate the issue
console.log("\n%c5️⃣ Recreation Test", "font-size: 14px; font-weight: bold");
if (elements.input && elements.button) {
    // Save original value
    const originalValue = elements.input.value;
    
    // Test typing
    console.log("Setting input value to 'Test message'...");
    elements.input.value = 'Test message';
    elements.input.dispatchEvent(new Event('input', { bubbles: true }));
    
    setTimeout(() => {
        console.log("After input event:");
        console.log("  • Input value:", `"${elements.input.value}"`);
        console.log("  • Button disabled:", elements.button.disabled);
        
        if (elements.button.disabled) {
            console.log("%c❌ Button is still disabled!", "color: red; font-weight: bold");
            
            // Try to manually enable
            console.log("\nTrying manual enable...");
            elements.button.disabled = false;
            console.log("Button disabled after manual set:", elements.button.disabled);
        } else {
            console.log("%c✅ Button enabled correctly!", "color: green; font-weight: bold");
        }
        
        // Restore original value
        elements.input.value = originalValue;
        elements.input.dispatchEvent(new Event('input', { bubbles: true }));
    }, 100);
}

// Test 6: Check for errors
console.log("\n%c6️⃣ Error Check", "font-size: 14px; font-weight: bold");
console.log("Check browser console for any JavaScript errors above");

// Test 7: Socket.IO connection
console.log("\n%c7️⃣ Socket.IO Check", "font-size: 14px; font-weight: bold");
if (window.discordChat?.socket) {
    const socket = window.discordChat.socket;
    console.log("Socket details:");
    console.log("  • Connected:", socket.connected);
    console.log("  • ID:", socket.id);
    console.log("  • Transport:", socket.io?.engine?.transport?.name);
    
    // Try to emit a test message
    console.log("\nTrying to emit test message...");
    try {
        socket.emit('chat_command', {
            message: '/help',
            user_id: window.discordChat.userId,
            username: 'Diagnostic Test',
            session_id: null,
            project_name: 'default'
        });
        console.log("✅ Test message emitted");
    } catch (e) {
        console.log("❌ Failed to emit:", e.message);
    }
}

// Test 8: Manual fix attempt
console.log("\n%c8️⃣ Manual Fix Attempt", "font-size: 14px; font-weight: bold");
if (elements.input && elements.button && !window.discordChat) {
    console.log("DiscordChat not initialized. Attempting manual initialization...");
    
    if (typeof DiscordChat !== 'undefined' && window.visualizer?.socket) {
        try {
            window.discordChat = new DiscordChat(window.visualizer.socket, window.visualizer);
            console.log("✅ DiscordChat manually initialized");
        } catch (e) {
            console.log("❌ Manual initialization failed:", e.message);
        }
    } else {
        console.log("❌ Cannot initialize - missing dependencies");
    }
}

// Summary
console.log("\n%c📊 Diagnostic Summary", "font-size: 16px; font-weight: bold; color: #2196F3");
const issues = [];

if (!window.discordChat) issues.push("DiscordChat not initialized");
if (!elements.input) issues.push("Input element not found");
if (!elements.button) issues.push("Button element not found");
if (elements.button?.disabled && elements.input?.value?.trim()) issues.push("Button disabled with text");
if (window.discordChat && !window.discordChat.socket?.connected) issues.push("Socket not connected");

if (issues.length === 0) {
    console.log("%c✅ No issues found! Chat should be working.", "color: green; font-weight: bold");
} else {
    console.log("%c❌ Issues found:", "color: red; font-weight: bold");
    issues.forEach(issue => console.log(`  • ${issue}`));
}

console.log("\n💡 Next steps:");
console.log("1. Check if there are any red errors in the console above");
console.log("2. Try opening http://localhost:5000/test_simple_chat.html to test in isolation");
console.log("3. Hard refresh the page (Ctrl+F5) and run this diagnostic again");
console.log("4. Check the Network tab (F12) to ensure all JS files loaded successfully");