import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { BookOpen, Search } from "lucide-react";
import { api } from "../api";

export type KnowledgeArticle = {
  id: string;
  title: string;
  category: string;
  source_name: string;
  source_url: string;
  content: string;
  reviewed_at: string;
  relevance?: number;
};

export default function KnowledgeCenter() {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadArticles(event?: FormEvent) {
    event?.preventDefault();
    setLoading(true);
    setError("");
    const params = new URLSearchParams();
    if (search.trim()) params.set("search", search.trim());
    if (category) params.set("category", category);
    try {
      const response = await api<KnowledgeArticle[]>(`/api/v1/knowledge${params.size ? `?${params.toString()}` : ""}`);
      setArticles(response);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load health information.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadArticles(); }, []);
  useEffect(() => {
    api<string[]>("/api/v1/knowledge/categories")
      .then(setCategories)
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Could not load article categories."));
  }, []);

  return <div className="page">
    <div className="page-heading"><div><div className="eyebrow">Knowledge center</div><h1>Health information from trusted sources</h1></div></div>
    <p className="page-intro">Browse general educational material from MedlinePlus, U.S. National Library of Medicine. Content is not personal medical advice.</p>
    <form className="filter-bar knowledge-filters" onSubmit={loadArticles}>
      <label>Search articles<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Try cough, headache, or chest pain" /></label>
      <label>Category<select value={category} onChange={(event) => setCategory(event.target.value)}><option value="">All categories</option>{categories.map((item) => <option key={item}>{item}</option>)}</select></label>
      <button className="button primary" type="submit"><Search size={16} /> Search</button>
    </form>
    {error && <div className="error" role="alert">{error}</div>}
    {loading && <div className="panel" role="status">Loading source-linked articles…</div>}
    {!loading && !error && articles.length === 0 && <div className="panel empty-state"><BookOpen /><strong>No matching articles found</strong><span>Try a different phrase or category.</span></div>}
    {!loading && articles.length > 0 && <div className="knowledge-grid">{articles.map((article) =>
      <article className="panel knowledge-card" key={article.id}>
        <div className="eyebrow">{article.category}</div>
        <h2><Link to={`/knowledge/${article.id}`}>{article.title}</Link></h2>
        <p>{article.content}</p>
        <div className="source-row">Source: <a href={article.source_url} target="_blank" rel="noreferrer">{article.source_name}</a></div>
        <Link className="text-link" to={`/knowledge/${article.id}`}>Read article details →</Link>
      </article>
    )}</div>}
  </div>;
}

export function KnowledgeArticlePage() {
  const { articleId = "" } = useParams();
  const [article, setArticle] = useState<(KnowledgeArticle & { related_articles: KnowledgeArticle[] }) | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<KnowledgeArticle & { related_articles: KnowledgeArticle[] }>(`/api/v1/knowledge/${encodeURIComponent(articleId)}`)
      .then(setArticle)
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Article unavailable."));
  }, [articleId]);
  return <div className="page">
    <div className="page-heading"><div><div className="eyebrow">Knowledge center</div><h1>{article?.title || "Article"}</h1></div><Link className="button" to="/knowledge">All articles</Link></div>
    {error && <div className="error" role="alert">{error}</div>}
    {!article && !error && <div className="panel" role="status">Loading article…</div>}
    {article && <>
      <article className="panel article-detail">
        <div className="eyebrow">{article.category}</div><p>{article.content}</p>
        <div className="source-box"><strong>Source and attribution</strong><span>{article.source_name}</span><a href={article.source_url} target="_blank" rel="noreferrer">Open original source ↗</a><small>Reviewed for source attribution: {article.reviewed_at}</small></div>
        <p className="disclaimer">This general information is not a diagnosis or treatment recommendation. For personal concerns, consult a licensed healthcare professional.</p>
      </article>
      {article.related_articles.length > 0 && <section className="related-articles"><h2>Related articles</h2><div className="knowledge-grid">{article.related_articles.map((related) =>
        <article className="panel knowledge-card" key={related.id}><h3><Link to={`/knowledge/${related.id}`}>{related.title}</Link></h3><p>{related.category}</p><a href={related.source_url} target="_blank" rel="noreferrer">{related.source_name}</a></article>
      )}</div></section>}
    </>}
  </div>;
}
