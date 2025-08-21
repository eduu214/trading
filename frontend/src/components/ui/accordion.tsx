/**
 * Accordion UI Component
 * Basic accordion component for the AlphaStrat UI system
 */

import React, { createContext, useContext, useState } from 'react';

interface AccordionContextValue {
  value?: string | string[];
  onValueChange?: (value: string | string[]) => void;
  type: 'single' | 'multiple';
  collapsible?: boolean;
}

const AccordionContext = createContext<AccordionContextValue | undefined>(undefined);

interface AccordionProps {
  type: 'single' | 'multiple';
  value?: string | string[];
  defaultValue?: string | string[];
  onValueChange?: (value: string | string[]) => void;
  collapsible?: boolean;
  children: React.ReactNode;
  className?: string;
}

interface AccordionItemProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

interface AccordionTriggerProps {
  children: React.ReactNode;
  className?: string;
}

interface AccordionContentProps {
  children: React.ReactNode;
  className?: string;
}

const Accordion: React.FC<AccordionProps> = ({
  type,
  value,
  defaultValue,
  onValueChange,
  collapsible = false,
  children,
  className
}) => {
  const [internalValue, setInternalValue] = useState<string | string[]>(
    defaultValue || (type === 'multiple' ? [] : '')
  );
  
  const currentValue = value !== undefined ? value : internalValue;
  
  const handleValueChange = (newValue: string | string[]) => {
    if (value === undefined) {
      setInternalValue(newValue);
    }
    onValueChange?.(newValue);
  };

  return (
    <AccordionContext.Provider value={{
      value: currentValue,
      onValueChange: handleValueChange,
      type,
      collapsible
    }}>
      <div className={`divide-y divide-gray-200 ${className || ''}`}>
        {children}
      </div>
    </AccordionContext.Provider>
  );
};

const AccordionItem: React.FC<AccordionItemProps> = ({ value, children, className }) => {
  const context = useContext(AccordionContext);
  if (!context) {
    throw new Error('AccordionItem must be used within Accordion');
  }

  const isOpen = context.type === 'multiple' 
    ? Array.isArray(context.value) && context.value.includes(value)
    : context.value === value;

  const ItemContext = createContext({ value, isOpen });

  return (
    <ItemContext.Provider value={{ value, isOpen }}>
      <div className={className}>
        {children}
      </div>
    </ItemContext.Provider>
  );
};

const AccordionTrigger: React.FC<AccordionTriggerProps> = ({ children, className }) => {
  const context = useContext(AccordionContext);
  
  if (!context) {
    throw new Error('AccordionTrigger must be used within Accordion');
  }

  const handleClick = () => {
    // For now, implement a simple open/close for a single item
    // In a real implementation, you'd need proper item context
    console.log('Accordion trigger clicked');
  };

  return (
    <button
      className={`flex w-full items-center justify-between py-4 font-medium transition-all hover:underline ${className || ''}`}
      onClick={handleClick}
    >
      {children}
      <svg
        className="h-4 w-4 shrink-0 transition-transform duration-200"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  );
};

const AccordionContent: React.FC<AccordionContentProps> = ({ children, className }) => {
  // For now, always show content - in a real implementation you'd track open state
  return (
    <div className={`pb-4 pt-0 ${className || ''}`}>
      {children}
    </div>
  );
};

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent };