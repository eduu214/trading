/**
 * Tooltip UI Component
 * Basic tooltip component for the AlphaStrat UI system
 */

import React, { createContext, useContext, useState } from 'react';

interface TooltipContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const TooltipContext = createContext<TooltipContextValue | undefined>(undefined);

interface TooltipProviderProps {
  children: React.ReactNode;
}

interface TooltipProps {
  children: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

interface TooltipTriggerProps {
  asChild?: boolean;
  children: React.ReactNode;
}

interface TooltipContentProps {
  children: React.ReactNode;
  className?: string;
  side?: 'top' | 'right' | 'bottom' | 'left';
}

const TooltipProvider: React.FC<TooltipProviderProps> = ({ children }) => {
  return <>{children}</>;
};

const Tooltip: React.FC<TooltipProps> = ({ 
  children, 
  open, 
  onOpenChange 
}) => {
  const [internalOpen, setInternalOpen] = useState(false);
  const isOpen = open !== undefined ? open : internalOpen;
  
  const setOpen = (newOpen: boolean) => {
    if (open === undefined) {
      setInternalOpen(newOpen);
    }
    onOpenChange?.(newOpen);
  };

  return (
    <TooltipContext.Provider value={{ open: isOpen, setOpen }}>
      <div className="relative inline-block">
        {children}
      </div>
    </TooltipContext.Provider>
  );
};

const TooltipTrigger: React.FC<TooltipTriggerProps> = ({ 
  children,
  asChild = false 
}) => {
  const context = useContext(TooltipContext);
  if (!context) {
    throw new Error('TooltipTrigger must be used within Tooltip');
  }

  const handleMouseEnter = () => context.setOpen(true);
  const handleMouseLeave = () => context.setOpen(false);

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, {
      onMouseEnter: handleMouseEnter,
      onMouseLeave: handleMouseLeave,
    } as any);
  }

  return (
    <div
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
    </div>
  );
};

const TooltipContent: React.FC<TooltipContentProps> = ({ 
  children, 
  className, 
  side = 'top' 
}) => {
  const context = useContext(TooltipContext);
  if (!context || !context.open) {
    return null;
  }

  const sideClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-2',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-2'
  };

  return (
    <div className={`absolute z-50 ${sideClasses[side]}`}>
      <div className={`bg-gray-900 text-white text-xs rounded px-2 py-1 shadow-lg ${className || ''}`}>
        {children}
      </div>
    </div>
  );
};

export { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent };