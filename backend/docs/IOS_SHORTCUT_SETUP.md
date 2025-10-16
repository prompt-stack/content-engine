# iOS Shortcut Setup Guide

## Overview

This guide will help you set up an iOS Shortcut to capture text content (like ChatGPT conversations) and send them directly to your Content Engine API.

## Prerequisites

- iPhone or iPad running iOS 13 or later
- Shortcuts app installed (comes pre-installed on iOS)
- Content Engine API running and accessible from your device
- Your API endpoint URL

## Setup Instructions

### Step 1: Create a New Shortcut

1. Open the **Shortcuts** app on your iPhone
2. Tap the **+** button to create a new shortcut
3. Name your shortcut something like "Save to Content Engine" or "Capture Text"

### Step 2: Add "Get Clipboard" Action

1. Tap **Add Action**
2. Search for "Get Clipboard"
3. Add the **Get Clipboard** action to your shortcut

This will capture whatever text you have copied to your clipboard.

### Step 3: Add "Get Text from Input" Action

1. Search for "Get Text from Input"
2. Add this action after the clipboard action
3. This ensures we're working with plain text

### Step 4: Add "URL" Action (API Endpoint)

1. Search for "URL"
2. Add the **URL** action
3. Enter your API endpoint:
   ```
   http://localhost:9765/api/capture/text
   ```
   **Note:** If your API is deployed, replace `localhost:9765` with your actual domain

### Step 5: Add "Get Contents of URL" Action

1. Search for "Get Contents of URL"
2. Add this action
3. Configure it with these settings:
   - **Method:** POST
   - **Headers:** Add a header
     - Key: `Content-Type`
     - Value: `application/json`
   - **Request Body:** JSON
   - **JSON:** Tap "Add field" and create:
     ```json
     {
       "title": "iOS Capture",
       "content": [Clipboard],
       "meta": {
         "source": "ios-shortcut",
         "device": "iPhone",
         "timestamp": "[Current Date]"
       }
     }
     ```

### Step 6: Add Error Handling (Optional)

1. Add a "Show Alert" action at the end
2. Set it to show "Content saved successfully!"
3. This provides feedback that the capture worked

### Step 7: Test Your Shortcut

1. Copy some text (e.g., from Notes or Safari)
2. Run your shortcut
3. Check your Content Engine API to verify the content was saved

## Usage

### From Any App:
1. Select and copy the text you want to save
2. Open the Shortcuts app
3. Tap your "Save to Content Engine" shortcut
4. You'll see a confirmation that the content was saved

### Add to Share Sheet (Recommended):
1. Open your shortcut in the Shortcuts app
2. Tap the settings icon (⚙️)
3. Enable "Show in Share Sheet"
4. Now you can share text directly from any app to your Content Engine!

## Advanced Configuration

### Custom Titles

Modify the JSON body to prompt for a title:

1. Before the "Get Contents of URL" action, add "Ask for Input"
2. Prompt: "Enter a title for this capture"
3. In the JSON body, replace `"iOS Capture"` with the variable from "Ask for Input"

### Automatic Metadata

The shortcut can automatically include:
- Current date/time: Use "Current Date" variable
- Device name: Use "Device Details" action
- Location: Use "Get Current Location" action (requires permission)

## Troubleshooting

### "Could not connect to server"
- Verify your API is running
- Check that the URL is correct
- Ensure your device is on the same network (if using localhost)
- Consider using ngrok or a public URL for remote access

### "Invalid JSON"
- Make sure all quotes are proper JSON quotes
- Verify the JSON structure matches the example above
- Check that variables are inserted correctly

### "401 Unauthorized"
- For MVP, authentication is disabled
- If you've enabled auth, add an Authorization header with your token

## Example Shortcut Configuration

Here's a complete example of what your shortcut should look like:

```
1. Get Clipboard
2. Get Text from Input
3. URL: http://localhost:9765/api/capture/text
4. Get Contents of URL
   - Method: POST
   - Headers: Content-Type: application/json
   - Request Body: JSON
     {
       "title": "iOS Capture",
       "content": [Clipboard],
       "meta": {
         "source": "ios-shortcut",
         "device": "iPhone"
       }
     }
5. Show Alert: "Saved successfully!"
```

## Next Steps

Once your shortcut is working:
1. Add it to your Home Screen for quick access
2. Use Siri to run it with voice commands
3. Create variations for different types of content
4. Explore automation triggers (e.g., save at specific times)

## API Reference

- **Endpoint:** `POST /api/capture/text`
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "title": "Optional title",
    "content": "Required content text",
    "meta": {
      "source": "source identifier",
      "any": "custom fields"
    }
  }
  ```
- **Response:**
  ```json
  {
    "id": 123,
    "title": "Optional title",
    "created_at": "2025-10-16T14:00:00"
  }
  ```

## Support

For issues or questions:
1. Check the API logs for errors
2. Verify the shortcut configuration
3. Test the API endpoint directly with curl
4. Consult the Content Engine documentation
