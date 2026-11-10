import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import { useToast } from './ToastContext';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();

  const fetchCurrentUser = useCallback(async () => {
    try {
      const res = await api.auth.getMe();
      setUser(res.data);
    } catch (err) {
      console.warn('Failed to restore user session:', err);
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token, fetchCurrentUser]);

  const login = async (email, password) => {
    try {
      const res = await api.auth.login({ email, password });
      const { access_token, user: loggedUser } = res.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(loggedUser);
      addToast(`Welcome back, ${loggedUser.full_name}!`, 'success');
      return loggedUser;
    } catch (err) {
      const msg = err.userMessage || 'Login failed. Please check your credentials.';
      addToast(msg, 'error');
      throw err;
    }
  };

  const register = async (userData) => {
    try {
      const res = await api.auth.register(userData);
      const { access_token, user: newUser } = res.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(newUser);
      addToast('Registration successful! Welcome to Shikayat Karo.', 'success');
      return newUser;
    } catch (err) {
      const msg = err.userMessage || 'Registration failed.';
      addToast(msg, 'error');
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    addToast('You have been logged out.', 'info');
  };

  const quickSwitchPersona = async (email, password = 'password123') => {
    try {
      await login(email, password);
    } catch (err) {
      console.error('Quick switch failed:', err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: user?.role || 'guest',
        isAuthenticated: !!user,
        loading,
        login,
        register,
        logout,
        quickSwitchPersona,
        refreshUser: fetchCurrentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
