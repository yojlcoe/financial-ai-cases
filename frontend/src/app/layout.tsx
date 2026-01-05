import './globals.css';
import type { Metadata } from 'next';
import Link from 'next/link';
import {
  Building2,
  Settings,
  PlayCircle,
  FileText,
  Home,
  Newspaper
} from 'lucide-react';

export const metadata: Metadata = {
  title: '事例調査AIエージェント',
  description: '金融機関のAI・DX事例を自動収集・分析',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="bg-gray-50">
        <div className="flex min-h-screen">
          {/* Sidebar */}
          <aside className="w-64 bg-gray-900 text-white">
            <div className="p-4">
              <h1 className="text-xl font-bold">事例調査Agent</h1>
              <p className="text-gray-400 text-sm mt-1">AI Case Study Research</p>
            </div>
            <nav className="mt-6">
              <NavLink href="/" icon={<Home size={20} />}>
                ダッシュボード
              </NavLink>
              <NavLink href="/companies" icon={<Building2 size={20} />}>
                企業管理
              </NavLink>
              <NavLink href="/settings" icon={<Settings size={20} />}>
                設定
              </NavLink>
              <NavLink href="/jobs" icon={<PlayCircle size={20} />}>
                実行管理
              </NavLink>
              <NavLink href="/articles" icon={<Newspaper size={20} />}>
                収集記事
              </NavLink>
              <NavLink href="/reports" icon={<FileText size={20} />}>
                レポート
              </NavLink>
            </nav>
          </aside>

          {/* Main Content */}
          <main className="flex-1 p-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

function NavLink({ 
  href, 
  icon, 
  children 
}: { 
  href: string; 
  icon: React.ReactNode; 
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}
