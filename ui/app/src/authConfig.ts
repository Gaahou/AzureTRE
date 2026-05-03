import { Configuration, PublicClientApplication } from "@azure/msal-browser";
import config from "./config.json";

// Determine if we're in offline mode
const isOfflineMode = config.deploymentMode === "offline";

// MSAL configuration for Azure AD (online mode)
const msalConfiguration: Configuration = {
  auth: {
    clientId: config.rootClientId,
    authority: `${config.activeDirectoryUri}/${config.rootTenantId}`,
    redirectUri: `${window.location.protocol}//${window.location.hostname}:${window.location.port}`,
    postLogoutRedirectUri: `${window.location.protocol}//${window.location.hostname}:${window.location.port}/logout`,
  },
};

// Keycloak configuration for offline mode
const keycloakConfiguration = {
  url: config.keycloakUrl || "http://localhost:8080",
  realm: config.keycloakRealm || "AzureTRE",
  clientId: config.keycloakClientId || "tre-ui-client",
  redirectUri: `${window.location.protocol}//${window.location.hostname}:${window.location.port}`,
  postLogoutRedirectUri: `${window.location.protocol}//${window.location.hostname}:${window.location.port}/logout`,
};

// Export authentication configuration based on deployment mode
export const authMode = isOfflineMode ? "keycloak" : "azuread";
export const pca = !isOfflineMode ? new PublicClientApplication(msalConfiguration) : null;
export const keycloakConfig = isOfflineMode ? keycloakConfiguration : null;

// Keycloak authorization endpoints (for offline mode)
export const keycloakEndpoints = isOfflineMode ? {
  authorize: `${keycloakConfiguration.url}/realms/${keycloakConfiguration.realm}/protocol/openid-connect/auth`,
  token: `${keycloakConfiguration.url}/realms/${keycloakConfiguration.realm}/protocol/openid-connect/token`,
  logout: `${keycloakConfiguration.url}/realms/${keycloakConfiguration.realm}/protocol/openid-connect/logout`,
  userInfo: `${keycloakConfiguration.url}/realms/${keycloakConfiguration.realm}/protocol/openid-connect/userinfo`,
} : null;
