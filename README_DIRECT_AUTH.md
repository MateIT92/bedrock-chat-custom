# Direct Authentication for Bedrock Chat

This approach allows you to inject authentication tokens directly into the Bedrock Chat frontend without using iframes, eliminating cross-origin restrictions.

## How It Works

Since the frontend doesn't need to open in an iframe, we can:

1. **Extract AWS Cognito information** using AWS CLI
2. **Generate mock authentication tokens** that match the expected format
3. **Inject tokens via browser console** on the same origin as the frontend
4. **Bypass authentication** by mocking the `fetchAuthSession()` function

## Prerequisites

- Python 3.6+
- AWS CLI configured with appropriate permissions
- Access to the Bedrock Chat frontend URL

## Quick Start

### Windows

```bash
# Double-click the batch file
run_auth.bat
```

### Linux/Mac

```bash
# Make the script executable
chmod +x direct_auth.py

# Run the script
python direct_auth.py
```

## Step-by-Step Process

1. **Run the authentication script**:

   ```bash
   python direct_auth.py
   ```

2. **The script will**:

   - Extract your AWS identity
   - Find Cognito User Pools and Clients
   - Generate injection commands
   - Optionally open the frontend in your browser

3. **On the Bedrock Chat page**:
   - Open browser console (F12)
   - Copy and paste the provided injection commands
   - Refresh the page

## Injection Methods

The script provides three different injection methods:

### Method 1: Mock fetchAuthSession

```javascript
// Override the fetchAuthSession function
window.fetchAuthSession = async () => mockSession;
```

### Method 2: Cognito Format

```javascript
// Store tokens in Cognito Identity Service Provider format
localStorage.setItem(
  "CognitoIdentityServiceProvider.{clientId}.{username}.accessToken",
  "mock_access_token"
);
```

### Method 3: Amplify Format

```javascript
// Store tokens in Amplify v6 format
localStorage.setItem(
  "amplify-authenticator-authToken",
  JSON.stringify(amplifySession)
);
```

## Why This Works

1. **No Cross-Origin Issues**: Since we're not using iframes, there are no cross-origin localStorage restrictions
2. **Same Origin Access**: Tokens are injected directly into the frontend's origin
3. **Function Override**: We can override the `fetchAuthSession()` function to return mock data
4. **Multiple Formats**: We provide multiple token storage formats to handle different scenarios

## Advantages Over Iframe Approach

- ✅ **No cross-origin restrictions**
- ✅ **Direct access to frontend localStorage**
- ✅ **Can override JavaScript functions**
- ✅ **Simpler implementation**
- ✅ **More reliable token injection**

## Troubleshooting

### Script Fails to Run

- Ensure AWS CLI is installed and configured
- Check that you have permissions to list Cognito resources
- Verify Python is installed and in your PATH

### Injection Doesn't Work

- Try each injection method one at a time
- Check browser console for error messages
- Ensure you're on the correct frontend URL
- Refresh the page after injection

### Frontend Still Shows Login

- The mock tokens may not have the correct format
- Try different injection methods
- Check if the frontend expects real tokens (not mock ones)
- Verify the user has proper permissions in the Cognito User Pool

## Security Considerations

⚠️ **Important**: This is a proof-of-concept approach using mock tokens. In production:

- Use real, valid tokens from proper authentication flow
- Implement proper token validation
- Consider security implications of function overriding
- Use HTTPS for all communications
- Implement proper session management

## Customization

You can modify the script to:

- Use specific User Pool IDs and Client IDs
- Target specific usernames
- Generate different token payloads
- Add more injection methods
- Integrate with your authentication system

## Files

- `direct_auth.py` - Main authentication script
- `simple_auth_injection.py` - Alternative approach with HTML page
- `run_auth.bat` - Windows batch file for easy execution
- `README_DIRECT_AUTH.md` - This documentation

## Next Steps

For production use, consider:

1. **Real Token Generation**: Implement proper token generation instead of mock tokens
2. **Secure Injection**: Use more secure methods for token injection
3. **Custom Domain**: Deploy Bedrock Chat under your own domain for better integration
4. **API Integration**: Use the backend APIs directly for authentication
5. **SSO Integration**: Implement proper Single Sign-On with your identity provider
