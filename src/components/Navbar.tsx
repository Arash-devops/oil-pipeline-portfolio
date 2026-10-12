"use client";
import { useRef, useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import styles from "./Navbar.module.css";

const links = [
  { label: "Research", href: "/#research" },
  { label: "Publications", href: "/#publications" },
  { label: "Projects", href: "/#projects" },
  { label: "About", href: "/#about" },
];
export default function Navbar() {
  const [open, setOpen] = useState(false);
  const button = useRef<HTMLButtonElement>(null);
  const pathname = usePathname();
  return (
    <header
      className={`${styles.header} ${pathname !== "/" ? styles.dark : ""}`}
      onKeyDown={(event) => {
        if (event.key === "Escape" && open) {
          setOpen(false);
          button.current?.focus();
        }
      }}
    >
      <a className={styles.skip} href="#main-content">
        Skip to content
      </a>
      <nav className={styles.nav} aria-label="Main navigation">
        <Link href="/" className={styles.brand} onClick={() => setOpen(false)}>
          Arash Razban<span>.</span>
        </Link>
        <button
          ref={button}
          className={styles.toggle}
          type="button"
          aria-expanded={open}
          aria-controls="main-navigation"
          onClick={() => setOpen(!open)}
        >
          {open ? "Close" : "Menu"}{" "}
          <span aria-hidden="true">{open ? "×" : "+"}</span>
        </button>
        <div
          id="main-navigation"
          className={`${styles.links} ${open ? styles.open : ""}`}
        >
          {links.map((link) => (
            <Link
              href={link.href}
              key={link.href}
              onClick={() => setOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <Link
            href="/#contact"
            className={styles.contact}
            onClick={() => setOpen(false)}
          >
            Let’s connect <span aria-hidden="true">↗</span>
          </Link>
        </div>
      </nav>
    </header>
  );
}
