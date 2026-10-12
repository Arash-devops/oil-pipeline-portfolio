import Image from "next/image";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { publications, research, education } from "@/data/research";
import { siteConfig } from "@/data/config";
import s from "./portfolio.module.css";

function Arrow() {
  return <span aria-hidden="true">↗</span>;
}

export default function Home() {
  return (
    <div className={s.portfolio}>
      <Navbar />
      <main id="main-content">
        <section
          className={`${s.container} ${s.hero}`}
          aria-labelledby="intro-heading"
        >
          <div>
            <p className={s.eyebrow}>Independent research · Berlin, Germany</p>
            <h1 id="intro-heading">
              Arash Razban<span>.</span>
            </h1>
            <p className={s.heroTitle}>
              Embedded &amp;
              <br />
              hardware security.
            </p>
            <p className={s.heroDescription}>
              I investigate how embedded systems protect secrets and preserve
              trustworthy execution, through firmware development, hardware
              experiments and instruction-trace analysis.
            </p>
            <div className={s.actions}>
              <a className={s.primaryButton} href="#research">
                Explore my research <span aria-hidden="true">↓</span>
              </a>
              <a className={s.textLink} href="#contact">
                Get in touch <Arrow />
              </a>
            </div>
            <p className={s.availability}>
              <span aria-hidden="true" />
              Seeking PhD opportunities in embedded &amp; hardware security
            </p>
          </div>
          <aside className={s.portraitBlock} aria-label="About Arash">
            <div className={s.portraitFrame}>
              <Image
                src="/images/arash-razban.jpg"
                alt="Portrait of Arash Razban"
                width={499}
                height={411}
                priority
                sizes="(max-width: 760px) 145px, 340px"
              />
            </div>
            <div className={s.portraitCaption}>
              <span>Currently</span>
              <p>
                MSc in Cyber Security
                <br />
                <strong>IU International University of Applied Sciences</strong>
              </p>
            </div>
          </aside>
        </section>
        <div className={s.focusStrip}>
          <div className={s.container}>
            <span>Research interests</span>
            <p>
              Timing side channels <i aria-hidden="true">/</i> Constant-time
              cryptography <i aria-hidden="true">/</i> Remote attestation
            </p>
          </div>
        </div>

        <section
          id="research"
          className={`${s.container} ${s.section}`}
          aria-labelledby="research-heading"
        >
          <div className={s.sectionHeading}>
            <div>
              <p className={s.eyebrow}>01 / Research</p>
              <h2 id="research-heading">
                Testing the assumptions
                <br />
                behind secure systems.
              </h2>
            </div>
            <p>
              My current work examines information leakage and state integrity
              on Arm Cortex-M and TrustZone-M.
            </p>
          </div>
          {research.map((study, i) => (
            <article className={s.study} key={study.id}>
              <div className={s.studyIndex}>
                0{i + 1}
                <span>{study.period}</span>
              </div>
              <div className={s.studyBody}>
                <p className={s.studyTopic}>{study.topic}</p>
                <h3>{study.title}</h3>
                <p>{study.description}</p>
                <div className={s.tags}>
                  {study.tools.map((tool) => (
                    <span key={tool}>{tool}</span>
                  ))}
                </div>
                <details className={s.methods}>
                  <summary>
                    Methods &amp; scope <span aria-hidden="true">+</span>
                  </summary>
                  <p>{study.methods}</p>
                </details>
              </div>
              <div className={s.studyLinks}>
                <a href={study.paper} className={s.textLink}>
                  Read preprint <Arrow />
                </a>
                {study.repository && (
                  <a href={study.repository} className={s.secondaryLink}>
                    Research repository <Arrow />
                  </a>
                )}
                <span>Independent research</span>
              </div>
            </article>
          ))}
        </section>

        <section
          id="publications"
          className={s.publicationsSection}
          aria-labelledby="publications-heading"
        >
          <div className={`${s.container} ${s.section}`}>
            <div className={s.sectionHeading}>
              <div>
                <p className={s.eyebrow}>02 / Publications</p>
                <h2 id="publications-heading">Papers &amp; preprints.</h2>
              </div>
              <p>
                Recent security studies and earlier work in image processing.
                Publication status is shown for each entry.
              </p>
            </div>
            {publications.map((paper) => (
              <article className={s.publication} key={paper.doi}>
                <div className={s.paperMeta}>
                  <span>{paper.year}</span>
                  <span className={s.paperType}>{paper.type}</span>
                </div>
                <div>
                  <h3>
                    <a href={`https://doi.org/${paper.doi}`}>
                      {paper.title} <Arrow />
                    </a>
                  </h3>
                  <p>{paper.authors}</p>
                  <p className={s.venue}>{paper.venue}</p>
                  <a className={s.doi} href={`https://doi.org/${paper.doi}`}>
                    DOI: {paper.doi}
                  </a>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section
          id="projects"
          className={`${s.container} ${s.section}`}
          aria-labelledby="projects-heading"
        >
          <div className={s.sectionHeading}>
            <div>
              <p className={s.eyebrow}>03 / Engineering</p>
              <h2 id="projects-heading">Ideas, implemented.</h2>
            </div>
            <p>
              Practical projects in browser-based software and data
              infrastructure.
            </p>
          </div>
          <div className={s.projectGrid}>
            <article className={`${s.project} ${s.pagesong}`}>
              <div className={s.projectTop}>
                <span className={s.projectCategory}>
                  Chrome extension · Open source
                </span>
                <svg
                  className={s.projectIcon}
                  viewBox="0 0 48 48"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M7 21v6m8-13v20m9-28v36m9-28v20m8-13v6"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
              <h3>PageSong</h3>
              <p className={s.projectTagline}>
                Web pages, read aloud. On your device.
              </p>
              <p>
                A published Chrome extension that turns web pages and selected
                text into speech generated locally in the browser, with sentence
                highlighting and playback controls.
              </p>
              <p className={s.projectDetail}>
                Built around local text processing and on-demand access to the
                active tab.
              </p>
              <div className={s.tags}>
                <span>Browser extension</span>
                <span>Local speech synthesis</span>
                <span>Privacy</span>
              </div>
              <div className={s.projectLinks}>
                <a
                  href="https://chromewebstore.google.com/detail/pagesong-read-aloud-with/kmfdokjckbjkjflehcglganmiiiplgea"
                  className={s.textLink}
                >
                  Chrome Web Store <Arrow />
                </a>
                <a
                  href="https://github.com/Arash-devops/pagesong"
                  className={s.secondaryLink}
                >
                  Source code <Arrow />
                </a>
              </div>
            </article>
            <article className={s.project}>
              <div className={s.projectTop}>
                <span className={s.projectCategory}>
                  Data engineering · Open source
                </span>
                <svg
                  className={s.projectIcon}
                  viewBox="0 0 48 48"
                  fill="none"
                  aria-hidden="true"
                >
                  <rect
                    x="3"
                    y="17"
                    width="10"
                    height="14"
                    rx="2"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                  <rect
                    x="19"
                    y="9"
                    width="10"
                    height="30"
                    rx="2"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                  <rect
                    x="35"
                    y="17"
                    width="10"
                    height="14"
                    rx="2"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                  <path
                    d="M13 24h6m10 0h6"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                </svg>
              </div>
              <h3>Oil Price Data Pipeline</h3>
              <p className={s.projectTagline}>
                From raw market data to an observable service.
              </p>
              <p>
                A containerised pipeline for ingesting and serving commodity
                data, combining a PostgreSQL warehouse, a DuckDB/Parquet
                lakehouse and a FastAPI service.
              </p>
              <p className={s.projectDetail}>
                Includes automated tests, CI/CD, Kubernetes deployment and
                Prometheus/Grafana monitoring.
              </p>
              <div className={s.tags}>
                <span>Python</span>
                <span>PostgreSQL &amp; DuckDB</span>
                <span>Docker</span>
              </div>
              <div className={s.projectLinks}>
                <Link href="/pipeline/" className={s.textLink}>
                  Explore the project <Arrow />
                </Link>
                <a
                  href="https://github.com/Arash-devops/oil-pipeline-portfolio"
                  className={s.secondaryLink}
                >
                  Source code <Arrow />
                </a>
              </div>
            </article>
          </div>
        </section>

        <section
          id="about"
          className={`${s.container} ${s.section} ${s.about}`}
          aria-labelledby="about-heading"
        >
          <div className={s.aboutCopy}>
            <p className={s.eyebrow}>04 / Background</p>
            <h2 id="about-heading">
              Hardware foundations.
              <br />A systems perspective.
            </h2>
            <p>
              I am an independent researcher based in Berlin and an MSc Cyber
              Security student at IU International University of Applied
              Sciences.
            </p>
            <p>
              My background brings together computer hardware engineering, data
              science and professional experience in systems administration and
              network infrastructure. Today, I use that perspective to
              investigate the security boundaries between software and hardware.
            </p>
            <a href={siteConfig.social.linkedin} className={s.textLink}>
              Connect on LinkedIn <Arrow />
            </a>
          </div>
          <div className={s.education}>
            <h3>Education</h3>
            {education.map((degree) => (
              <div className={s.degree} key={degree.title}>
                <p className={s.degreePeriod}>
                  {degree.period}
                  {degree.current && <span>In progress</span>}
                </p>
                <h4>{degree.title}</h4>
                <p>{degree.institution}</p>
                {degree.note && <p className={s.degreeNote}>{degree.note}</p>}
              </div>
            ))}
          </div>
        </section>

        <section
          id="contact"
          className={s.contact}
          aria-labelledby="contact-heading"
        >
          <div className={s.container}>
            <div>
              <p className={s.eyebrow}>05 / Contact</p>
              <h2 id="contact-heading">
                Let’s discuss
                <br />
                the next research question.
              </h2>
              <p>
                I’m seeking PhD opportunities in embedded and hardware security,
                with particular interests in side-channel analysis, secure
                firmware and remote attestation.
              </p>
              <p>
                I also welcome conversations about relevant engineering roles
                and research collaborations.
              </p>
            </div>
            <div className={s.contactLinks}>
              <a className={s.emailLink} href={siteConfig.social.email}>
                {siteConfig.email} <Arrow />
              </a>
              <a
                href={`${siteConfig.social.email}?subject=Academic%20CV%20request`}
                className={s.contactSecondary}
              >
                Request my academic CV <Arrow />
              </a>
              <div>
                <a href={siteConfig.social.linkedin}>
                  LinkedIn <Arrow />
                </a>
                <a href={siteConfig.social.github}>
                  GitHub <Arrow />
                </a>
              </div>
            </div>
          </div>
        </section>
      </main>
      <footer className={s.footer}>
        <div className={s.container}>
          <a href="#main-content" className={s.wordmark}>
            Arash Razban<span>.</span>
          </a>
          <span>Berlin, Germany</span>
          <a href="https://github.com/Arash-devops/oil-pipeline-portfolio">
            Website source <Arrow />
          </a>
        </div>
      </footer>
    </div>
  );
}
