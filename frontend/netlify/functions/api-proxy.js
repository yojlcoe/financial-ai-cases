const API_TARGET = process.env.API_PROXY_TARGET || "http://localhost:8000";
const BASIC_AUTH_USERNAME = process.env.API_BASIC_AUTH_USERNAME;
const BASIC_AUTH_PASSWORD = process.env.API_BASIC_AUTH_PASSWORD;

function buildAuthHeader() {
  if (!BASIC_AUTH_USERNAME || !BASIC_AUTH_PASSWORD) {
    throw new Error("Missing API basic auth environment variables");
  }
  const token = Buffer.from(
    `${BASIC_AUTH_USERNAME}:${BASIC_AUTH_PASSWORD}`,
  ).toString("base64");
  return `Basic ${token}`;
}

function stripFunctionPrefix(pathname) {
  return pathname.replace(/^\/\.netlify\/functions\/api-proxy\/?/, "");
}

async function handler(event) {
  try {
    const url = new URL(event.rawUrl);
    const splat = stripFunctionPrefix(event.path || "");
    const targetUrl = `${API_TARGET}/api/v1/${splat}${url.search}`;

    const headers = {
      "Content-Type": event.headers["content-type"] || "application/json",
      Accept: event.headers.accept || "application/json",
      Authorization: buildAuthHeader(),
    };

    const method = event.httpMethod || "GET";
    const body =
      method === "GET" || method === "HEAD"
        ? undefined
        : event.isBase64Encoded
          ? Buffer.from(event.body || "", "base64")
          : event.body;

    const response = await fetch(targetUrl, {
      method,
      headers,
      body,
    });

    const responseBody = await response.text();
    return {
      statusCode: response.status,
      headers: {
        "content-type": response.headers.get("content-type") || "application/json",
      },
      body: responseBody,
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ detail: error.message || "Proxy error" }),
    };
  }
}

module.exports = { handler };
