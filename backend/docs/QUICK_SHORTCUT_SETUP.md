# Quick iOS Shortcut Setup (Copy-Paste Method)

## Option 1: Direct Import URL (Fastest)

You can use this URL scheme to quickly create the shortcut:

```
shortcuts://import-shortcut/?url=https://www.icloud.com/shortcuts/YOUR_SHORTCUT_ID
```

However, since shortcuts need to be created first, here's the fastest manual method:

## Option 2: 2-Minute Setup (Recommended)

### Quick Steps:

1. **Open Shortcuts app** on your iPhone
2. **Tap "+" to create new shortcut**
3. **Copy and configure these 4 actions:**

#### Action 1: Get Clipboard
- Search: "Get Clipboard"
- Add it

#### Action 2: Set Variable
- Search: "Set Variable"
- Name it: "CapturedText"

#### Action 3: Get Contents of URL
- Search: "Get Contents of URL"
- Tap "Show More"
- Configure:
  - **URL:** `http://YOUR_SERVER:9765/api/capture/text`
  - **Method:** POST
  - **Headers:**
    - Add New Header
    - Key: `Content-Type`
    - Value: `application/json`
  - **Request Body:** JSON
  - Tap "Add field" and paste this structure:

```json
{
  "title": "iOS Capture",
  "content": [Variable: CapturedText],
  "meta": {
    "source": "ios-shortcut",
    "device": "iPhone"
  }
}
```

**Note:** For the `"content"` value, tap where it says `[Variable: CapturedText]` and select your "CapturedText" variable from the dropdown.

#### Action 4: Show Notification
- Search: "Show Notification"
- Text: "Saved to Content Engine!"

### Using localhost from iPhone

If your API is on your Mac:
1. Find your Mac's local IP: `System Settings > Network > WiFi > Details > TCP/IP`
2. Use that IP instead of localhost: `http://192.168.1.XXX:9765/api/capture/text`

## Option 3: One-Line Command (Terminal → QR Code)

Generate a QR code that creates the shortcut:

```bash
# Install qrencode if needed
brew install qrencode

# Generate QR code for the API endpoint
echo "http://$(ipconfig getifaddr en0):9765/api/capture/text" | qrencode -o ~/Desktop/api-endpoint-qr.png

open ~/Desktop/api-endpoint-qr.png
```

Then scan this QR code when setting up the shortcut's URL field.

## Option 4: Use Shortcuts Share Sheet

If someone else creates the shortcut, they can:
1. Open the shortcut in Shortcuts app
2. Tap the ••• menu
3. Tap "Share"
4. Send you the iCloud link
5. You tap the link and it auto-installs!

## Option 5: Use Toolbox Pro App (Advanced)

If you want programmatic creation:
1. Install "Toolbox Pro" app (paid)
2. Use its "Create Shortcut" action
3. Pass JSON configuration

## Testing Your Shortcut

1. Copy this text: `"Test capture from iOS Shortcut"`
2. Run your shortcut
3. Check your API: `curl http://localhost:9765/api/capture/list`

## Troubleshooting

### "Cannot Connect to Server"
Run this on your Mac to find the correct IP:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
```

Use that IP in your shortcut URL.

### "Invalid Response"
The API endpoint must be accessible from your iPhone. Options:
- Use same WiFi network
- Use ngrok: `ngrok http 9765`
- Deploy to a public server

## Share Your Shortcut

Once created, you can share it:
1. Open shortcut in Shortcuts app
2. Tap ••• (three dots)
3. Tap "Share" icon
4. Choose "Copy iCloud Link"
5. Share that link with others!

The link will look like: `https://www.icloud.com/shortcuts/xxxxx`
