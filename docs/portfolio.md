# Personal research portfolio

The homepage at `arashrazban.com` presents Arash's embedded and hardware security research, publications, engineering projects, education and contact details. The existing data pipeline demonstration remains at `/pipeline/`.

## Edit the website

- Homepage sections and project copy: `src/app/page.tsx`.
- Research, publications and education: `src/data/research.ts`.
- Homepage styles: `src/app/portfolio.module.css`.
- Shared navigation: `src/components/Navbar.tsx` and `Navbar.module.css`.
- Site description and contact details: `src/data/config.ts`.
- Portrait: `public/images/arash-razban.jpg`.
- Social preview and icon: `public/og-image.png` and `public/icon.svg`.

The homepage uses scoped styles. The pipeline demonstration retains its existing dark presentation and functionality. Navigation links return to homepage sections from either route.

## Content sources and scope

The research descriptions, education dates, institutions and publication citations follow the hardware-security CV supplied by Arash on 12 October 2026. The portrait is extracted from that CV without retouching. Research is described as independent; university enrolment is not represented as research employment.

Both Research Square entries are labelled preprints. Hardware experiments are described separately from QEMU instruction-trace analysis. The copy does not claim universal constant-time proofs, unmeasured performance, or security beyond the scope of the studies.

PageSong's description follows its public Chrome Web Store listing and linked repository. The data pipeline description follows this repository. Skill percentages, placeholder project links, unsupported education details, and the claim of three completed master's degrees are removed from the homepage. The current Cyber Security degree is shown as in progress. Certificate dates are omitted because the supplied sources conflict.

The academic CV link opens an email request; the original CV containing phone numbers is not published. Contact links use the email address already published on the site. No contact form backend or analytics service is introduced.

## Check and deploy

```sh
npm ci
npm run build
```

The build performs the existing lint and TypeScript checks and produces the static site in `out/`. The existing GitHub Pages workflow deploys pushes to `master`. The pipeline services and their deployment configuration are unchanged.

Check the homepage at desktop and phone widths, the mobile menu (including Escape), research disclosures, publication links, image loading, and navigation to `/pipeline/` and back before publishing changes.
