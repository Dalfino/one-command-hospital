/**
 * Medplum Bot/service auth — OAuth2 client_credentials with a JWT assertion.
 *
 * MEDPLUM_AUTH_JSON (env) shape:
 *   { "clientId": "...", "privateKey": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
 *     "algorithm": "RS384", "tokenUrl": "http://medplum:8080/oauth2/token" }
 *
 * If MEDPLUM_AUTH_JSON is unset/empty, the mediator runs in UNAUTHENTICATED
 * v0 mode (sandbox only) — every writeback carries a loud warning header.
 * Register the client in Medplum (ClientApplication) with the matching
 * public key; never put secrets in the repo.
 */
import jwt from "jsonwebtoken";
import { randomUUID } from "node:crypto";

let cached = { token: null, exp: 0 };

function config() {
  const raw = process.env.MEDPLUM_AUTH_JSON || "";
  if (!raw.trim()) return null;
  try {
    return JSON.parse(raw);
  } catch {
    throw new Error("MEDPLUM_AUTH_JSON is not valid JSON");
  }
}

export function authMode() {
  return config() ? "jwt-client-assertion" : "unauthenticated-v0";
}

export async function getMedplumToken() {
  const cfg = config();
  if (!cfg) return null;

  const now = Math.floor(Date.now() / 1000);
  if (cached.token && cached.exp - 60 > now) return cached.token;

  const tokenUrl = cfg.tokenUrl || "http://medplum:8080/oauth2/token";
  const assertion = jwt.sign(
    {
      iss: cfg.clientId,
      sub: cfg.clientId,
      aud: tokenUrl,
      exp: now + 300,
      jti: randomUUID(),
    },
    cfg.privateKey,
    { algorithm: cfg.algorithm || "RS384" }
  );

  const body = new URLSearchParams({
    grant_type: "client_credentials",
    scope: "openid",
    client_assertion_type: "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    client_assertion: assertion,
  });

  const r = await fetch(tokenUrl, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!r.ok) throw new Error(`medplum token exchange failed: ${r.status}`);
  const data = await r.json();
  cached = { token: data.access_token, exp: now + (data.expires_in || 300) };
  return cached.token;
}

export async function fhirHeaders(extra = {}) {
  const token = await getMedplumToken();
  const h = { "Content-Type": "application/fhir+json", ...extra };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}
