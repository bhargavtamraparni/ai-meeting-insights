import React from 'react';
import { Link } from 'react-router-dom';

// A simple, abstract SVG for our logo
const LogoIcon = () => (
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="32" height="32" rx="8" fill="rgb(79 70 229)"/>
    <path d="M12 20L16 16L12 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M20 12L20 20" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-800">
      <header className="bg-white/80 backdrop-blur-lg sticky top-0 z-10 border-b border-slate-200">
        <nav className="container mx-auto px-4 lg:px-8 py-3 flex items-center justify-center">
          <Link to="/" className="flex items-center gap-3">
            <span className="text-4xl font-bold tracking-tight text-slate-900">
              Meeting Insights
            </span>
          </Link>
        </nav>
      </header>
      <main className="container mx-auto px-4 lg:px-8 py-10">
        {children}
      </main>
    </div>
  );
};

export default Layout;