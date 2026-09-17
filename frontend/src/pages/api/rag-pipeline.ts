/**
 * Next.js API proxy: /api/rag-pipeline → FastAPI POST /api/rag-pipeline
 * Handles both POST (pipeline) and GET (status check)
 */
import type { NextApiRequest, NextApiResponse } from 'next';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    // Status check
    try {
      const backendRes = await fetch(`${BACKEND}/api/rag-pipeline/status`);
      const data = await backendRes.json();
      return res.status(backendRes.status).json(data);
    } catch (e: any) {
      return res.status(502).json({ error: 'Backend unreachable', detail: e.message });
    }
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const backendRes = await fetch(`${BACKEND}/api/rag-pipeline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body),
    });

    // Success returns a file (PDF/LaTeX/Markdown); errors return JSON.
    // Pass the raw bytes through with the backend's content headers.
    const buf = Buffer.from(await backendRes.arrayBuffer());
    const ct = backendRes.headers.get('content-type');
    const cd = backendRes.headers.get('content-disposition');
    if (ct) res.setHeader('content-type', ct);
    if (cd) res.setHeader('content-disposition', cd);
    return res.status(backendRes.status).send(buf);
  } catch (e: any) {
    return res.status(502).json({ error: 'Backend unreachable', detail: e.message });
  }
}
