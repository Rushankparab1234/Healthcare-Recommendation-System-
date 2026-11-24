import { FormEvent, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import {
  Activity,
  Bot,
  BookOpen,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  MapPin,
  ShieldCheck,
  Stethoscope,
  UserRound,
} from "lucide-react";
import { api, getToken } from "./api";
import DashboardPage from "./pages/DashboardPage";
import AssessmentPage from "./pages/AssessmentPage";
import ProviderDirectory, { ProviderDetailPage } from "./pages/ProviderDirectory";
import KnowledgeCenter, { KnowledgeArticlePage } from "./pages/KnowledgeCenter";
import AssistantPage from "./pages/AssistantPage";
import ProfilePage from "./pages/ProfilePage";

function Logo() {
  return (
    <Link className="brand" to="/">
      <span className="brand-mark"><HeartPulse size={20} /></span>
      <span>HealthWise <b>AI</b></span>
    </Link>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const authenticated = Boolean(getToken());
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Logo />
        <nav>
          <Link to="/dashboard"><LayoutDashboard size={18} /> Dashboard</Link>
          <Link to="/assessment"><Stethoscope size={18} /> Symptom assessment</Link>
          <Link to="/providers"><MapPin size={18} /> Find providers</Link>
          <Link to="/assistant"><Bot size={18} /> Health assistant</Link>
          <Link to="/knowledge"><BookOpen size={18} /> Knowledge center</Link>
          <Link to="/profile"><UserRound size={18} /> Profile</Link>
        </nav>
        {authenticated ? (
          <button className="logout" onClick={() => { localStorage.clear(); navigate("/"); }}>
            <LogOut size={18} /> Sign out
          </button>
        ) : <Link className="sidebar-login" to="/login">Sign in</Link>}
      </aside>
      <main>{children}</main>
    </div>
  );
}

function Landing() {
  return (
    <div className="landing">
      <header className="topbar"><Logo /><div><Link to="/login">Sign in</Link><Link className="button" to="/register">Create account</Link></div></header>
      <section className="hero">
        <div>
          <div className="eyebrow"><ShieldCheck size={16} /> Private healthcare navigation</div>
          <h1>Find the right care, <span>with clarity.</span></h1>
          <p>HealthWise AI organizes health concerns and helps you explore relevant specialties and demo providers—without claiming to diagnose.</p>
          <Link className="button primary" to="/assessment">Start an assessment</Link>
        </div>
        <div className="hero-card">
          <div className="card-label">Navigation summary</div>
          <div className="pulse-row"><span><Activity size={18} /></span><div><small>Concern type</small><strong>General symptom review</strong></div></div>
          <div className="pulse-row"><span><Stethoscope size={18} /></span><div><small>Suggested next step</small><strong>Explore relevant specialties</strong></div></div>
          <div className="safety-note"><ShieldCheck size={16} /> Emergency signs are handled with urgent-care guidance.</div>
        </div>
      </section>
      <section className="trust-strip">
        <div><strong>Transparent</strong><span>Explainable ranking</span></div>
        <div><strong>Safety-first</strong><span>Emergency override</span></div>
        <div><strong>Synthetic demo</strong><span>No real providers</span></div>
      </section>
      <footer>Educational decision support only. Not a diagnosis or substitute for professional medical care.</footer>
    </div>
  );
}

function AuthPage({ mode }: { mode: "login" | "register" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      const data = await api<{
        access_token: string;
        token_type: string;
        role: string;
        full_name: string;
      }>(
        mode === "login" ? "/api/v1/auth/login" : "/api/v1/auth/register",
        { method: "POST", body: JSON.stringify(mode === "login" ? { email, password } : { email, password, full_name: name }) },
      );
      localStorage.setItem("healthwise_token", data.access_token);
      localStorage.setItem("healthwise_name", data.full_name);
      setSuccess(mode === "register" ? "Account created. Redirecting to your dashboard…" : "Signed in. Redirecting…");
      window.setTimeout(() => navigate("/dashboard"), 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to continue.");
    } finally {
      setLoading(false);
    }
  }
  return (
    <div className="auth-layout">
      <div className="auth-logo"><Logo /></div>
      <form className="auth-card" onSubmit={submit}>
        <div className="eyebrow">Secure account</div>
        <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
        {mode === "register" && <label>Full name<input value={name} onChange={(e) => setName(e.target.value)} required minLength={2} /></label>}
        <label>Email address<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
        <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={mode === "register" ? 12 : 1} /></label>
        {error && <div className="error" role="alert">{error}</div>}
        {success && <div className="success" role="status">{success}</div>}
        <button className="button primary" type="submit" disabled={loading}>
          {loading ? (mode === "login" ? "Signing in…" : "Creating account…") : (mode === "login" ? "Sign in" : "Create account")}
        </button>
        <p>{mode === "login" ? "New to HealthWise?" : "Already have an account?"} <Link to={mode === "login" ? "/register" : "/login"}>{mode === "login" ? "Create account" : "Sign in"}</Link></p>
      </form>
    </div>
  );
}

function Protected({ children }: { children: React.ReactNode }) {
  return getToken() ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/register" element={<AuthPage mode="register" />} />
      <Route path="/dashboard" element={<Protected><Shell><DashboardPage /></Shell></Protected>} />
      <Route path="/assessment" element={<Protected><Shell><AssessmentPage /></Shell></Protected>} />
      <Route path="/providers" element={<Protected><Shell><ProviderDirectory /></Shell></Protected>} />
      <Route path="/providers/:providerId" element={<Protected><Shell><ProviderDetailPage /></Shell></Protected>} />
      <Route path="/assistant" element={<Protected><Shell><AssistantPage /></Shell></Protected>} />
      <Route path="/knowledge" element={<Protected><Shell><KnowledgeCenter /></Shell></Protected>} />
      <Route path="/knowledge/:articleId" element={<Protected><Shell><KnowledgeArticlePage /></Shell></Protected>} />
      <Route path="/profile" element={<Protected><Shell><ProfilePage /></Shell></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
