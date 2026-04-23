// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { apiFetch, ApiError } from "@/lib/api-client";
import { downloadBlob } from "@/lib/download";
import { Button } from "./button";
import { ErrorBanner } from "./error-banner";
import { TextInput } from "./text-input";

const CATEGORIES = ["audit_log", "suspicion_profiles"] as const;
type Category = (typeof CATEGORIES)[number];

const schema = z
  .object({
    from: z.string().min(1, "From is required"),
    to: z.string().min(1, "To is required"),
    audit_log: z.boolean(),
    suspicion_profiles: z.boolean(),
  })
  .refine((v) => v.audit_log || v.suspicion_profiles, {
    message: "Select at least one category",
    path: ["audit_log"],
  });

type FormValues = z.infer<typeof schema>;

export function ComplianceForm() {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { from: "", to: "", audit_log: false, suspicion_profiles: false },
  });

  async function onSubmit(v: FormValues) {
    setSubmitError(null);
    setBusy(true);
    try {
      const categories: Category[] = [];
      if (v.audit_log) categories.push("audit_log");
      if (v.suspicion_profiles) categories.push("suspicion_profiles");
      const blob = await apiFetch<Blob>("/dashboard/api/compliance/export", {
        method: "POST",
        body: JSON.stringify({
          from: new Date(v.from).toISOString(),
          to: new Date(v.to).toISOString(),
          categories,
          format: "zip",
        }),
        asBlob: true,
      });
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      downloadBlob(`compliance-export-${stamp}.zip`, blob);
    } catch (e) {
      if (e instanceof ApiError) {
        setSubmitError(`Export failed (${e.status}): ${e.bodyText}`);
      } else {
        setSubmitError("Export failed");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex max-w-xl flex-col gap-4">
      {submitError ? <ErrorBanner message={submitError} /> : null}
      <div className="grid grid-cols-2 gap-3">
        <TextInput label="From" type="datetime-local" {...register("from")} error={errors.from?.message} />
        <TextInput label="To" type="datetime-local" {...register("to")} error={errors.to?.message} />
      </div>
      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm font-medium text-slate-700">Categories</legend>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" {...register("audit_log")} />
          Audit log
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" {...register("suspicion_profiles")} />
          Suspicion profiles
        </label>
        {errors.audit_log ? <span className="text-xs text-red-600">{errors.audit_log.message}</span> : null}
      </fieldset>
      <div>
        <Button type="submit" disabled={busy}>
          {busy ? "Exporting…" : "Export ZIP"}
        </Button>
      </div>
    </form>
  );
}
