'use client';

import { useEffect, useState } from 'react';
import { Building2, FileText, PlayCircle, Clock, LineChart } from 'lucide-react';
import { getCompanies, getJobs, getArticles, getArticleAnalysisStats, getArticleAnalysisCoefficients } from '@/lib/api';
import { formatDate } from '@/utils/datetime';
import { ArticleAnalysisCoefficients } from '@/types';

export default function Dashboard() {
  const [stats, setStats] = useState({
    companies: 0,
    articles: 0,
    jobs: 0,
    lastRun: null as string | null,
    analysisCoefficient: 0,
  });
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState<ArticleAnalysisCoefficients | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const [companiesRes, articlesRes, jobsRes, analysisRes, coefficientsRes] = await Promise.all([
          getCompanies(),
          getArticles(),
          getJobs(),
          getArticleAnalysisStats(),
          getArticleAnalysisCoefficients(),
        ]);

        const lastJob = jobsRes.items[0];

        setStats({
          companies: companiesRes.total,
          articles: articlesRes.total,
          jobs: jobsRes.total,
          lastRun: lastJob?.started_at || null,
          analysisCoefficient: analysisRes.coefficient,
        });
        setAnalysis(coefficientsRes);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, []);

  if (loading) {
    return <div className="text-center py-10">読み込み中...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            ダッシュボード
          </h1>
          <p className="text-gray-600 mt-1">金融AI事例調査システムの概要</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <StatCard
          icon={<Building2 size={24} />}
          label="登録企業数"
          value={stats.companies}
          color="blue"
        />
        <StatCard
          icon={<FileText size={24} />}
          label="収集記事数"
          value={stats.articles}
          color="green"
        />
        <StatCard
          icon={<PlayCircle size={24} />}
          label="実行回数"
          value={stats.jobs}
          color="purple"
        />
        <StatCard
          icon={<Clock size={24} />}
          label="最終実行"
          value={stats.lastRun ? formatDate(stats.lastRun) : '-'}
          color="orange"
        />
      </div>

      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl shadow-md p-6 border border-blue-100">
        <h2 className="text-xl font-bold mb-4 text-gray-800">クイックスタート</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <QuickStartCard number={1} text="「企業管理」で調査対象の企業を登録" />
          <QuickStartCard number={2} text="「設定」で検索期間を設定" />
          <QuickStartCard number={3} text="「実行管理」でジョブを開始" />
          <QuickStartCard number={4} text="「収集記事」で結果を確認" />
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
        <h2 className="text-xl font-bold mb-6 text-gray-800">分析データ（記事数）</h2>
        {analysis ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <BarChartCard title="カテゴリ別" items={analysis.by_category} />
            <BarChartCard title="業務領域別" items={analysis.by_business_area} />
            <BarChartCard title="地域別" items={analysis.by_region} />
            <LineChartCard
              title="時系列推移（月別）"
              items={analysis.by_month.map((item) => ({
                label: item.period,
                count: item.count,
              }))}
            />
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">分析データがありません</div>
        )}
      </div>
    </div>
  );
}

function QuickStartCard({ number, text }: { number: number; text: string }) {
  return (
    <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
          {number}
        </div>
        <p className="text-sm text-gray-700 leading-relaxed">{text}</p>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'emerald';
}) {
  const colorClasses = {
    blue: 'bg-blue-500 text-white',
    green: 'bg-green-500 text-white',
    purple: 'bg-purple-500 text-white',
    orange: 'bg-orange-500 text-white',
    emerald: 'bg-emerald-500 text-white',
  };

  const gradientClasses = {
    blue: 'from-blue-50 to-blue-100',
    green: 'from-green-50 to-green-100',
    purple: 'from-purple-50 to-purple-100',
    orange: 'from-orange-50 to-orange-100',
    emerald: 'from-emerald-50 to-emerald-100',
  };

  return (
    <div className={`bg-gradient-to-br ${gradientClasses[color]} rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-all hover:-translate-y-1`}>
      <div className="flex items-center gap-4">
        <div className={`p-3 ${colorClasses[color]} rounded-lg shadow-md`}>{icon}</div>
        <div>
          <p className="text-gray-600 text-sm font-medium">{label}</p>
          <p className="text-3xl font-bold text-gray-800 mt-1">{value}</p>
        </div>
      </div>
    </div>
  );
}

function BarChartCard({
  title,
  items,
}: {
  title: string;
  items: { label: string; count: number }[];
}) {
  const trimmedItems = items.slice(0, 8);
  const maxValue = Math.max(...trimmedItems.map((item) => item.count), 1);
  return (
    <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
      <h3 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
        <div className="w-1 h-5 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full" />
        {title}
      </h3>
      {trimmedItems.length === 0 ? (
        <div className="text-sm text-gray-500 text-center py-4">データなし</div>
      ) : (
        <div className="space-y-3 text-sm">
          {trimmedItems.map((item) => (
            <div key={item.label} className="group">
              <div className="flex justify-between text-gray-600 mb-1.5">
                <span className="truncate font-medium">{item.label}</span>
                <span className="font-bold text-gray-800 ml-2">{item.count}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-emerald-400 to-emerald-600 h-2.5 rounded-full transition-all duration-500 group-hover:from-emerald-500 group-hover:to-emerald-700"
                  style={{ width: `${(item.count / maxValue) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function LineChartCard({
  title,
  items,
}: {
  title: string;
  items: { label: string; count: number }[];
}) {
  if (items.length === 0) {
    return (
      <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
          <div className="w-1 h-5 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full" />
          {title}
        </h3>
        <div className="text-sm text-gray-500 text-center py-4">データなし</div>
      </div>
    );
  }

  const maxValue = Math.max(...items.map((item) => item.count), 1);
  const chartWidth = 320;
  const chartHeight = 140;
  const padding = 20;
  const step = items.length > 1 ? (chartWidth - padding * 2) / (items.length - 1) : 0;

  const points = items
    .map((item, index) => {
      const x = padding + step * index;
      const y = padding + (1 - item.count / maxValue) * (chartHeight - padding * 2);
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
      <h3 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
        <div className="w-1 h-5 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full" />
        {title}
      </h3>
      <svg
        width="100%"
        height={chartHeight}
        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
        className="mb-4"
      >
        <defs>
          <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>
        </defs>
        <polyline
          fill="none"
          stroke="url(#lineGradient)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />
        {items.map((item, index) => {
          const x = padding + step * index;
          const y = padding + (1 - item.count / maxValue) * (chartHeight - padding * 2);
          return (
            <g key={item.label}>
              <circle cx={x} cy={y} r="4" fill="white" stroke="#3b82f6" strokeWidth="2" />
              <circle cx={x} cy={y} r="2" fill="#3b82f6" />
            </g>
          );
        })}
      </svg>
      <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 max-h-32 overflow-y-auto">
        {items.map((item) => (
          <div key={item.label} className="flex justify-between py-1">
            <span className="truncate font-medium">{item.label}</span>
            <span className="font-bold text-gray-800 ml-2">{item.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
