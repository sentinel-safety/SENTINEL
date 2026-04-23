// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


export function ErrorBanner({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
      {message}
    </div>
  );
}
