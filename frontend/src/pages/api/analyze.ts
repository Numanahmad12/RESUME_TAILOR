/**
 * Next.js API proxy: /api/analyze → FastAPI POST /api/analyze
 */
import type { NextApiRequest, NextApiResponse } from 'next';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const backendRes = await fetch(`${BACKEND}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body),
    });

    const data = await backendRes.json();
    return res.status(backendRes.status).json(data);
  } catch (e: any) {
    return res.status(502).json({ error: 'Backend unreachable', detail: e.message });
  }
}
