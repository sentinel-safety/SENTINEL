// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "./button";
import { TextInput } from "./text-input";
import { ErrorBanner } from "./error-banner";
import { useAuth } from "@/lib/auth-context";
import { BFF_BASE_URL } from "@/lib/env";
import type { LoginResponse } from "@/lib/types";

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const schema = z.object({
  email: z.string().min(1, "Email is required").regex(emailRegex, "Invalid email"),
  password: z.string().min(1, "Password is required"),
});

type FormValues = z.infer<typeof schema>;

export function LoginForm() {
  const { setSession } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setError(null);
    try {
      const res = await fetch(`${BFF_BASE_URL}/dashboard/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      if (res.status === 401) {
        setError("Invalid email or password");
        return;
      }
      if (!res.ok) {
        setError(`Login failed (${res.status})`);
        return;
      }
      const data = (await res.json()) as LoginResponse;
      setSession(data);
      router.push("/alerts");
    } catch {
      setError("Network error — please try again");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
      {error ? <ErrorBanner message={error} /> : null}
      <TextInput
        label="Email"
        type="email"
        autoComplete="email"
        {...register("email")}
        error={errors.email?.message}
      />
      <TextInput
        label="Password"
        type="password"
        autoComplete="current-password"
        {...register("password")}
        error={errors.password?.message}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Signing in…" : "Sign in"}
      </Button>
    </form>
  );
}
