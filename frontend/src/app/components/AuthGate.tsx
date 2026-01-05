"use client";

import { useEffect, useState } from "react";

type AuthGateProps = {
  children: React.ReactNode;
};

const STORAGE_KEY = "basic_auth_token";

export default function AuthGate({ children }: AuthGateProps) {
  const [ready, setReady] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = window.localStorage.getItem(STORAGE_KEY);
    setAuthed(Boolean(token));
    setReady(true);
  }, []);

  const onSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!username || !password) {
      setError("ユーザー名とパスワードを入力してください。");
      return;
    }
    const token = btoa(`${username}:${password}`);
    window.localStorage.setItem(STORAGE_KEY, token);
    setAuthed(true);
    setError("");
  };

  const onLogout = () => {
    window.localStorage.removeItem(STORAGE_KEY);
    setAuthed(false);
    setUsername("");
    setPassword("");
  };

  if (!ready) {
    return null;
  }

  if (!authed) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
        <div className="w-full max-w-sm rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h1 className="text-xl font-semibold text-gray-900">ログイン</h1>
          <p className="mt-1 text-sm text-gray-500">
            ユーザー名とパスワードを入力してください。
          </p>
          <form className="mt-6 space-y-4" onSubmit={onSubmit}>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                ユーザー名
              </label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                パスワード
              </label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
            {error ? (
              <p className="text-sm text-red-600">{error}</p>
            ) : null}
            <button
              type="submit"
              className="w-full rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
            >
              ログイン
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <>
      <button
        type="button"
        onClick={onLogout}
        className="fixed right-6 top-6 z-50 rounded-md bg-gray-900 px-3 py-2 text-xs font-medium text-white hover:bg-gray-800"
      >
        ログアウト
      </button>
      {children}
    </>
  );
}
