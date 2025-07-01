// Discord Chat Send Issue Diagnostic
// Copy and paste this entire script into the browser console at http://localhost:5000

console.clear();
console.log("🔍 Discord Chat Send Issue Diagnostic");
console.log("=====================================\n");

// Test 1: Check elements
console.log("1️⃣ Checking DOM elements...");
const elements = {
    input: document.getElementById('chat-input-field'),
    button: document.getElementById('chat-send-btn'),
    messages: document.getElementById('chat-messages'),
    panel: document.getElementById('chat-panel')
};

for (const [name, el] of Object.entries(elements)) {
    console.log(`   ${el ? '✅' : '❌'} ${name}: ${el ? 'found' : 'NOT FOUND'}`);
}

// Test 2: Check DiscordChat instance
console.log("\n2️⃣ Checking DiscordChat instance...");
if (window.discordChat) {
    console.log("   ✅ window.discordChat exists");
    console.log(`   • User ID: ${window.discordChat.userId}`);
    console.log(`   • Socket exists: ${!!window.discordChat.socket}`);
    console.log(`   • Socket connected: ${window.discordChat.socket?.connected}`);
} else {
    console.log("   ❌ window.discordChat NOT FOUND");
    console.log(`   • DiscordChat class exists: ${!!window.DiscordChat}`);
}

// Test 3: Check current state
console.log("\n3️⃣ Checking current state...");
if (elements.input && elements.button) {
    console.log(`   • Input value: "${elements.input.value}"`);
    console.log(`   • Button disabled: ${elements.button.disabled}`);
    console.log(`   • Button onclick: ${elements.button.onclick}`);
    
    // Check event listeners
    const listeners = getEventListeners ? getEventListeners(elements.button) : null;
    if (listeners) {
        console.log(`   • Button click listeners: ${listeners.click?.length || 0}`);
    }
}

// Test 4: Test the send flow
console.log("\n4️⃣ Testing send flow...");
console.log("   Setting up monitoring...");

// Monitor sendMessage calls
if (window.discordChat) {
    const original = window.discordChat.sendMessage;
    window.discordChat.sendMessage = function() {
        console.log("   🎯 sendMessage CALLED!");
        console.log("   • Arguments:", arguments);
        console.log("   • This:", this);
        const result = original.apply(this, arguments);
        console.log("   • Result:", result);
        return result;
    };
}

// Monitor socket emissions
if (window.discordChat?.socket) {
    const originalEmit = window.discordChat.socket.emit;
    window.discordChat.socket.emit = function(event, data) {
        console.log(`   📡 Socket emit: ${event}`, data);
        return originalEmit.apply(this, arguments);
    };
}

// Monitor button clicks
if (elements.button) {
    elements.button.addEventListener('click', (e) => {
        console.log("   🖱️ Button clicked!");
        console.log(`   • Disabled: ${e.target.disabled}`);
        console.log(`   • Input value: "${elements.input.value}"`);
    }, true);
}

// Test 5: Try to send a message
console.log("\n5️⃣ Attempting to send test message...");
if (elements.input && elements.button) {
    // Set value
    elements.input.value = "Diagnostic test message";
    elements.input.dispatchEvent(new Event('input', { bubbles: true }));
    
    setTimeout(() => {
        console.log(`   • Input value: "${elements.input.value}"`);
        console.log(`   • Button disabled: ${elements.button.disabled}`);
        
        if (!elements.button.disabled) {
            console.log("   • Clicking button...");
            elements.button.click();
        } else {
            console.log("   ❌ Button is disabled!");
            
            // Check why it might be disabled
            console.log("\n6️⃣ Investigating why button is disabled...");
            
            // Look for the event handler
            const inputHandlers = getEventListeners ? getEventListeners(elements.input) : null;
            if (inputHandlers) {
                console.log(`   • Input listeners: ${JSON.stringify(Object.keys(inputHandlers))}`);
                console.log(`   • Input 'input' listeners: ${inputHandlers.input?.length || 0}`);
            }
            
            // Try to manually trigger the handler
            console.log("   • Trying manual trigger...");
            const event = new Event('input', { bubbles: true });
            elements.input.dispatchEvent(event);
            
            setTimeout(() => {
                console.log(`   • Button disabled after manual trigger: ${elements.button.disabled}`);
            }, 100);
        }
    }, 100);
}

// Test 6: Direct socket test
console.log("\n7️⃣ Direct socket test...");
if (window.discordChat?.socket?.connected) {
    try {
        window.discordChat.socket.emit('chat_command', {
            message: '/help',
            user_id: window.discordChat.userId,
            username: 'Diagnostic',
            session_id: null,
            project_name: 'default'
        });
        console.log("   ✅ Direct socket emission successful");
    } catch (e) {
        console.log(`   ❌ Socket emission failed: ${e.message}`);
    }
} else {
    console.log("   ❌ Socket not connected");
}

console.log("\n📊 Diagnostic complete!");
console.log("Check the output above for issues.");
console.log("\n💡 Common issues:");
console.log("• discordChat not initialized → Page didn't load properly");
console.log("• Socket not connected → WebSocket connection failed");
console.log("• Button stays disabled → Event handler not attached");
console.log("• sendMessage not called → Click event not firing");

// Return diagnostic summary
const summary = {
    elementsFound: Object.values(elements).every(el => el),
    discordChatExists: !!window.discordChat,
    socketConnected: window.discordChat?.socket?.connected || false,
    buttonEnabled: !elements.button?.disabled
};

console.log("\n📋 Summary:", summary);