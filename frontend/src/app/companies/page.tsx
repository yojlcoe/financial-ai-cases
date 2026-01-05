'use client';

import { useEffect, useState } from 'react';
import { Plus, Trash2, ExternalLink, X, Edit } from 'lucide-react';
import {
  getCompanies,
  createCompany,
  deleteCompany,
  updateCompany,
  addSourceUrl,
  updateSourceUrl,
  deleteSourceUrl
} from '@/lib/api';
import { Company } from '@/types';

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showUrlModal, setShowUrlModal] = useState<number | null>(null);
  const [editingUrl, setEditingUrl] = useState<{ companyId: number; url: any } | null>(null);

  const fetchCompanies = async () => {
    try {
      const res = await getCompanies();
      setCompanies(res.items);
    } catch (error) {
      console.error('Failed to fetch companies:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompanies();
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm('この企業を削除しますか？')) return;
    try {
      await deleteCompany(id);
      fetchCompanies();
    } catch (error) {
      console.error('Failed to delete company:', error);
    }
  };

  const handleDeleteUrl = async (companyId: number, urlId: number) => {
    try {
      await deleteSourceUrl(companyId, urlId);
      fetchCompanies();
    } catch (error) {
      console.error('Failed to delete URL:', error);
    }
  };

  const handleToggleActive = async (company: Company) => {
    try {
      await updateCompany(company.id, { is_active: !company.is_active });
      fetchCompanies();
    } catch (error) {
      console.error('Failed to update company status:', error);
    }
  };

  if (loading) {
    return <div className="text-center py-10">読み込み中...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">企業管理</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus size={20} />
          企業を追加
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">企業名</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">英語名</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">国</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">対象URL</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">ステータス</th>
              <th className="px-6 py-3 text-right text-sm font-medium text-gray-500">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {companies.map((company) => (
              <tr key={company.id}>
                <td className="px-6 py-4 font-medium">{company.name}</td>
                <td className="px-6 py-4 text-gray-500">{company.name_en || '-'}</td>
                <td className="px-6 py-4 text-gray-500">{company.country || '-'}</td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1">
                    {company.source_urls.map((url) => (
                      <span
                        key={url.id}
                        className="inline-flex items-center gap-1 bg-gray-100 text-xs px-2 py-1 rounded"
                      >
                        <a href={url.url} target="_blank" rel="noopener noreferrer">
                          <ExternalLink size={12} />
                        </a>
                        <button
                          onClick={() => setEditingUrl({ companyId: company.id, url })}
                          className="text-blue-500 hover:text-blue-700"
                        >
                          <Edit size={12} />
                        </button>
                        <button
                          onClick={() => handleDeleteUrl(company.id, url.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <X size={12} />
                        </button>
                      </span>
                    ))}
                    <button
                      onClick={() => setShowUrlModal(company.id)}
                      className="text-blue-600 text-xs hover:underline"
                    >
                      + URL追加
                    </button>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => handleToggleActive(company)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      company.is_active
                        ? 'bg-green-100 text-green-700 hover:bg-green-200'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {company.is_active ? '✓ 有効' : '✕ 無効'}
                  </button>
                </td>
                <td className="px-6 py-4 text-right">
                  <button
                    onClick={() => handleToggleActive(company)}
                    className={`text-sm px-3 py-1.5 rounded-lg border transition-all mr-3 ${
                      company.is_active
                        ? 'border-orange-300 text-orange-700 hover:bg-orange-50'
                        : 'border-green-300 text-green-700 hover:bg-green-50'
                    }`}
                  >
                    {company.is_active ? '無効化' : '有効化'}
                  </button>
                  <button
                    onClick={() => handleDelete(company.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 size={18} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 企業追加モーダル */}
      {showModal && (
        <CompanyModal
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false);
            fetchCompanies();
          }}
        />
      )}

      {/* URL追加モーダル */}
      {showUrlModal && (
        <UrlModal
          companyId={showUrlModal}
          onClose={() => setShowUrlModal(null)}
          onSuccess={() => {
            setShowUrlModal(null);
            fetchCompanies();
          }}
        />
      )}

      {/* URL編集モーダル */}
      {editingUrl && (
        <UrlEditModal
          companyId={editingUrl.companyId}
          url={editingUrl.url}
          onClose={() => setEditingUrl(null)}
          onSuccess={() => {
            setEditingUrl(null);
            fetchCompanies();
          }}
        />
      )}
    </div>
  );
}

function CompanyModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    name: '',
    name_en: '',
    country: '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createCompany(formData);
      onSuccess();
    } catch (error) {
      console.error('Failed to create company:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">企業を追加</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">企業名 *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full border rounded-lg px-3 py-2"
              placeholder="三井住友銀行"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">英語名</label>
            <input
              type="text"
              value={formData.name_en}
              onChange={(e) => setFormData({ ...formData, name_en: e.target.value })}
              className="w-full border rounded-lg px-3 py-2"
              placeholder="Sumitomo Mitsui Banking Corporation"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">国</label>
            <input
              type="text"
              value={formData.country}
              onChange={(e) => setFormData({ ...formData, country: e.target.value })}
              className="w-full border rounded-lg px-3 py-2"
              placeholder="日本"
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '保存中...' : '保存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function UrlModal({
  companyId,
  onClose,
  onSuccess,
}: {
  companyId: number;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [url, setUrl] = useState('');
  const [urlType, setUrlType] = useState('press_release');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await addSourceUrl(companyId, { url, url_type: urlType });
      onSuccess();
    } catch (error) {
      console.error('Failed to add URL:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">URLを追加</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">URL *</label>
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
              placeholder="https://www.example.com/news/"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">種類</label>
            <select
              value={urlType}
              onChange={(e) => setUrlType(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
            >
              <option value="press_release">プレスリリース</option>
              <option value="news">ニュース</option>
              <option value="blog">ブログ</option>
              <option value="duckduckgo">DuckDuckGo検索</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '追加中...' : '追加'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function UrlEditModal({
  companyId,
  url: initialUrl,
  onClose,
  onSuccess,
}: {
  companyId: number;
  url: any;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [url, setUrl] = useState(initialUrl.url);
  const [urlType, setUrlType] = useState(initialUrl.url_type);
  const [isActive, setIsActive] = useState(initialUrl.is_active);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await updateSourceUrl(companyId, initialUrl.id, {
        url,
        url_type: urlType,
        is_active: isActive,
      });
      onSuccess();
    } catch (error) {
      console.error('Failed to update URL:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">URLを編集</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">URL *</label>
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
              placeholder="https://www.example.com/news/"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">種類</label>
            <select
              value={urlType}
              onChange={(e) => setUrlType(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
            >
              <option value="press_release">プレスリリース</option>
              <option value="news">ニュース</option>
              <option value="blog">ブログ</option>
              <option value="duckduckgo">DuckDuckGo検索</option>
            </select>
          </div>
          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm font-medium">有効</span>
            </label>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '保存中...' : '保存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
