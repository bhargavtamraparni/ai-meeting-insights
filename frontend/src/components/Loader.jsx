import React from 'react';

const Loader = ({ small = false, simple = false }) => {
  const sizeClass = small ? 'w-4 h-4' : 'w-10 h-10';
  const borderClass = simple ? 'border-2' : 'border-4';
  // A modern spinner using a branded accent color for the moving part
  return (
    <div className={`animate-spin rounded-full ${sizeClass} ${borderClass} border-slate-300 border-t-indigo-600`}></div>
  );
};

export default Loader;
