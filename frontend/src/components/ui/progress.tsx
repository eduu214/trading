/**
 * Progress UI Component
 * Basic progress component for the AlphaStrat UI system
 */

import React from 'react';

interface ProgressProps {
  value?: number;
  max?: number;
  className?: string;
}

const Progress: React.FC<ProgressProps> = ({ 
  value = 0, 
  max = 100, 
  className 
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={`relative overflow-hidden rounded-full bg-gray-200 ${className || ''}`}>
      <div 
        className="h-full bg-blue-600 transition-all duration-300 ease-in-out"
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};

export { Progress };