import { NextRequest, NextResponse } from "next/server";

const API_TARGET = process.env.API_PROXY_TARGET || "http://localhost:8000";
const BASIC_AUTH_USERNAME = process.env.API_BASIC_AUTH_USERNAME;
const BASIC_AUTH_PASSWORD = process.env.API_BASIC_AUTH_PASSWORD;

function buildAuthHeader(): string {
  if (!BASIC_AUTH_USERNAME || !BASIC_AUTH_PASSWORD) {
    throw new Error("Missing API basic auth environment variables");
  }
  const token = Buffer.from(
    `${BASIC_AUTH_USERNAME}:${BASIC_AUTH_PASSWORD}`,
  ).toString("base64");
  return `Basic ${token}`;
}

async function proxy(request: NextRequest, path: string[]) {
  const targetUrl = new URL(`${API_TARGET}/api/v1/${path.join("/")}`);
  targetUrl.search = new URL(request.url).search;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");
  headers.delete("connection");
  headers.delete("cookie");
  headers.set("Authorization", buildAuthHeader());

  const method = request.method.toUpperCase();
  const body =
    method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();

  const response = await fetch(targetUrl.toString(), {
    method,
    headers,
    body,
  });

  const responseBody = await response.arrayBuffer();
  const responseHeaders = new Headers(response.headers);
  responseHeaders.delete("content-encoding");

  return new NextResponse(responseBody, {
    status: response.status,
    headers: responseHeaders,
  });
}

export async function GET(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxy(request, context.params.path);
}

export async function POST(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxy(request, context.params.path);
}

export async function PUT(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxy(request, context.params.path);
}

export async function PATCH(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxy(request, context.params.path);
}

export async function DELETE(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxy(request, context.params.path);
}
