/**
 * Keycloak OIDC Authentication Helper
 *
 * Provides OAuth 2.0 authorization code flow for Keycloak authentication.
 * This module is used in offline deployment mode as an alternative to Azure AD/MSAL.
 */

import { keycloakConfig, keycloakEndpoints } from './authConfig';

export interface KeycloakUser {
  sub: string;
  preferred_username: string;
  email?: string;
  name?: string;
  given_name?: string;
  family_name?: string;
  realm_access?: {
    roles: string[];
  };
}

export interface KeycloakTokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  id_token?: string;
}

/**
 * Generate a random string for PKCE code verifier
 */
function generateCodeVerifier(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

/**
 * Generate PKCE code challenge from verifier
 */
async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const hash = await crypto.subtle.digest('SHA-256', data);
  const base64 = btoa(String.fromCharCode(...new Uint8Array(hash)));
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/**
 * Initiate Keycloak login flow
 */
export async function loginWithKeycloak(): Promise<void> {
  if (!keycloakConfig || !keycloakEndpoints) {
    throw new Error('Keycloak not configured - check deploymentMode in config');
  }

  // Generate PKCE parameters
  const codeVerifier = generateCodeVerifier();
  const codeChallenge = await generateCodeChallenge(codeVerifier);
  const state = generateCodeVerifier(); // Random state for CSRF protection

  // Store PKCE verifier and state in session storage
  sessionStorage.setItem('pkce_code_verifier', codeVerifier);
  sessionStorage.setItem('oauth_state', state);

  // Build authorization URL
  const params = new URLSearchParams({
    client_id: keycloakConfig.clientId,
    redirect_uri: keycloakConfig.redirectUri,
    response_type: 'code',
    scope: 'openid profile email',
    state: state,
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
  });

  const authUrl = `${keycloakEndpoints.authorize}?${params.toString()}`;

  // Redirect to Keycloak login
  window.location.href = authUrl;
}

/**
 * Handle OAuth callback and exchange authorization code for tokens
 */
export async function handleKeycloakCallback(): Promise<KeycloakTokenResponse> {
  if (!keycloakConfig || !keycloakEndpoints) {
    throw new Error('Keycloak not configured');
  }

  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  const state = urlParams.get('state');
  const storedState = sessionStorage.getItem('oauth_state');
  const codeVerifier = sessionStorage.getItem('pkce_code_verifier');

  if (!code) {
    throw new Error('No authorization code received');
  }

  if (state !== storedState) {
    throw new Error('State mismatch - possible CSRF attack');
  }

  if (!codeVerifier) {
    throw new Error('No code verifier found in session');
  }

  // Exchange authorization code for tokens
  const tokenParams = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: keycloakConfig.clientId,
    code: code,
    redirect_uri: keycloakConfig.redirectUri,
    code_verifier: codeVerifier,
  });

  const response = await fetch(keycloakEndpoints.token, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: tokenParams.toString(),
  });

  if (!response.ok) {
    throw new Error(`Token exchange failed: ${response.statusText}`);
  }

  const tokens: KeycloakTokenResponse = await response.json();

  // Clean up session storage
  sessionStorage.removeItem('pkce_code_verifier');
  sessionStorage.removeItem('oauth_state');

  // Store tokens
  sessionStorage.setItem('access_token', tokens.access_token);
  sessionStorage.setItem('refresh_token', tokens.refresh_token);
  sessionStorage.setItem('token_expiry', String(Date.now() + tokens.expires_in * 1000));

  return tokens;
}

/**
 * Get current user info from Keycloak
 */
export async function getKeycloakUser(): Promise<KeycloakUser> {
  if (!keycloakEndpoints) {
    throw new Error('Keycloak not configured');
  }

  const accessToken = sessionStorage.getItem('access_token');
  if (!accessToken) {
    throw new Error('No access token available');
  }

  const response = await fetch(keycloakEndpoints.userInfo, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch user info: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Refresh access token using refresh token
 */
export async function refreshKeycloakToken(): Promise<KeycloakTokenResponse> {
  if (!keycloakConfig || !keycloakEndpoints) {
    throw new Error('Keycloak not configured');
  }

  const refreshToken = sessionStorage.getItem('refresh_token');
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  const tokenParams = new URLSearchParams({
    grant_type: 'refresh_token',
    client_id: keycloakConfig.clientId,
    refresh_token: refreshToken,
  });

  const response = await fetch(keycloakEndpoints.token, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: tokenParams.toString(),
  });

  if (!response.ok) {
    throw new Error(`Token refresh failed: ${response.statusText}`);
  }

  const tokens: KeycloakTokenResponse = await response.json();

  // Update stored tokens
  sessionStorage.setItem('access_token', tokens.access_token);
  sessionStorage.setItem('refresh_token', tokens.refresh_token);
  sessionStorage.setItem('token_expiry', String(Date.now() + tokens.expires_in * 1000));

  return tokens;
}

/**
 * Check if access token is expired or about to expire
 */
export function isTokenExpired(): boolean {
  const expiry = sessionStorage.getItem('token_expiry');
  if (!expiry) return true;

  const expiryTime = parseInt(expiry, 10);
  const now = Date.now();

  // Consider token expired if it expires in less than 5 minutes
  return now >= expiryTime - (5 * 60 * 1000);
}

/**
 * Logout from Keycloak
 */
export async function logoutFromKeycloak(): Promise<void> {
  if (!keycloakConfig || !keycloakEndpoints) {
    throw new Error('Keycloak not configured');
  }

  const idToken = sessionStorage.getItem('id_token');

  // Clear local storage
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('refresh_token');
  sessionStorage.removeItem('id_token');
  sessionStorage.removeItem('token_expiry');

  // Build logout URL
  const params = new URLSearchParams({
    post_logout_redirect_uri: keycloakConfig.postLogoutRedirectUri,
    ...(idToken && { id_token_hint: idToken }),
  });

  const logoutUrl = `${keycloakEndpoints.logout}?${params.toString()}`;

  // Redirect to Keycloak logout
  window.location.href = logoutUrl;
}

/**
 * Get current access token
 */
export function getAccessToken(): string | null {
  return sessionStorage.getItem('access_token');
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  const token = getAccessToken();
  return token !== null && !isTokenExpired();
}