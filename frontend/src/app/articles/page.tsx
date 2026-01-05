'use client';

import { useEffect, useState } from 'react';
import { ExternalLink, ChevronDown, ChevronUp, Download, Plus, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { getArticles, getCompanies, updateArticle, getPrompts, addArticleFromUrl, addArticlesFromUrls } from '@/lib/api';
import { Article, Company } from '@/types';

export default function ArticlesPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [totalArticles, setTotalArticles] = useState<number>(0);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize] = useState<number>(50);
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedBusinessArea, setSelectedBusinessArea] = useState<string>('');
  const [selectedTag, setSelectedTag] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [reviewStatus, setReviewStatus] = useState<string>('');
  const [editingArticle, setEditingArticle] = useState<Article | null>(null);
  const [editValues, setEditValues] = useState({
    title: '',
    summary: '',
    published_date: '',
    category: '',
    business_area: '',
    tags: '',
    is_inappropriate: false,
    inappropriate_reason: '',
  });
  const [savingArticle, setSavingArticle] = useState(false);
  const [expandedArticles, setExpandedArticles] = useState<Set<number>>(new Set());
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [availableBusinessAreas, setAvailableBusinessAreas] = useState<string[]>([]);
  const [showAddUrlModal, setShowAddUrlModal] = useState(false);
  const [urlCompanyPairs, setUrlCompanyPairs] = useState<Array<{ url: string; companyId: string }>>([
    { url: '', companyId: '' }
  ]);
  const [addingArticle, setAddingArticle] = useState(false);

  useEffect(() => {
    fetchData();
  }, [currentPage, selectedCompany, selectedCategory, selectedBusinessArea, selectedTag, startDate, endDate, reviewStatus]);

  const fetchData = async () => {
    try {
      setLoading(true);

      // クエリパラメータを構築
      const params: Record<string, string> = {
        skip: ((currentPage - 1) * pageSize).toString(),
        limit: pageSize.toString(),
      };

      if (selectedCompany) {
        params.company_id = selectedCompany;
      }
      if (selectedCategory) {
        params.category = selectedCategory;
      }
      if (selectedBusinessArea) {
        params.business_area = selectedBusinessArea;
      }
      if (selectedTag) {
        params.tags = selectedTag;
      }
      if (startDate) {
        params.start_date = startDate;
      }
      if (endDate) {
        params.end_date = endDate;
      }
      if (reviewStatus !== '') {
        params.is_reviewed = reviewStatus;
      }

      const [articlesRes, companiesRes, promptsRes] = await Promise.all([
        getArticles(params),
        getCompanies(),
        getPrompts(),
      ]);
      setArticles(articlesRes.items);
      setTotalArticles(articlesRes.total);
      setCompanies(companiesRes.items);
      setAvailableCategories(promptsRes.classifier.categories);
      setAvailableBusinessAreas(promptsRes.classifier.business_areas);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  // バックエンドでフィルタリング済みなので、そのまま表示
  const filteredArticles = articles;

  // カテゴリとビジネス領域の選択肢は、プロンプト設定から取得
  const categories = availableCategories;
  const businessAreas = availableBusinessAreas;

  // タグの選択肢は現在のページの記事から取得（全体から取得するにはAPIの追加が必要）
  const allTags = Array.from(
    new Set(
      articles
        .filter((a) => a.tags)
        .flatMap((a) => a.tags!.split(',').map((t) => t.trim()))
    )
  ).sort();

  const getCompanyName = (companyId: number) => {
    return companies.find((c) => c.id === companyId)?.name || '不明';
  };

  const startEdit = (article: Article) => {
    setEditingArticle(article);
    setEditValues({
      title: article.title || '',
      summary: article.summary || '',
      published_date: article.published_date || '',
      category: article.category || '',
      business_area: article.business_area || '',
      tags: article.tags || '',
      is_inappropriate: article.is_inappropriate || false,
      inappropriate_reason: article.inappropriate_reason || '',
    });
  };

  const cancelEdit = () => {
    setEditingArticle(null);
  };

  const saveEdit = async () => {
    if (!editingArticle) {
      return;
    }

    // 不適切フラグがONの場合、理由が必須
    if (editValues.is_inappropriate && !editValues.inappropriate_reason.trim()) {
      alert('不適切な理由を入力してください');
      return;
    }

    try {
      setSavingArticle(true);
      const updated = await updateArticle(editingArticle.id, {
        title: editValues.title.trim() || null,
        summary: editValues.summary.trim() || null,
        published_date: editValues.published_date.trim() || null,
        category: editValues.category.trim() || null,
        business_area: editValues.business_area.trim() || null,
        tags: editValues.tags.trim() || null,
        is_inappropriate: editValues.is_inappropriate,
        inappropriate_reason: editValues.inappropriate_reason.trim() || null,
      });

      // 不適切フラグが付けられた場合は一覧から削除、それ以外は更新
      if (editValues.is_inappropriate) {
        setArticles((prev) =>
          prev.filter((article) => article.id !== editingArticle.id)
        );
      } else {
        setArticles((prev) =>
          prev.map((article) =>
            article.id === editingArticle.id ? { ...article, ...updated } : article
          )
        );
      }
      setEditingArticle(null);
    } catch (error) {
      console.error('Failed to update article:', error);
    } finally {
      setSavingArticle(false);
    }
  };

  const toggleExpand = (articleId: number) => {
    setExpandedArticles((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(articleId)) {
        newSet.delete(articleId);
      } else {
        newSet.add(articleId);
      }
      return newSet;
    });
  };

  const toggleReviewStatus = async (article: Article) => {
    try {
      const newStatus = !article.is_reviewed;
      await updateArticle(article.id, {
        is_reviewed: newStatus,
      });

      // ローカルの状態を更新
      setArticles((prev) =>
        prev.map((a) =>
          a.id === article.id ? { ...a, is_reviewed: newStatus } : a
        )
      );
    } catch (error) {
      console.error('Failed to update review status:', error);
      alert('確認状態の更新に失敗しました');
    }
  };

  const downloadCSV = () => {
    const headers = ['ID', '企業名', 'タイトル', 'URL', '公開日', 'カテゴリ', 'ビジネス領域', 'タグ'];
    const csvContent = [
      headers.join(','),
      ...filteredArticles.map((article) => {
        const row = [
          article.id,
          `"${getCompanyName(article.company_id).replace(/"/g, '""')}"`,
          `"${(article.title || '').replace(/"/g, '""')}"`,
          `"${article.url.replace(/"/g, '""')}"`,
          article.published_date || '',
          `"${(article.category || '').replace(/"/g, '""')}"`,
          `"${(article.business_area || '').replace(/"/g, '""')}"`,
          `"${(article.tags || '').replace(/"/g, '""')}"`,
        ];
        return row.join(',');
      }),
    ].join('\n');

    const bom = '\uFEFF';
    const blob = new Blob([bom + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `articles_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const addUrlField = () => {
    setUrlCompanyPairs([...urlCompanyPairs, { url: '', companyId: '' }]);
  };

  const removeUrlField = (index: number) => {
    if (urlCompanyPairs.length === 1) return; // 最低1つは残す
    setUrlCompanyPairs(urlCompanyPairs.filter((_, i) => i !== index));
  };

  const updateUrlField = (index: number, value: string) => {
    const newPairs = [...urlCompanyPairs];
    newPairs[index].url = value;
    setUrlCompanyPairs(newPairs);
  };

  const updateCompanyField = (index: number, companyId: string) => {
    const newPairs = [...urlCompanyPairs];
    newPairs[index].companyId = companyId;
    setUrlCompanyPairs(newPairs);
  };

  const addArticles = async () => {
    // 空でないURL&企業が選択されているペアのみフィルタ
    const validPairs = urlCompanyPairs.filter(
      pair => pair.url.trim().length > 0 && pair.companyId.length > 0
    );

    if (validPairs.length === 0) {
      alert('URLと企業を選択してください');
      return;
    }

    try {
      setAddingArticle(true);

      // 各ペアを個別に処理するためのジョブを作成
      const promises = validPairs.map(pair =>
        addArticleFromUrl(pair.url.trim(), parseInt(pair.companyId))
      );

      const results = await Promise.all(promises);

      setShowAddUrlModal(false);
      setUrlCompanyPairs([{ url: '', companyId: '' }]);

      const jobIds = results.map(r => r.job_id).join(', ');
      alert(`記事追加処理を開始しました\n${validPairs.length}件のURLを処理します。\nジョブID: ${jobIds}\n実行管理ページで進捗を確認できます。`);
    } catch (error) {
      console.error('Failed to add articles:', error);
      alert('記事の追加に失敗しました');
    } finally {
      setAddingArticle(false);
    }
  };

  if (loading) {
    return <div className="text-center py-10">読み込み中...</div>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-4">収集記事一覧</h1>
        <div className="flex gap-3 flex-wrap">
          <select
            value={selectedCompany}
            onChange={(e) => {
              setSelectedCompany(e.target.value);
              setCurrentPage(1);
            }}
            className="border rounded-lg px-3 py-2"
          >
            <option value="">全企業</option>
            {companies.map((company) => (
              <option key={company.id} value={company.id}>
                {company.name}
              </option>
            ))}
          </select>
          <select
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setCurrentPage(1);
            }}
            className="border rounded-lg px-3 py-2"
          >
            <option value="">全カテゴリ</option>
            {categories.map((category) => (
              <option key={category} value={category || ''}>
                {category}
              </option>
            ))}
          </select>
          <select
            value={selectedBusinessArea}
            onChange={(e) => {
              setSelectedBusinessArea(e.target.value);
              setCurrentPage(1);
            }}
            className="border rounded-lg px-3 py-2"
          >
            <option value="">全ビジネス領域</option>
            {businessAreas.map((area) => (
              <option key={area} value={area || ''}>
                {area}
              </option>
            ))}
          </select>
          <select
            value={selectedTag}
            onChange={(e) => {
              setSelectedTag(e.target.value);
              setCurrentPage(1);
            }}
            className="border rounded-lg px-3 py-2"
          >
            <option value="">全タグ</option>
            {allTags.map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
          </select>
          <select
            value={reviewStatus}
            onChange={(e) => {
              setReviewStatus(e.target.value);
              setCurrentPage(1);
            }}
            className="border rounded-lg px-3 py-2"
          >
            <option value="">確認状態: すべて</option>
            <option value="true">確認済み</option>
            <option value="false">未確認</option>
          </select>
          <input
            type="date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setCurrentPage(1);
            }}
            className="border rounded-lg px-3 py-2"
            placeholder="開始日"
          />
          <span className="flex items-center text-gray-500">〜</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setCurrentPage(1);
            }}
            className="border rounded-lg px-3 py-2"
            placeholder="終了日"
          />
        </div>
      </div>

      <div className="flex justify-between items-center mb-4">
        <div className="text-sm text-gray-600">
          全 {totalArticles} 件中 {totalArticles > 0 ? ((currentPage - 1) * pageSize) + 1 : 0}〜{Math.min(currentPage * pageSize, totalArticles)} 件目を表示
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAddUrlModal(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
          >
            <Plus size={16} />
            URLから追加
          </button>
          <button
            onClick={downloadCSV}
            className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm"
          >
            <Download size={16} />
            CSVダウンロード
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {filteredArticles.map((article) => (
          <div
            key={article.id}
            className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <div className="flex items-start gap-3 mb-2">
                  <h2 className="text-lg font-semibold flex-1">
                    {article.title}
                  </h2>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      type="button"
                      onClick={() => toggleReviewStatus(article)}
                      className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                        article.is_reviewed
                          ? 'bg-green-50 text-green-700 border-green-300 hover:bg-green-100'
                          : 'bg-gray-50 text-gray-600 border-gray-300 hover:bg-gray-100'
                      }`}
                    >
                      {article.is_reviewed ? '✓ 確認済み' : '未確認'}
                    </button>
                    <button
                      type="button"
                      onClick={() => startEdit(article)}
                      className="text-xs text-gray-600 hover:text-gray-900 border border-gray-200 rounded px-2 py-1"
                    >
                      編集
                    </button>
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800"
                    >
                      <ExternalLink size={20} />
                    </a>
                  </div>
                </div>
                <div className="flex gap-2 text-sm text-gray-600 mb-3">
                  <span className="font-medium">
                    {getCompanyName(article.company_id)}
                  </span>
                  {article.published_date && (
                    <>
                      <span>•</span>
                      <span>{article.published_date}</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {article.summary && (
              <div className="mb-3">
                <button
                  type="button"
                  onClick={() => toggleExpand(article.id)}
                  className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-2"
                >
                  {expandedArticles.has(article.id) ? (
                    <>
                      <ChevronUp size={16} />
                      <span>サマリーを隠す</span>
                    </>
                  ) : (
                    <>
                      <ChevronDown size={16} />
                      <span>サマリーを表示</span>
                    </>
                  )}
                </button>
                {expandedArticles.has(article.id) && (
                  <div className="text-gray-700 border-l-2 border-blue-200 pl-4">
                    <ReactMarkdown
                      components={{
                        h2: ({ children }) => (
                          <h2 className="text-sm font-semibold text-gray-900 mt-3 mb-2">
                            {children}
                          </h2>
                        ),
                        p: ({ children }) => (
                          <p className="text-sm leading-relaxed mb-2">{children}</p>
                        ),
                        ul: ({ children }) => (
                          <ul className="list-disc pl-5 space-y-1 mb-2 text-sm">
                            {children}
                          </ul>
                        ),
                        li: ({ children }) => (
                          <li className="text-sm leading-relaxed">{children}</li>
                        ),
                        strong: ({ children }) => (
                          <strong className="font-semibold text-gray-900">
                            {children}
                          </strong>
                        ),
                      }}
                    >
                      {article.summary}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              {article.category && (
                <span className="inline-block bg-blue-100 text-blue-700 text-xs px-3 py-1 rounded-full">
                  {article.category}
                </span>
              )}
              {article.business_area && (
                <span className="inline-block bg-green-100 text-green-700 text-xs px-3 py-1 rounded-full">
                  {article.business_area}
                </span>
              )}
              {article.tags &&
                article.tags.split(',').map((tag, idx) => (
                  <span
                    key={idx}
                    className="inline-block bg-gray-100 text-gray-700 text-xs px-3 py-1 rounded-full"
                  >
                    {tag.trim()}
                  </span>
                ))}
            </div>
          </div>
        ))}
      </div>

      {filteredArticles.length === 0 && !loading && (
        <div className="text-center py-10 text-gray-500">
          記事が見つかりませんでした
        </div>
      )}

      {/* ページネーション */}
      {totalArticles > pageSize && (
        <div className="mt-8 space-y-3">
          <div className="text-center text-sm text-gray-600">
            ページ {currentPage} / {Math.ceil(totalArticles / pageSize)}
          </div>
          <div className="flex justify-center items-center gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              前へ
            </button>
            <div className="flex gap-1">
            {Array.from({ length: Math.ceil(totalArticles / pageSize) }, (_, i) => i + 1)
              .filter(page => {
                // 現在のページ周辺と最初・最後のページのみ表示
                return page === 1 ||
                       page === Math.ceil(totalArticles / pageSize) ||
                       Math.abs(page - currentPage) <= 2;
              })
              .map((page, idx, arr) => (
                <div key={page} className="flex items-center">
                  {idx > 0 && arr[idx - 1] !== page - 1 && (
                    <span className="px-2 text-gray-400">...</span>
                  )}
                  <button
                    onClick={() => setCurrentPage(page)}
                    className={`px-4 py-2 border rounded-lg ${
                      currentPage === page
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    {page}
                  </button>
                </div>
              ))}
          </div>
          <button
            onClick={() => setCurrentPage(Math.min(Math.ceil(totalArticles / pageSize), currentPage + 1))}
            disabled={currentPage === Math.ceil(totalArticles / pageSize)}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            次へ
          </button>
          </div>
        </div>
      )}

      {showAddUrlModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">URLから記事を追加</h2>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm text-gray-600">URL と企業</label>
                  <button
                    type="button"
                    onClick={addUrlField}
                    className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
                    disabled={addingArticle}
                  >
                    <Plus size={14} />
                    URLを追加
                  </button>
                </div>
                <div className="space-y-3">
                  {urlCompanyPairs.map((pair, index) => (
                    <div key={index} className="flex gap-2 items-start">
                      <div className="flex-1 space-y-2">
                        <input
                          type="url"
                          value={pair.url}
                          onChange={(e) => updateUrlField(index, e.target.value)}
                          className="w-full border rounded-lg px-3 py-2 text-sm"
                          placeholder="https://..."
                          disabled={addingArticle}
                        />
                        <select
                          value={pair.companyId}
                          onChange={(e) => updateCompanyField(index, e.target.value)}
                          className="w-full border rounded-lg px-3 py-2 text-sm"
                          disabled={addingArticle}
                        >
                          <option value="">企業を選択</option>
                          {companies.map((company) => (
                            <option key={company.id} value={company.id}>
                              {company.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      {urlCompanyPairs.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeUrlField(index)}
                          className="p-2 text-gray-400 hover:text-red-600 border rounded-lg hover:border-red-200 mt-1"
                          disabled={addingArticle}
                        >
                          <X size={16} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                type="button"
                onClick={() => {
                  setShowAddUrlModal(false);
                  setUrlCompanyPairs([{ url: '', companyId: '' }]);
                }}
                className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50"
                disabled={addingArticle}
              >
                キャンセル
              </button>
              <button
                type="button"
                onClick={addArticles}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60"
                disabled={addingArticle}
              >
                {addingArticle ? '追加中...' : '追加'}
              </button>
            </div>
          </div>
        </div>
      )}

      {editingArticle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">記事を編集</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  タイトル
                </label>
                <input
                  type="text"
                  value={editValues.title}
                  onChange={(e) =>
                    setEditValues((prev) => ({
                      ...prev,
                      title: e.target.value,
                    }))
                  }
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder="記事のタイトルを入力..."
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  サマリー
                </label>
                <textarea
                  value={editValues.summary}
                  onChange={(e) =>
                    setEditValues((prev) => ({
                      ...prev,
                      summary: e.target.value,
                    }))
                  }
                  className="w-full border rounded-lg px-3 py-2 min-h-[200px] text-sm"
                  placeholder="記事のサマリーを入力..."
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  公開日
                </label>
                <input
                  type="date"
                  value={editValues.published_date}
                  onChange={(e) =>
                    setEditValues((prev) => ({
                      ...prev,
                      published_date: e.target.value,
                    }))
                  }
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  カテゴリ
                </label>
                <select
                  value={editValues.category}
                  onChange={(e) =>
                    setEditValues((prev) => ({
                      ...prev,
                      category: e.target.value,
                    }))
                  }
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">選択してください</option>
                  {availableCategories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  ビジネス領域
                </label>
                <select
                  value={editValues.business_area}
                  onChange={(e) =>
                    setEditValues((prev) => ({
                      ...prev,
                      business_area: e.target.value,
                    }))
                  }
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">選択してください</option>
                  {availableBusinessAreas.map((area) => (
                    <option key={area} value={area}>
                      {area}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  タグ（カンマ区切り）
                </label>
                <input
                  value={editValues.tags}
                  onChange={(e) =>
                    setEditValues((prev) => ({
                      ...prev,
                      tags: e.target.value,
                    }))
                  }
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="例: 生成AI, 自動化, OCR"
                />
              </div>
              <div className="pt-2 border-t space-y-3">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_inappropriate"
                    checked={editValues.is_inappropriate}
                    onChange={(e) =>
                      setEditValues((prev) => ({
                        ...prev,
                        is_inappropriate: e.target.checked,
                        inappropriate_reason: e.target.checked ? prev.inappropriate_reason : '',
                      }))
                    }
                    className="w-4 h-4"
                  />
                  <label htmlFor="is_inappropriate" className="text-sm text-red-600 font-medium cursor-pointer">
                    不適切な記事としてマーク（一覧・分析から除外されます）
                  </label>
                </div>
                {editValues.is_inappropriate && (
                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700">
                      不適切な理由 <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={editValues.inappropriate_reason}
                      onChange={(e) =>
                        setEditValues((prev) => ({
                          ...prev,
                          inappropriate_reason: e.target.value,
                        }))
                      }
                      className="w-full border rounded-lg px-3 py-2"
                      rows={3}
                      placeholder="例: 金融業界と無関係、AI/DXに関する内容なし、重複記事など"
                      required={editValues.is_inappropriate}
                    />
                  </div>
                )}
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                type="button"
                onClick={cancelEdit}
                className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50"
                disabled={savingArticle}
              >
                キャンセル
              </button>
              <button
                type="button"
                onClick={saveEdit}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60"
                disabled={savingArticle}
              >
                {savingArticle ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
