// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import type { SelectHTMLAttributes, ReactNode } from "react";

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  children: ReactNode;
}

export function SelectInput({ label, id, className = "", children, ...rest }: Props) {
  const selectId = id ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={selectId} className="text-sm font-medium text-slate-700">
        {label}
      </label>
      <select
        id={selectId}
        {...rest}
        className={`rounded border border-slate-300 bg-white px-3 py-2 text-sm focus:border-slate-500 focus:outline-none ${className}`}
      >
        {children}
      </select>
    </div>
  );
}
