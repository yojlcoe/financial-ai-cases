'use client';

import { useEffect, useState } from 'react';
import { PlayCircle, RefreshCw } from 'lucide-react';
import { getJobs, startJob } from '@/lib/api';
import { JobHistory } from '@/types';
import { formatDateTime } from '@/utils/datetime';

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  const fetchJobs = async () => {
    try {
      const res = await getJobs();
      setJobs(res.items);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    // 10秒ごとに更新
    const interval = setInterval(fetchJobs, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleStartJob = async () => {
    if (!confirm('調査ジョブを開始しますか？')) return;
    setStarting(true);
    try {
      await startJob('manual');
      fetchJobs();
    } catch (error) {
      console.error('Failed to start job:', error);
      alert('ジョブの開始に失敗しました。設定と企業が登録されているか確認してください。');
    } finally {
      setStarting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      running: 'bg-blue-100 text-blue-700',
      completed: 'bg-green-100 text-green-700',
      failed: 'bg-red-100 text-red-700',
    };
    const labels: Record<string, string> = {
      running: '実行中',
      completed: '完了',
      failed: '失敗',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs ${styles[status] || 'bg-gray-100'}`}>
        {labels[status] || status}
      </span>
    );
  };

  if (loading) {
    return <div className="text-center py-10">読み込み中...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">実行管理</h1>
        <div className="flex gap-3">
          <button
            onClick={fetchJobs}
            className="flex items-center gap-2 border px-4 py-2 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw size={18} />
            更新
          </button>
          <button
            onClick={handleStartJob}
            disabled={starting}
            className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            <PlayCircle size={20} />
            {starting ? '開始中...' : 'ジョブを開始'}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">ID</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">種類</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">ステータス</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">進捗</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">記事数</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">開始日時</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">完了日時</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {jobs.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-10 text-center text-gray-500">
                  実行履歴がありません
                </td>
              </tr>
            ) : (
              jobs.map((job) => (
                <tr key={job.id}>
                  <td className="px-6 py-4">{job.id}</td>
                  <td className="px-6 py-4">{job.job_type}</td>
                  <td className="px-6 py-4">{getStatusBadge(job.status)}</td>
                  <td className="px-6 py-4">
                    {job.processed_companies} / {job.total_companies}
                  </td>
                  <td className="px-6 py-4">{job.total_articles}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {formatDateTime(job.started_at)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {job.completed_at ? formatDateTime(job.completed_at) : '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {jobs.some((j) => j.status === 'running') && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <p className="text-blue-700">
            ジョブが実行中です。この画面は10秒ごとに自動更新されます。
          </p>
        </div>
      )}
    </div>
  );
}
