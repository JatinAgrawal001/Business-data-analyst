/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { ToastContainer } from './components/common/ToastContainer';
import { Menu, X } from 'lucide-react';

// Views
import { LandingView } from './views/LandingView';
import { AuthLoginView } from './views/AuthLoginView';
import { AuthSignupView } from './views/AuthSignupView';
import { AuthForgotPasswordView } from './views/AuthForgotPasswordView';
import { DashboardView } from './views/DashboardView';
import { ProjectsView } from './views/ProjectsView';
import { NewProjectView } from './views/NewProjectView';
import { DatasetUploadView } from './views/DatasetUploadView';
import { DatasetDetailView } from './views/DatasetDetailView';
import { AnalyticsView } from './views/AnalyticsView';
import { InsightsView } from './views/InsightsView';
import { RecommendationsView } from './views/RecommendationsView';
import { ForecastView } from './views/ForecastView';
import { ChatView } from './views/ChatView';
import { ReportsView } from './views/ReportsView';
import { SettingsView } from './views/SettingsView';
import { ProfileView } from './views/ProfileView';

const AppContent: React.FC = () => {
  const { currentRoute, user, isLoading } = useApp();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // Initial loading indicator
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0A0B10] flex flex-col items-center justify-center relative overflow-hidden">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-sky-500 animate-pulse flex items-center justify-center shadow-xl shadow-indigo-500/25 mb-4">
          <div className="w-5 h-5 rounded-full border-2 border-white border-t-transparent animate-spin" />
        </div>
        <p className="text-xs font-semibold text-slate-300 font-display tracking-wide">
          Connecting to InsightFlow...
        </p>
      </div>
    );
  }

  // Determine current active component based on route and auth state
  const renderCurrentView = () => {
    if (currentRoute === '/login') return <AuthLoginView />;
    if (currentRoute === '/signup') return <AuthSignupView />;
    if (currentRoute === '/forgot-password') return <AuthForgotPasswordView />;
    if (currentRoute === '/landing') return <LandingView />;

    // Protected Routes: Require authenticated user
    if (!user) {
      return <AuthLoginView />;
    }

    // Authenticated / Main App Views
    if (currentRoute === '/' || currentRoute === '/dashboard') return <DashboardView />;
    if (currentRoute === '/projects') return <ProjectsView />;
    if (currentRoute === '/projects/new') return <NewProjectView />;
    if (currentRoute === '/datasets/upload') return <DatasetUploadView />;
    if (currentRoute.startsWith('/datasets')) return <DatasetDetailView />;
    if (currentRoute.startsWith('/analytics')) return <AnalyticsView />;
    if (currentRoute.startsWith('/insights')) return <InsightsView />;
    if (currentRoute.startsWith('/recommendations')) return <RecommendationsView />;
    if (currentRoute.startsWith('/forecast')) return <ForecastView />;
    if (currentRoute.startsWith('/chat')) return <ChatView />;
    if (currentRoute === '/reports') return <ReportsView />;
    if (currentRoute === '/settings') return <SettingsView />;
    if (currentRoute === '/profile') return <ProfileView />;

    return <DashboardView />;
  };

  const isStandaloneRoute = ['/landing', '/login', '/signup', '/forgot-password'].includes(currentRoute) || !user;

  return (
    <div className="relative min-h-screen bg-[#0A0B10] text-slate-200 font-sans selection:bg-indigo-500/30 selection:text-indigo-200 overflow-x-hidden">
      {/* Ambient Frosted Glass Background Orbs */}
      <div className="fixed top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="fixed top-[30%] right-[15%] w-[30%] h-[30%] bg-purple-600/5 rounded-full blur-[100px] pointer-events-none" />

      {isStandaloneRoute ? (
        <main className="relative z-10">{renderCurrentView()}</main>
      ) : (
        <div className="relative z-10 flex min-h-screen">
          {/* Mobile Overlay */}
          {mobileSidebarOpen && (
            <div
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 lg:hidden"
              onClick={() => setMobileSidebarOpen(false)}
            />
          )}

          {/* Sidebar */}
          <Sidebar
            mobileOpen={mobileSidebarOpen}
            onMobileClose={() => setMobileSidebarOpen(false)}
          />

          {/* Main Layout Container */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* Mobile Header Bar with Hamburger */}
            <div className="lg:hidden flex items-center justify-between h-14 px-4 backdrop-blur-xl bg-[#0A0B10]/80 border-b border-white/10 sticky top-0 z-20">
              <button
                onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
                className="p-2 rounded-xl bg-white/5 border border-white/10 text-slate-300 hover:text-white cursor-pointer"
                aria-label="Toggle navigation menu"
              >
                {mobileSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
              <span className="text-sm font-bold font-display text-white">InsightFlow AI</span>
              <div className="w-9" />
            </div>

            {/* Desktop Navbar */}
            <Navbar />

            {/* Viewport Content Area */}
            <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto animate-in fade-in duration-200">
              {renderCurrentView()}
            </main>
          </div>
        </div>
      )}

      {/* Global Toast Alerts */}
      <ToastContainer />
    </div>
  );
};

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
