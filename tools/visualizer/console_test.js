// Direct browser console test
// Copy and paste this entire script into the browser console at http://localhost:5000

console.log("🧪 Starting direct console test...");

// Test 1: Check if elements exist
const input = document.getElementById('chat-input-field');
const button = document.getElementById('chat-send-btn');

if (!input || !button) {
    console.error("❌ Elements not found!");
    console.log("Input element:", input);
    console.log("Button element:", button);
} else {
    console.log("✅ Elements found");
    
    // Test 2: Check current state
    console.log("\n📊 Current state:");
    console.log("- Input value:", input.value);
    console.log("- Button disabled:", button.disabled);
    
    // Test 3: Try enabling/disabling directly
    console.log("\n🔧 Testing direct manipulation:");
    
    // Test disable
    button.disabled = true;
    console.log("- Set button.disabled = true");
    console.log("- Button is now disabled:", button.disabled);
    
    // Test enable
    button.disabled = false;
    console.log("- Set button.disabled = false");
    console.log("- Button is now disabled:", button.disabled);
    
    // Test 4: Simulate typing
    console.log("\n⌨️ Simulating typing:");
    input.value = "Test message";
    input.dispatchEvent(new Event('input', { bubbles: true }));
    console.log("- Set input value to 'Test message'");
    console.log("- Dispatched input event");
    console.log("- Button is now disabled:", button.disabled);
    
    // Test 5: Clear input
    console.log("\n🧹 Clearing input:");
    input.value = "";
    input.dispatchEvent(new Event('input', { bubbles: true }));
    console.log("- Cleared input value");
    console.log("- Dispatched input event");
    console.log("- Button is now disabled:", button.disabled);
    
    // Test 6: Check event listeners
    console.log("\n🎯 Checking event listeners:");
    console.log("- Input element events:", getEventListeners ? getEventListeners(input) : "getEventListeners not available");
    console.log("- Button element events:", getEventListeners ? getEventListeners(button) : "getEventListeners not available");
    
    // Test 7: Check DiscordChat instance
    console.log("\n🔍 Looking for DiscordChat instance:");
    if (window.discordChat) {
        console.log("✅ Found window.discordChat");
    } else if (window.DiscordChat) {
        console.log("✅ Found window.DiscordChat class");
    } else {
        console.log("❌ DiscordChat not found on window");
    }
}

console.log("\n✅ Test complete! Check the results above.");
console.log("💡 If the button doesn't respond to input events, the JavaScript may not be fully loaded.");