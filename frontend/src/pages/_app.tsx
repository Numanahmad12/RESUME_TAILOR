import type { AppProps } from 'next/app';
import Head from 'next/head';
import { Toaster } from 'react-hot-toast';
import { AnimatePresence } from 'framer-motion';
import '../styles/globals.css';

// Register GSAP ScrollTrigger globally once on client startup.
if (typeof window !== 'undefined') {
  // Dynamic import so it never runs on the server
  import('gsap').then(({ gsap }) => {
    import('gsap/dist/ScrollTrigger').then(({ ScrollTrigger }) => {
      gsap.registerPlugin(ScrollTrigger);
    });
  });
}

export default function App({ Component, pageProps, router }: AppProps) {
  return (
    <>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <AnimatePresence mode="wait" initial={false}>
        <Component {...pageProps} key={router.pathname} />
      </AnimatePresence>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid rgba(255,46,46,0.25)',
            borderRadius: '12px',
            fontSize: '14px',
          },
          success: { iconTheme: { primary: '#10b981', secondary: '#f1f5f9' } },
          error: { iconTheme: { primary: '#ef4444', secondary: '#f1f5f9' } },
        }}
      />
    </>
  );
}
