// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_BFF_BASE_URL: process.env.NEXT_PUBLIC_BFF_BASE_URL ?? "http://127.0.0.1:8009",
  },
};

export default config;
