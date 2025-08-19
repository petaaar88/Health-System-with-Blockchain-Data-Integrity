import { jwtDecode } from "jwt-decode";

export const decodeToken = (token) => {
  try {
    if (!token) return null;
    return jwtDecode(token);
  } catch (error) {
    console.error("Error decoding token:", error);
    return null;
  }
};

export const getRoleFromToken = (token) => {
  const decoded = decodeToken(token);
  return decoded?.user_type || null;
};

export const getUserIdFromToken = (token) => {
  return decodeToken(token)?.sub || null;
};

export const isTokenExpired = (token) => {
  try {
    const decoded = decodeToken(token);
    if (!decoded || !decoded.exp) return true;

    return decoded.exp * 1000 < Date.now();
  } catch (error) {
    return true;
  }
};
