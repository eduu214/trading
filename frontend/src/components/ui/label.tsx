/**
 * Label UI Component
 * Basic label component for the AlphaStrat UI system
 */

import React from 'react';

interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  children: React.ReactNode;
}

const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <label
        ref={ref}
        className={`text-sm font-medium text-gray-700 ${className || ''}`}
        {...props}
      >
        {children}
      </label>
    );
  }
);
Label.displayName = 'Label';

export { Label };