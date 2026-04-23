// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { readSession } from "@/lib/storage";

export default function RootPage() {
  const router = useRouter();
  useEffect(() => {
    const s = readSession();
    router.replace(s ? "/alerts" : "/login");
  }, [router]);
  return null;
}
