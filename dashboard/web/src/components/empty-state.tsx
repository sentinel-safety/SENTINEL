// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


export function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}
