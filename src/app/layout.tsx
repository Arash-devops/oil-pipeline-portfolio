import type { Metadata } from 'next';
import { Playfair_Display, DM_Sans, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { siteConfig } from '@/data/config';

const playfair = Playfair_Display({
  subsets: ['latin'],
  weight: ['400', '600', '700', '900'],
  variable: '--font-playfair',
  display: 'swap',
});

const dmSans = DM_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600'],
  variable: '--font-dm-sans',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-jetbrains',
  display: 'swap',
});

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.openGraph.url),
  title: siteConfig.title,
  description: siteConfig.description,
  keywords: [
    'DevOps Engineer', 'Data Engineer', 'Backend Developer',
    'Cloud Engineer', 'Kubernetes', 'Terraform', 'Apache Spark',
    'Python', 'Go', 'Germany', 'Arash Razban',
  ],
  authors: [{ name: siteConfig.name }],
  creator: siteConfig.name,
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: siteConfig.openGraph.url,
    title: siteConfig.title,
    description: siteConfig.description,
    siteName: siteConfig.name,
    images: [
      {
        url: siteConfig.openGraph.image,
        width: 1200,
        height: 630,
        alt: `${siteConfig.name} — Portfolio`,
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: siteConfig.title,
    description: siteConfig.description,
    images: [siteConfig.openGraph.image],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: import('react').ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`scroll-smooth ${playfair.variable} ${dmSans.variable} ${jetbrainsMono.variable}`}
    >
      <body className="bg-[#0a0e17] text-slate-200 antialiased">
        {children}
      </body>
    </html>
  );
}
