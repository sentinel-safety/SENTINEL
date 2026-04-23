// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import type { InputHTMLAttributes } from "react";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function TextInput({ label, error, id, className = "", ...rest }: Props) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={inputId} className="text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={inputId}
        {...rest}
        className={`rounded border border-slate-300 bg-white px-3 py-2 text-sm focus:border-slate-500 focus:outline-none ${className}`}
      />
      {error ? <span className="text-xs text-red-600">{error}</span> : null}
    </div>
  );
}
