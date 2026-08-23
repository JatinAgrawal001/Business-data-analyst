import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Analysis, Dataset, Project, Report, ToastMessage, User } from '../types';
import { api } from '../services/api';
import { supabaseService, mapSupabaseUserToAppUser } from '../services/supabase';
import { Session } from '@supabase/supabase-js';

interface AppContextType {
  user: User | null;
  session: Session | null;
  projects: Project[];
  datasets: Dataset[];
  reports: Report[];
  currentProject: Project | null;
  currentDataset: Dataset | null;
  analysis: Analysis | null;
  currentAnalysis: Analysis | null;
  loading: boolean;
  isLoading: boolean;
  analysisLoading: boolean;
  currentRoute: string;
  routeParam: string | null;
  toasts: ToastMessage[];
  setCurrentRoute: (route: string, param?: string) => void;
  setCurrentDatasetById: (id: string) => Promise<void>;
  setCurrentProjectById: (id: string) => Promise<void>;
  deleteDataset: (id: string) => Promise<void>;
  refreshDatasets: () => Promise<void>;
  refreshProjects: () => Promise<void>;
  refreshReports: () => Promise<void>;
  refreshAnalysis: (datasetId?: string) => Promise<void>;
  showToast: (type: ToastMessage['type'], title: string, message?: string) => void;
  removeToast: (id: string) => void;
  login: (email: string, password?: string) => Promise<void>;
  signUp: (name: string, email: string, password?: string, company?: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (updates: Partial<User>) => Promise<void>;
  resetPassword: (email: string) => Promise<{ success: boolean; message: string }>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [currentDataset, setCurrentDataset] = useState<Dataset | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [analysisLoading, setAnalysisLoading] = useState<boolean>(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Parse path and param from window.location.pathname / hash
  const parseCurrentLocation = () => {
    const hash = window.location.hash.replace('#', '');
    const pathname = hash || window.location.pathname || '/dashboard';
    
    // Check dynamic routes
    const dynamicPrefixes = ['/datasets/', '/analytics/', '/insights/', '/recommendations/', '/forecast/', '/chat/'];
    for (const prefix of dynamicPrefixes) {
      if (pathname.startsWith(prefix)) {
        const baseRoute = prefix.slice(0, -1);
        const param = pathname.slice(prefix.length);
        return { route: baseRoute, param: param || null };
      }
    }

    if (pathname === '/' || pathname === '') {
      return { route: '/dashboard', param: null };
    }

    return { route: pathname, param: null };
  };

  const initialLoc = parseCurrentLocation();
  const [currentRoute, setCurrentRouteState] = useState<string>(initialLoc.route);
  const [routeParam, setRouteParam] = useState<string | null>(initialLoc.param);

  const setCurrentRoute = (route: string, param?: string) => {
    setCurrentRouteState(route);
    setRouteParam(param || null);
    const fullPath = param ? `${route}/${param}` : route;
    window.location.hash = fullPath;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Sync with browser hash changes
  useEffect(() => {
    const handleHashChange = () => {
      const parsed = parseCurrentLocation();
      setCurrentRouteState(parsed.route);
      setRouteParam(parsed.param);
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Load app data for active user
  const loadAppData = async (currentUser: User | null) => {
    try {
      const [projectList, datasetList, reportList] = await Promise.all([
        api.getProjects(currentUser?.id),
        api.getDatasets(undefined, currentUser?.id),
        api.getReports()
      ]);

      setProjects(projectList);
      setDatasets(datasetList);
      setReports(reportList);

      const initialDataset = datasetList[0] || null;
      setCurrentDataset(initialDataset);
      const initialProject = projectList.find((p) => p.id === initialDataset?.projectId) || projectList[0] || null;
      setCurrentProject(initialProject);

      if (initialDataset) {
        const initialAnalysis = await api.getAnalysisByDatasetId(initialDataset.id);
        setAnalysis(initialAnalysis);
      }
    } catch {
      // Graceful fallback for initial dataset loading
    }
  };

  // Initialize Supabase Auth session & onAuthStateChange listener
  useEffect(() => {
    let isMounted = true;

    const initAuth = async () => {
      try {
        setLoading(true);
        // Check active session from Supabase
        const initialSession = await supabaseService.getSession();
        if (initialSession && initialSession.user) {
          setSession(initialSession);
          const profile = await supabaseService.getProfile(initialSession.user.id);
          const appUser = mapSupabaseUserToAppUser(initialSession.user, profile);
          if (isMounted) {
            setUser(appUser);
            await loadAppData(appUser);
          }
        } else {
          // Check local or fallback user
          const currentUser = await api.getCurrentUser();
          if (isMounted) {
            setUser(currentUser);
            await loadAppData(currentUser);
          }
        }
      } catch {
        // Fallback silently if offline or initial load fails
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    initAuth();

    // Subscribe to real-time auth changes from Supabase
    const { data: authSubscription } = supabaseService.onAuthStateChange(async (event, newSession) => {
      if (!isMounted) return;
      setSession(newSession);

      if (event === 'SIGNED_IN' || event === 'USER_UPDATED' || event === 'TOKEN_REFRESHED') {
        if (newSession?.user) {
          const profile = await supabaseService.getProfile(newSession.user.id);
          const appUser = mapSupabaseUserToAppUser(newSession.user, profile);
          setUser(appUser);
          await loadAppData(appUser);
        }
      } else if (event === 'SIGNED_OUT') {
        setUser(null);
        setSession(null);
        setProjects([]);
        setDatasets([]);
        setReports([]);
        setCurrentProject(null);
        setCurrentDataset(null);
        setAnalysis(null);
      }
    });

    return () => {
      isMounted = false;
      authSubscription?.subscription?.unsubscribe();
    };
  }, []);

  // Respond to route parameter changes when dataset is specified
  useEffect(() => {
    if (routeParam && datasets.length > 0) {
      const match = datasets.find((d) => d.id === routeParam);
      if (match && (!currentDataset || currentDataset.id !== match.id)) {
        setCurrentDataset(match);
        refreshAnalysis(match.id);
      }
    }
  }, [routeParam, datasets]);

  const showToast = (type: ToastMessage['type'], title: string, message?: string) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`;
    const newToast: ToastMessage = { id, type, title, message, duration: 4500 };
    setToasts((prev) => [...prev, newToast]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const setCurrentDatasetById = async (id: string) => {
    try {
      const ds = datasets.find((d) => d.id === id) || (await api.getDatasetById(id));
      if (ds) {
        setCurrentDataset(ds);
        const proj = projects.find((p) => p.id === ds.projectId);
        if (proj) setCurrentProject(proj);
        await refreshAnalysis(ds.id);
      }
    } catch (err) {
      showToast('error', 'Could not switch dataset', String(err));
    }
  };

  const setCurrentProjectById = async (id: string) => {
    try {
      const proj = projects.find((p) => p.id === id) || (await api.getProjectById(id));
      if (proj) {
        setCurrentProject(proj);
        if (proj.defaultDatasetId) {
          await setCurrentDatasetById(proj.defaultDatasetId);
        }
      }
    } catch (err) {
      showToast('error', 'Could not switch project', String(err));
    }
  };

  const deleteDataset = async (id: string) => {
    try {
      await api.deleteDataset(id);
      const remaining = datasets.filter((d) => d.id !== id);
      setDatasets(remaining);
      
      if (currentDataset?.id === id) {
        const nextDataset = remaining[0] || null;
        setCurrentDataset(nextDataset);
        if (nextDataset) {
          const nextAnalysis = await api.getAnalysisByDatasetId(nextDataset.id);
          setAnalysis(nextAnalysis);
        } else {
          setAnalysis(null);
        }
      }
      showToast('success', 'Dataset Deleted', 'Dataset has been removed from workspace.');
    } catch (err: any) {
      showToast('error', 'Delete Failed', err.message || 'Could not delete dataset');
      throw err;
    }
  };

  const refreshDatasets = async () => {
    const list = await api.getDatasets(undefined, user?.id);
    setDatasets(list);
  };

  const refreshProjects = async () => {
    const list = await api.getProjects(user?.id);
    setProjects(list);
  };

  const refreshReports = async () => {
    const list = await api.getReports();
    setReports(list);
  };

  const refreshAnalysis = async (datasetId?: string) => {
    const targetId = datasetId || currentDataset?.id;
    if (!targetId) return;

    try {
      setAnalysisLoading(true);
      const res = await api.getAnalysisByDatasetId(targetId);
      setAnalysis(res);
    } catch {
      showToast('error', 'Analysis computation failed');
    } finally {
      setAnalysisLoading(false);
    }
  };

  const login = async (email: string, password?: string) => {
    try {
      const usr = await api.login(email, password);
      setUser(usr);
      await loadAppData(usr);
      showToast('success', 'Authenticated Successfully', `Welcome back, ${usr.name}!`);
      setCurrentRoute('/dashboard');
    } catch (err: any) {
      showToast('error', 'Authentication Failed', err.message || 'Invalid credentials');
      throw err;
    }
  };

  const signUp = async (name: string, email: string, password?: string, company?: string) => {
    try {
      const usr = await api.signup(name, email, password, company);
      setUser(usr);
      await loadAppData(usr);
      showToast('success', 'Account Created', `Welcome to InsightFlow, ${name}!`);
      setCurrentRoute('/dashboard');
    } catch (err: any) {
      showToast('error', 'Registration Failed', err.message || 'Could not complete signup');
      throw err;
    }
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch {
      // Ignore network errors during logout
    }
    setUser(null);
    setSession(null);
    setProjects([]);
    setDatasets([]);
    setReports([]);
    setCurrentProject(null);
    setCurrentDataset(null);
    setAnalysis(null);
    showToast('info', 'Logged out successfully');
    setCurrentRoute('/login');
  };

  const updateProfile = async (updates: Partial<User>) => {
    try {
      const updated = await api.updateProfile(updates);
      setUser(updated);
      showToast('success', 'Profile Updated', 'Your profile information has been saved.');
    } catch (err: any) {
      showToast('error', 'Profile Update Failed', err.message);
      throw err;
    }
  };

  const resetPassword = async (email: string) => {
    return api.forgotPassword(email);
  };

  return (
    <AppContext.Provider
      value={{
        user,
        session,
        projects,
        datasets,
        reports,
        currentProject,
        currentDataset,
        analysis,
        currentAnalysis: analysis,
        loading,
        isLoading: loading,
        analysisLoading,
        currentRoute,
        routeParam,
        toasts,
        setCurrentRoute,
        setCurrentDatasetById,
        setCurrentProjectById,
        deleteDataset,
        refreshDatasets,
        refreshProjects,
        refreshReports,
        refreshAnalysis,
        showToast,
        removeToast,
        login,
        signUp,
        logout,
        updateProfile,
        resetPassword
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
