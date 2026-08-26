import http from "./http";
import type { UserPublic } from "../stores/auth";

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: UserPublic;
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const response = await http.post<TokenResponse>(
    "/api/v1/auth/login",
    payload,
  );

  return response.data;
}

export async function register(payload: RegisterPayload): Promise<UserPublic> {
  const response = await http.post<UserPublic>(
    "/api/v1/auth/register",
    payload,
  );

  return response.data;
}
