/**
 * Alert UI Component
 * Basic alert component for the AlphaStrat UI system
 */

import React from 'react';

interface AlertProps {
  variant?: 'default' | 'destructive' | 'warning' | 'success';
  children: React.ReactNode;
  className?: string;
}

interface AlertDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

interface AlertTitleProps {
  children: React.ReactNode;
  className?: string;
}

const Alert: React.FC<AlertProps> = ({ 
  variant = 'default', 
  children, 
  className 
}) => {
  const variantClasses = {
    default: 'bg-blue-50 border-blue-200 text-blue-800',
    destructive: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    success: 'bg-green-50 border-green-200 text-green-800'
  };

  return (
    <div className={`relative w-full rounded-lg border p-4 ${variantClasses[variant]} ${className || ''}`}>
      {children}
    </div>
  );
};

const AlertTitle: React.FC<AlertTitleProps> = ({ 
  children, 
  className 
}) => {
  return (
    <h5 className={`mb-1 font-medium leading-none tracking-tight ${className || ''}`}>
      {children}
    </h5>
  );
};

const AlertDescription: React.FC<AlertDescriptionProps> = ({ 
  children, 
  className 
}) => {
  return (
    <div className={`text-sm ${className || ''}`}>
      {children}
    </div>
  );
};

export { Alert, AlertTitle, AlertDescription };