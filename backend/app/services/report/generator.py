from datetime import date, datetime
from typing import List, Dict, Optional
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Article, Company


class ReportGenerator:
    """Markdownレポートを生成"""
    
    def __init__(self, output_dir: str = "/app/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    async def generate(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: date,
    ) -> str:
        """
        レポートを生成
        
        Args:
            db: DBセッション
            start_date: 対象開始日
            end_date: 対象終了日
        
        Returns:
            生成したレポートのファイルパス
        """
        # 企業と記事を取得
        query = select(Company).options(
            selectinload(Company.articles)
        ).where(Company.is_active == True)
        
        result = await db.execute(query)
        companies = result.scalars().all()
        
        # レポート生成
        report_lines = [
            f"# AI・DX事例調査レポート",
            f"",
            f"**調査期間**: {start_date} 〜 {end_date}",
            f"**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"",
            f"---",
            f"",
        ]
        
        for company in companies:
            # 期間内の記事をフィルタ（発行日不明は除外しない）
            articles = [
                a for a in company.articles
                if (a.published_date is None)
                or (start_date <= a.published_date <= end_date)
            ]
            
            report_lines.append(f"# {company.name}")
            if company.country:
                report_lines.append(f"**国**: {company.country}")
            report_lines.append("")

            if not articles:
                report_lines.append("該当なし")
                report_lines.append("")
                report_lines.append("---")
                report_lines.append("")
                continue
            
            # カテゴリごとにグループ化
            by_category = {}
            for article in articles:
                cat = article.category or "その他"
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(article)
            
            for category, cat_articles in by_category.items():
                report_lines.append(f"## 【{category}】")
                report_lines.append("")
                
                for article in cat_articles:
                    report_lines.append(f"### {article.title}")
                    report_lines.append("")
                    
                    if article.summary:
                        report_lines.append(article.summary)
                        report_lines.append("")
                    elif article.content:
                        report_lines.append("## 本文")
                        report_lines.append(article.content)
                        report_lines.append("")
                    
                    # メタ情報
                    report_lines.append("#### メタ情報")
                    report_lines.append(f"- **カテゴリ**: {article.category or '未分類'}")
                    report_lines.append(f"- **業務領域**: {article.business_area or '未分類'}")
                    
                    if article.tags:
                        tags = " ".join([f"#{t.strip()}" for t in article.tags.split(",")])
                        report_lines.append(f"- **タグ**: {tags}")
                    
                    if article.published_date:
                        report_lines.append(f"- **発行日**: {article.published_date}")
                    else:
                        report_lines.append("- **発行日**: 不明")
                    
                    report_lines.append(f"- **ソース**: {article.url}")
                    report_lines.append("")
                    report_lines.append("---")
                    report_lines.append("")
            
            report_lines.append("")
        
        # ファイル出力
        filename = f"report_{start_date}_{end_date}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        
        return filepath
