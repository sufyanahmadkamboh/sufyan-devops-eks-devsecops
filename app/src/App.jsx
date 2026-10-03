import { profile } from "./profile.js";
import "./App.css";

// Version and commit are baked in at build time by the pipeline (see Dockerfile), so the page shows what runs.
const build = { version: import.meta.env.VITE_VERSION || "dev", commit: (import.meta.env.VITE_COMMIT || "local").slice(0, 7) };

export default function App() {
  return (
    <main>
      <article className="card" aria-label="Profile card">
        <header className="header">
          <div className="avatar" aria-hidden="true">{profile.initials}</div>
          <div>
            <h1 className="name">{profile.name}</h1>
            <p className="role">{profile.role}</p>
          </div>
        </header>
        <p className="bio">{profile.bio}</p>
        <ul className="meta" aria-label="Skills">
          {profile.tags.map((t) => (
            <li key={t} className="tag">{t}</li>
          ))}
        </ul>
        <nav className="cta" aria-label="Links">
          {profile.links.map((l) => (
            <a key={l.label} className={l.primary ? "btn primary" : "btn"} href={l.href}
               {...(l.href.startsWith("http") ? { target: "_blank", rel: "noreferrer noopener" } : {})}>
              {l.label}
            </a>
          ))}
        </nav>
        <footer className="build">
          v{build.version} · {build.commit} · served from Amazon EKS
        </footer>
      </article>
    </main>
  );
}
