// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useState } from "react";
import { Button } from "./button";

interface Props {
  title: string;
  secret: string;
  onClose: () => void;
}

export function SecretOnceModal({ title, secret, onClose }: Props) {
  const [confirmed, setConfirmed] = useState(false);
  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-900/40 p-4">
      <div role="dialog" aria-modal="true" className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <h2 className="mb-2 text-lg font-semibold">{title} secret</h2>
        <p className="mb-3 text-sm text-slate-600">
          This secret will be shown <strong>only once</strong>. Copy it now — you will not be able to retrieve it later.
        </p>
        <pre className="mb-3 overflow-x-auto rounded bg-slate-100 p-3 font-mono text-sm text-slate-900">{secret}</pre>
        <label className="mb-4 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
          I have saved this secret in a safe place.
        </label>
        <div className="flex justify-end">
          <Button disabled={!confirmed} onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
