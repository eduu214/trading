/**
 * Slider UI Component
 * Basic slider component for the AlphaStrat UI system
 */

import React from 'react';

interface SliderProps {
  value?: number[];
  defaultValue?: number[];
  min?: number;
  max?: number;
  step?: number;
  onValueChange?: (value: number[]) => void;
  className?: string;
}

const Slider: React.FC<SliderProps> = ({
  value,
  defaultValue = [0],
  min = 0,
  max = 100,
  step = 1,
  onValueChange,
  className
}) => {
  const [internalValue, setInternalValue] = React.useState(defaultValue);
  const currentValue = value !== undefined ? value : internalValue;
  
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = [Number(event.target.value)];
    if (value === undefined) {
      setInternalValue(newValue);
    }
    onValueChange?.(newValue);
  };

  const percentage = ((currentValue[0] - min) / (max - min)) * 100;

  return (
    <div className={`relative flex items-center select-none touch-none ${className || ''}`}>
      <div className="relative flex-1 h-2">
        {/* Track */}
        <div className="absolute inset-0 bg-gray-200 rounded-full"></div>
        
        {/* Filled portion */}
        <div 
          className="absolute left-0 top-0 h-full bg-blue-600 rounded-full"
          style={{ width: `${percentage}%` }}
        ></div>
        
        {/* Slider input */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={currentValue[0]}
          onChange={handleChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        
        {/* Thumb */}
        <div 
          className="absolute top-1/2 w-5 h-5 bg-white border-2 border-blue-600 rounded-full shadow-sm transform -translate-y-1/2 -translate-x-1/2"
          style={{ left: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};

export { Slider };