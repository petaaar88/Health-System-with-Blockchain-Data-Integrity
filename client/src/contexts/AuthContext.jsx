import React, { createContext, useContext, useState, useEffect } from "react";
import { getRoleFromToken, getUserIdFromToken } from "../utils/jwtUtil";

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider!");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => {
    return localStorage.getItem("authToken");
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      validateToken();
    } else {
      setLoading(false);
    }
  }, []);

  const validateToken = async () => {
    try {
      const response = await fetch(import.meta.env.VITE_API_URL + "/api/auth/verify", {
        method:"POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
      
      if (response.ok) {
        const userData = await response.json();
        
         let new_user = {
            id: getUserIdFromToken(token),
            role: getRoleFromToken(token)
        }
        
        setUser(new_user);
      } else {
        logout();
      }
    } catch (error) {
      console.error("Token validation error:", error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (id, password) => {
    try {
      const response = await fetch(
        import.meta.env.VITE_API_URL + "/api/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ id, password }),
        }
      );

      const data = await response.json();
    
      if (response.ok) {
        setToken(data.access_token);

        let new_user = {
            id: getUserIdFromToken(data.access_token),
            role: getRoleFromToken(data.access_token)
        }

        setUser(new_user);
        localStorage.setItem("authToken", data.access_token);
        return { success: true };
      } else {
        return {
          success: false,
          error: data.message || "Invalid Credentials",
        };
      }
    } catch (error) {
      console.error("Login error:", error);
      return {
        success: false,
        error: "Internal Error",
      };
    }
  };

 
  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("authToken");
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated: !!token && !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
