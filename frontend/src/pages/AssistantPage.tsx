import { FormEvent, useState } from "react";
import { Bot } from "lucide-react";
import { api } from "../api";

type AssistantResponse = {
  answer: string;
  sources: { id: string; title: string; source: string; url: string; relevance: number }[];
  retrieval_status: string;
  generation: string;
  caution: string;
};

export default function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AssistantResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function ask(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await api<AssistantResponse>("/api/v1/assistant", {
        method: "POST",
        body: JSON.stringify({ question }),
      }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The assistant request failed.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="page">
    <div className="page-heading"><div><div className="eyebrow">Healthcare information assistant</div><h1>Ask a general health question</h1></div></div>
    <section className="assistant-panel">
      <div className="chat-empty"><Bot size={32} /><p>Answers are extractive summaries from the local MedlinePlus source collection, with links to the original pages. This assistant does not diagnose or prescribe.</p></div>
      {loading && <div className="loading-message" role="status">Searching source documents…</div>}
      {error && <div className="error" role="alert">{error}</div>}
      {result && <div className="chat-answer" aria-live="polite">
        <strong>HealthWise AI · {result.generation} response</strong>
        <p className="assistant-answer">{result.answer}</p>
        {result.sources.length > 0 && <div className="citation-list"><strong>Sources</strong>{result.sources.map((source, index) =>
          <a key={source.id} href={source.url} target="_blank" rel="noreferrer">[{index + 1}] {source.title} — {source.source} ↗</a>
        )}</div>}
        <small>{result.caution}</small>
      </div>}
      <form onSubmit={ask}>
        <label className="sr-only" htmlFor="assistant-question">Question</label>
        <input id="assistant-question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about cough, headache, or chest pain information…" required maxLength={500} />
        <button className="button primary" type="submit" disabled={loading}>{loading ? "Searching…" : "Ask"}</button>
      </form>
    </section>
  </div>;
}
