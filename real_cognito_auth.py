#!/usr/bin/env python3
"""
Real Cognito Authentication for Bedrock Chat
Extracts real AWS Cognito user tokens by authenticating a user
"""

import json
import subprocess
import sys
import webbrowser
import base64
import time
from urllib.parse import urlencode, parse_qs

def get_cognito_info():
    """Get Cognito User Pool and Client information"""
    try:
        # Get the current user's identity
        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity'],
            capture_output=True, text=True, check=True
        )
        identity = json.loads(result.stdout)
        print(f"✅ Authenticated as: {identity.get('Arn', 'Unknown')}")
        
        # Get Cognito User Pools
        result = subprocess.run([
            'aws', 'cognito-idp', 'list-user-pools',
            '--max-results', '20'
        ], capture_output=True, text=True, check=True)
        
        user_pools = json.loads(result.stdout)
        if not user_pools.get('UserPools'):
            print("❌ No Cognito User Pools found")
            return None
            
        user_pool_id = user_pools['UserPools'][0]['Id']
        print(f"📋 Found User Pool: {user_pool_id}")
        
        # Get User Pool Clients
        result = subprocess.run([
            'aws', 'cognito-idp', 'list-user-pool-clients',
            '--user-pool-id', user_pool_id,
            '--max-results', '20'
        ], capture_output=True, text=True, check=True)
        
        clients = json.loads(result.stdout)
        if not clients.get('UserPoolClients'):
            print("❌ No User Pool Clients found")
            return None
            
        client_id = clients['UserPoolClients'][0]['ClientId']
        print(f"🔑 Found Client ID: {client_id}")
        
        # Get User Pool details to find the domain
        result = subprocess.run([
            'aws', 'cognito-idp', 'describe-user-pool',
            '--user-pool-id', user_pool_id
        ], capture_output=True, text=True, check=True)
        
        user_pool_details = json.loads(result.stdout)
        domain = user_pool_details['UserPool'].get('Domain', '')
        print(f"🌐 Found Domain: {domain}")
        
        return {
            'user_pool_id': user_pool_id,
            'client_id': client_id,
            'domain': domain,
            'identity': identity
        }
        
    except subprocess.CalledProcessError as e:
        print(f"❌ AWS CLI error: {e}")
        print(f"Error output: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def get_user_credentials():
    """Get user credentials from user input"""
    try:
        print("\n🔐 Please enter your Cognito credentials:")
        email = input("📧 Email: ").strip()
        password = input("🔑 Password: ").strip()
        
        if not email or not password:
            print("❌ Email and password are required")
            return None
            
        return {
            'email': email,
            'password': password
        }
        
    except KeyboardInterrupt:
        print("\n❌ Input cancelled")
        return None
    except Exception as e:
        print(f"❌ Error getting credentials: {e}")
        return None

def authenticate_user_and_get_tokens(cognito_info, credentials):
    """Authenticate user and get real tokens"""
    try:
        print(f"\n🔐 Authenticating user: {credentials['email']}")
        
        # First, we need to initiate auth
        result = subprocess.run([
            'aws', 'cognito-idp', 'initiate-auth',
            '--auth-flow', 'USER_PASSWORD_AUTH',
            '--client-id', cognito_info['client_id'],
            '--auth-parameters', f'USERNAME={credentials["email"]},PASSWORD={credentials["password"]}'
        ], capture_output=True, text=True, check=True)
        
        auth_result = json.loads(result.stdout)
        
        # Check if we need to respond to a challenge
        if 'ChallengeName' in auth_result:
            challenge_name = auth_result['ChallengeName']
            session = auth_result.get('Session')
            
            print(f"⚠️  Challenge required: {challenge_name}")
            
            if challenge_name == 'NEW_PASSWORD_REQUIRED':
                # Ask user for new password
                print("⚠️  New password required. Please enter a new password:")
                new_password = input("🔑 New Password: ").strip()
                
                if not new_password:
                    print("❌ New password is required")
                    return None
                
                # Respond to new password challenge
                result = subprocess.run([
                    'aws', 'cognito-idp', 'respond-to-auth-challenge',
                    '--client-id', cognito_info['client_id'],
                    '--challenge-name', 'NEW_PASSWORD_REQUIRED',
                    '--session', session,
                    '--challenge-responses', f'USERNAME={credentials["email"]},NEW_PASSWORD={new_password}'
                ], capture_output=True, text=True, check=True)
                
                auth_result = json.loads(result.stdout)
            
            elif challenge_name == 'SMS_MFA' or challenge_name == 'SOFTWARE_TOKEN_MFA':
                print("❌ MFA challenge not supported in this script")
                return None
        
        # Check if we have tokens
        if 'AuthenticationResult' in auth_result:
            tokens = auth_result['AuthenticationResult']
            print("✅ Authentication successful!")
            
            return {
                'access_token': tokens.get('AccessToken'),
                'id_token': tokens.get('IdToken'),
                'refresh_token': tokens.get('RefreshToken'),
                'expires_in': tokens.get('ExpiresIn'),
                'token_type': tokens.get('TokenType')
            }
        else:
            print("❌ No authentication result found")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Authentication failed: {e}")
        print(f"Error output: {e.stderr}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error during authentication: {e}")
        return None

def decode_jwt_token(token):
    """Decode JWT token to get payload"""
    try:
        # Split the token
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode the payload (second part)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        
        # Decode base64
        decoded = base64.b64decode(payload)
        return json.loads(decoded.decode('utf-8'))
    except Exception as e:
        print(f"❌ Failed to decode token: {e}")
        return None

def generate_real_token_commands(cognito_info, credentials, tokens):
    """Generate JavaScript commands with real tokens"""
    
    # Decode the ID token to get user info
    id_token_payload = decode_jwt_token(tokens['id_token'])
    
    # Extract username from token or use email
    username = id_token_payload.get('cognito:username', credentials['email']) if id_token_payload else credentials['email']
    
    # Method 1: Real Cognito Identity Service Provider format
    method1 = f"""
// Method 1: Real Cognito Identity Service Provider format
localStorage.setItem('CognitoIdentityServiceProvider.{cognito_info["client_id"]}.{username}.accessToken', '{tokens["access_token"]}');
localStorage.setItem('CognitoIdentityServiceProvider.{cognito_info["client_id"]}.{username}.idToken', '{tokens["id_token"]}');
localStorage.setItem('CognitoIdentityServiceProvider.{cognito_info["client_id"]}.{username}.refreshToken', '{tokens["refresh_token"]}');
localStorage.setItem('CognitoIdentityServiceProvider.{cognito_info["client_id"]}.LastAuthUser', '{username}');

console.log('✅ Real Cognito tokens stored!');
"""
    
    # Method 2: Real Amplify v6 format
    method2 = f"""
// Method 2: Real Amplify v6 format
const realSession = {{
    tokens: {{
        accessToken: {{
            toString: () => '{tokens["access_token"]}',
            payload: {json.dumps(id_token_payload) if id_token_payload else "{}"}
        }},
        idToken: {{
            toString: () => '{tokens["id_token"]}',
            payload: {json.dumps(id_token_payload) if id_token_payload else "{}"}
        }},
        refreshToken: {{
            toString: () => '{tokens["refresh_token"]}'
        }}
    }},
    credentials: {{
        accessKeyId: 'real_access_key',
        secretAccessKey: 'real_secret_key',
        sessionToken: 'real_session_token'
    }}
}};

// Override the fetchAuthSession function
window.fetchAuthSession = async () => realSession;

// Also store in Amplify format
localStorage.setItem('amplify-authenticator-authToken', JSON.stringify(realSession));
localStorage.setItem('amplify-authenticator-user', JSON.stringify({{
    username: '{username}',
    attributes: {{
        email: '{credentials["email"]}',
        sub: '{id_token_payload.get("sub", "") if id_token_payload else ""}'
    }}
}}));

console.log('✅ Real Amplify session stored!');
"""
    
    # Method 3: Direct function override with real tokens
    method3 = f"""
// Method 3: Direct function override with real tokens
const realTokens = {{
    accessToken: '{tokens["access_token"]}',
    idToken: '{tokens["id_token"]}',
    refreshToken: '{tokens["refresh_token"]}',
    expiresIn: {tokens["expires_in"]},
    tokenType: '{tokens["token_type"]}'
}};

// Override fetchAuthSession to return real tokens
window.fetchAuthSession = async () => {{
    return {{
        tokens: {{
            accessToken: {{
                toString: () => realTokens.accessToken,
                payload: {json.dumps(id_token_payload) if id_token_payload else "{}"}
            }},
            idToken: {{
                toString: () => realTokens.idToken,
                payload: {json.dumps(id_token_payload) if id_token_payload else "{}"}
            }},
            refreshToken: {{
                toString: () => realTokens.refreshToken
            }}
        }}
    }};
}};

console.log('✅ Real tokens injected via function override!');
"""
    
    return method1, method2, method3

def main():
    print("🔐 Bedrock Chat Real Cognito Authentication")
    print("=" * 50)
    
    # Get Cognito info
    cognito_info = get_cognito_info()
    if not cognito_info:
        print("❌ Failed to get Cognito information.")
        sys.exit(1)
    
    # Get user credentials
    credentials = get_user_credentials()
    if not credentials:
        print("❌ Failed to get user credentials.")
        sys.exit(1)
    
    # Authenticate user and get tokens
    tokens = authenticate_user_and_get_tokens(cognito_info, credentials)
    if not tokens:
        print("❌ Failed to authenticate user and get tokens.")
        print("💡 Note: Check your email and password, or if MFA is required.")
        sys.exit(1)
    
    # Generate injection commands
    method1, method2, method3 = generate_real_token_commands(cognito_info, credentials, tokens)
    
    # Frontend URL
    frontend_url = "https://d36lcrfb6vw3t7.cloudfront.net"
    
    print(f"\n🎯 Ready with REAL Cognito tokens!")
    print(f"👤 User: {credentials['email']}")
    print(f"🔑 Client ID: {cognito_info['client_id']}")
    print(f"🏊 User Pool: {cognito_info['user_pool_id']}")
    print(f"⏰ Token expires in: {tokens['expires_in']} seconds")
    
    print(f"\n📋 Instructions:")
    print(f"1. Open Bedrock Chat: {frontend_url}")
    print(f"2. Open browser console (F12)")
    print(f"3. Try the injection methods below:")
    
    print(f"\n🔧 Method 1: Real Cognito Format")
    print("-" * 40)
    print(method1)
    
    print(f"\n🔧 Method 2: Real Amplify Format")
    print("-" * 40)
    print(method2)
    
    print(f"\n🔧 Method 3: Direct Function Override")
    print("-" * 40)
    print(method3)
    
    print(f"\n💡 Tips:")
    print(f"- These are REAL Cognito tokens from actual user authentication")
    print(f"- Tokens will expire in {tokens['expires_in']} seconds")
    print(f"- Try each method one at a time")
    print(f"- After injection, refresh the page")
    
    # Ask if user wants to open the frontend
    try:
        response = input(f"\n🌐 Open Bedrock Chat in browser? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            webbrowser.open(frontend_url)
            print("✅ Opened Bedrock Chat!")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    
    print(f"\n🎯 Next steps:")
    print(f"1. Navigate to: {frontend_url}")
    print(f"2. Open browser console (F12)")
    print(f"3. Copy and paste the injection commands")
    print(f"4. Refresh the page after injection")

if __name__ == "__main__":
    main() 