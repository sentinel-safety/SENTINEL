// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { RoleGate } from "@/components/role-gate";
import { Shell } from "@/components/shell";
import { ActionConfigSection } from "@/components/settings/action-config-section";
import { ApiKeysSection } from "@/components/settings/api-keys-section";
import { GeneralSection } from "@/components/settings/general-section";
import { WebhooksSection } from "@/components/settings/webhooks-section";

export default function SettingsPage() {
  return (
    <Shell>
      <h1 className="mb-4 text-xl font-semibold">Tenant settings</h1>
      <RoleGate
        allow={["admin"]}
        fallback={<div className="text-sm text-slate-600">Only admins may view tenant settings.</div>}
      >
        <div className="flex flex-col gap-10">
          <section>
            <h2 className="mb-3 text-base font-semibold text-slate-800">General</h2>
            <GeneralSection />
          </section>
          <section>
            <h2 className="mb-3 text-base font-semibold text-slate-800">Action configuration</h2>
            <ActionConfigSection />
          </section>
          <section>
            <h2 className="mb-3 text-base font-semibold text-slate-800">Webhooks</h2>
            <WebhooksSection />
          </section>
          <section>
            <h2 className="mb-3 text-base font-semibold text-slate-800">API keys</h2>
            <ApiKeysSection />
          </section>
        </div>
      </RoleGate>
    </Shell>
  );
}
