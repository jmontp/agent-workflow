#!/bin/bash

echo "🔍 Comprehensive Discord Interface Diagnostic"
echo "==========================================="
echo

# 1. Check file modification times
echo "📅 File modification times:"
ls -la static/js/discord-chat.js | awk '{print "discord-chat.js: " $6 " " $7 " " $8}'
ls -la static/css/discord-chat.css | awk '{print "discord-chat.css: " $6 " " $7 " " $8}'
echo

# 2. Check if our fixes are in the files
echo "✏️ Checking for our fixes in discord-chat.js:"
grep -n "Initial state - disable send button" static/js/discord-chat.js || echo "❌ Initial state comment NOT FOUND"
grep -n "sendButton.disabled = messageInput.value.trim().length === 0;" static/js/discord-chat.js || echo "❌ Initial state code NOT FOUND"
grep -n "console.log('Input changed, has content:'" static/js/discord-chat.js || echo "❌ Console log NOT FOUND"
echo

# 3. Check what the server is actually serving
echo "🌐 Checking what server is serving:"
curl -s http://localhost:5000/static/js/discord-chat.js | grep -c "Initial state - disable send button" | xargs -I {} echo "Initial state comment found: {} times"
curl -s http://localhost:5000/static/js/discord-chat.js | grep -c "sendButton.disabled = messageInput.value.trim" | xargs -I {} echo "Initial state code found: {} times"
echo

# 4. Check for multiple input listeners
echo "🎯 Checking for duplicate event listeners:"
grep -n "addEventListener('input'" static/js/discord-chat.js | wc -l | xargs -I {} echo "Number of input event listeners in file: {}"
echo

# 5. Create a minimal test
echo "🧪 Creating minimal test file..."
cat > test_minimal.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Minimal Chat Test</title>
</head>
<body>
    <h1>Minimal Chat Test</h1>
    <input type="text" id="chat-input-field" placeholder="Type here...">
    <button id="chat-send-btn">Send</button>
    <div id="status"></div>
    
    <script>
        const input = document.getElementById('chat-input-field');
        const button = document.getElementById('chat-send-btn');
        const status = document.getElementById('status');
        
        // Initial state
        button.disabled = input.value.trim().length === 0;
        status.textContent = `Initial: Button disabled = ${button.disabled}`;
        
        // Input handler
        input.addEventListener('input', (e) => {
            const hasContent = e.target.value.trim().length > 0;
            button.disabled = !hasContent;
            status.textContent = `Input: "${e.target.value}" | Button disabled = ${button.disabled}`;
            console.log('Input changed:', e.target.value, 'Button disabled:', button.disabled);
        });
        
        console.log('Minimal test loaded');
    </script>
</body>
</html>
EOF

echo "✅ Created test_minimal.html"
echo "   Open this file in your browser to test the functionality in isolation"
echo

# 6. Summary
echo "📊 Summary:"
echo "- Check browser console (F12) for any JavaScript errors"
echo "- Try the minimal test file: file://$(pwd)/test_minimal.html"
echo "- If minimal test works but main app doesn't, there's a conflict"
echo "- Try a different browser (Firefox, Edge) to rule out Chrome issues"
echo

echo "🔄 To force a complete refresh:"
echo "1. Close ALL browser windows (not just tabs)"
echo "2. Clear browser data for localhost:5000"
echo "3. Restart the browser"
echo "4. Navigate to http://localhost:5000"