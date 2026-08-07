import React from 'react';

interface Step {
  id: string;
  title: string;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
  onStepClick?: (stepIndex: number) => void;
}

const Stepper: React.FC<StepperProps> = ({ steps, currentStep, onStepClick }) => {
  return (
    <div className="mb-4">
      <div className="flex justify-between relative">
        {/* Progress line background */}
        <div className="absolute top-4 left-0 right-0 h-1 bg-gray-200 -z-10 rounded-full"></div>
        {/* Progress line fill */}
        <div 
          className="absolute top-4 left-0 h-1 bg-blue-500 -z-10 rounded-full transition-all duration-500 ease-in-out"
          style={{ 
            width: `${steps.length > 1 ? ((currentStep) / (steps.length - 1)) * 100 : 0}%`,
            maxWidth: '100%'
          }}
        ></div>
        
        {steps.map((step, index) => (
          <div
            key={step.id}
            onClick={() => onStepClick && onStepClick(index)}
            className="flex flex-col items-center relative cursor-pointer group hover:scale-105 transition-transform"
            title={`Jump to Step ${index + 1}: ${step.title}`}
          >
            <div 
              className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 text-xs transition-all duration-300 ${
                index < currentStep
                  ? 'bg-green-500 text-white border-0 hover:bg-green-600'
                  : index === currentStep
                  ? 'bg-blue-600 text-white border-2 border-blue-200'
                  : 'bg-white text-gray-400 border-2 border-gray-300 group-hover:border-blue-400 group-hover:text-blue-600'
              }`}
              style={{
                boxShadow: index === currentStep ? '0 0 0 3px rgba(59, 130, 246, 0.25)' : 'none'
              }}
            >
              {index < currentStep ? (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <span className="font-bold">{index + 1}</span>
              )}
            </div>
            <span 
              className={`text-[11px] font-medium text-center leading-tight w-20 transition-colors duration-300 ${
                index === currentStep ? 'text-blue-600 font-bold' : 'text-slate-500 group-hover:text-blue-600'
              }`}
            >
              {step.title}
            </span>
          </div>
        ))}
      </div>
      
      {/* Progress text */}
      <div className="text-center mt-2 text-[11px] font-semibold text-slate-400">
        Step {currentStep + 1} of {steps.length}
      </div>
    </div>
  );
};

export default Stepper;