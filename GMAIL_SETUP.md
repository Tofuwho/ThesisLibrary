# Gmail Email Setup Guide

## Quick Setup Steps

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account: https://myaccount.google.com/
2. Click on **Security** in the left sidebar
3. Under "Signing in to Google", enable **2-Step Verification** if not already enabled

### Step 2: Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
   - Or navigate: Google Account → Security → 2-Step Verification → App passwords
2. Select **Mail** as the app
3. Select **Other (Custom name)** as the device
4. Enter a name like "Thesis Library Django"
5. Click **Generate**
6. Copy the 16-character password (it will look like: `abcd efgh ijkl mnop`)

### Step 3: Update Settings
Open `thesis_site/settings.py` and replace:

```python
EMAIL_HOST_USER = 'your-email@gmail.com'  # Replace with your Gmail
EMAIL_HOST_PASSWORD = 'your-app-password'  # Replace with the 16-char app password
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'  # Replace with your Gmail
```

**Example:**
```python
EMAIL_HOST_USER = 'mythesislibrary@gmail.com'
EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'  # Your generated app password
DEFAULT_FROM_EMAIL = 'mythesislibrary@gmail.com'
```

### Step 4: Restart Django Server
After updating settings, restart your Django development server:
```bash
# Stop the server (Ctrl+C) and restart:
python manage.py runserver
```

### Step 5: Test Email
Try signing up again - you should now receive emails in your Gmail inbox!

## Security Note (Optional but Recommended)

For better security, use environment variables instead of hardcoding:

1. Create a `.env` file in your project root:
```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

2. Install python-decouple:
```bash
pip install python-decouple
```

3. Update settings.py to use:
```python
from decouple import config

EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
```

## Troubleshooting

**If emails still don't arrive:**
1. Check spam/junk folder
2. Verify the app password is correct (no spaces, all 16 characters)
3. Make sure 2FA is enabled
4. Check Django console for error messages
5. Verify Gmail account isn't locked or restricted

**Common Errors:**
- "Username and Password not accepted" → Wrong app password or 2FA not enabled
- "Connection refused" → Check firewall/network settings
- "Authentication failed" → App password expired or incorrect

