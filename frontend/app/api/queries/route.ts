import { NextResponse } from "next/server";

type QueryRequest = {
  query?: string;
};

function getBackendUrl() {
  // Prefer server-only env var. Fall back to NEXT_PUBLIC for compatibility.
  const baseUrl =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    "http://127.0.0.1:8000";

  return baseUrl.replace(/\/$/, "");
}

export async function POST(req: Request) {
  let payload: QueryRequest;

  try {
    payload = (await req.json()) as QueryRequest;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON" }, { status: 400 });
  }

  if (!payload?.query) {
    return NextResponse.json({ detail: "query is required" }, { status: 400 });
  }

  const backendRes = await fetch(`${getBackendUrl()}/queries`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: payload.query }),
    cache: "no-store",
  });

  const body = await backendRes.json().catch(() => ({}));
  return NextResponse.json(body, { status: backendRes.status });
}
