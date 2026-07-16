import React from "react";
import clsx from "clsx";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, type = "text", ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            {label}
          </label>
        )}
        <input
          type={type}
          className={clsx(
            "w-full px-4 py-2.5 bg-slate-900/60 border rounded-lg text-slate-100 placeholder-slate-500 transition-all duration-200 focus:outline-none focus:ring-2 focus:border-brand-500 focus:ring-brand-500/20",
            error ? "border-red-500 focus:border-red-500 focus:ring-red-500/20" : "border-slate-700",
            className
          )}
          ref={ref}
          {...props}
        />
        {error && <span className="block mt-1 text-xs text-red-500">{error}</span>}
      </div>
    );
  }
);
Input.displayName = "Input";
export default Input;
