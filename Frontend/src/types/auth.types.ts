// Auth Types based on Swagger API specification

export type RegisterRequest = {
  email: string;
  password: string;
  fullName: string;
  phoneNumber: string;
};

export type LoginRequest = {
  email: string;
  password: string;
  ipAddress: string;
  userAgent: string;
  deviceFingerprint?: string;
};

export type AuthenticationResponse = {
  refreshToken: string | null;
  accessToken: string | null;
  id: string;
  email: string | null;
  fullName: string | null;
  phoneNumber: string | null;
  emailVerified: boolean;
};

export type ApiResponse<T> = {
  success: boolean;
  message: string | null;
  data: T;
  statusCode: number;
  meta: unknown;
  errorCode: string | null;
};

export type AuthenticationResponseApiResponse = ApiResponse<AuthenticationResponse>;
