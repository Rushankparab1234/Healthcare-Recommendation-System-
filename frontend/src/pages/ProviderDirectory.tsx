import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Bookmark, MapPin, Search, Stethoscope } from "lucide-react";
import { api } from "../api";
import type { Provider } from "../types";

type DashboardSaved = { saved_providers: Provider[] };

export default function ProviderDirectory() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [savedIds, setSavedIds] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [specialtyOptions, setSpecialtyOptions] = useState<string[]>([]);
  const [location, setLocation] = useState("");
  const [consultationType, setConsultationType] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [savingId, setSavingId] = useState("");

  const loadProviders = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.set("search", search.trim());
      if (specialty) params.set("specialty", specialty);
      if (location.trim()) params.set("location", location.trim());
      if (consultationType) params.set("consultation_type", consultationType);
      const query = params.size ? `?${params.toString()}` : "";
      const result = await api<Provider[]>(`/api/v1/providers${query}`);
      setProviders(result);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load providers.");
    } finally {
      setLoading(false);
    }
  }, [consultationType, location, search, specialty]);

  useEffect(() => {
    void loadProviders();
  }, [loadProviders]);

  useEffect(() => {
    api<DashboardSaved>("/api/v1/patients/me/dashboard")
      .then((result) => setSavedIds(result.saved_providers.map((provider) => provider.id)))
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Could not load your saved providers."));
  }, []);

  useEffect(() => {
    api<{ name: string }[]>("/api/v1/specialties")
      .then((result) => setSpecialtyOptions(result.map((item) => item.name)))
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Could not load specialty filters."));
  }, []);

  async function submitSearch(event: FormEvent) {
    event.preventDefault();
    await loadProviders();
  }

  async function toggleSaved(provider: Provider) {
    setSavingId(provider.id);
    setError("");
    setNotice("");
    const currentlySaved = savedIds.includes(provider.id);
    try {
      await api(
        `/api/v1/providers/${encodeURIComponent(provider.id)}/save`,
        { method: currentlySaved ? "DELETE" : "POST" },
      );
      setSavedIds((current) => currentlySaved
        ? current.filter((id) => id !== provider.id)
        : [...current, provider.id]);
      setNotice(currentlySaved ? "Provider removed from saved list." : "Demo provider saved to your dashboard.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update saved providers.");
    } finally {
      setSavingId("");
    }
  }

  return (
    <div className="page">
      <div className="page-heading"><div><div className="eyebrow">Provider discovery</div><h1>Explore demo providers</h1></div></div>
      <div className="safety-banner"><Stethoscope size={18} /><div><strong>Demonstration catalogue only</strong><span>These synthetic entries are not real, verified, or bookable healthcare professionals.</span></div></div>
      <form className="filter-bar provider-filters" onSubmit={submitSearch}>
        <label>Search provider<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Provider name" /></label>
        <label>Specialty<select value={specialty} onChange={(event) => setSpecialty(event.target.value)}><option value="">All specialties</option>{specialtyOptions.map((name) => <option key={name}>{name}</option>)}</select></label>
        <label>Location<input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="City" /></label>
        <label>Consultation<select value={consultationType} onChange={(event) => setConsultationType(event.target.value)}><option value="">Any type</option><option value="in-person">In person</option><option value="video">Video</option></select></label>
        <button className="button primary" type="submit"><Search size={16} /> Search</button>
      </form>
      {error && <div className="error" role="alert">{error}</div>}
      {notice && <div className="success" role="status">{notice}</div>}
      {loading && <div className="panel" role="status">Loading demo providers…</div>}
      {!loading && !error && providers.length === 0 && <div className="panel empty-state"><strong>No providers match these filters</strong><span>Try a different search or clear some filters.</span></div>}
      {!loading && providers.length > 0 && <div className="provider-grid">{providers.map((provider) =>
        <article className="provider-card" key={provider.id}>
          <div className="provider-avatar"><Stethoscope /></div>
          <div>
            <h3><Link to={`/providers/${encodeURIComponent(provider.id)}`}>{provider.name}</Link></h3>
            <p>{provider.specialty}</p>
            <span><MapPin size={14} /> {provider.location}</span>
            <span>{provider.consultation_type}</span>
            <small className="provider-warning">{provider.verification_status}</small>
          </div>
          <button type="button" className="save-button" onClick={() => void toggleSaved(provider)} disabled={savingId === provider.id} aria-label={`${savedIds.includes(provider.id) ? "Unsave" : "Save"} ${provider.name}`}>
            <Bookmark size={16} fill={savedIds.includes(provider.id) ? "currentColor" : "none"} />
            {savingId === provider.id ? "Saving…" : savedIds.includes(provider.id) ? "Saved" : "Save"}
          </button>
        </article>
      )}</div>}
    </div>
  );
}

export function ProviderDetailPage() {
  const { providerId = "" } = useParams();
  const id = providerId;
  const [provider, setProvider] = useState<Provider | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Provider>(`/api/v1/providers/${encodeURIComponent(id)}`)
      .then(setProvider)
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Provider details unavailable."));
  }, [id]);
  return <div className="page">
    <div className="page-heading"><div><div className="eyebrow">Provider details</div><h1>{provider?.name || "Demo provider"}</h1></div><Link className="button" to="/providers">Back to search</Link></div>
    {error && <div className="error" role="alert">{error}</div>}
    {!provider && !error && <div className="panel" role="status">Loading provider details…</div>}
    {provider && <section className="panel provider-detail">
      <span className="badge">SYNTHETIC DEMO · NOT VERIFIED</span>
      <h2>{provider.specialty}</h2><p><MapPin size={16} /> {provider.location}</p>
      <p>Consultation type: {provider.consultation_type}</p>
      <p>Qualifications: {provider.qualification_information}</p>
      <p>Availability: {provider.availability.description}</p>
      <p>Verification: {provider.verification_status}</p>
      <p className="disclaimer">This entry is synthetic, is not a real healthcare professional, and cannot be booked.</p>
    </section>}
  </div>;
}
