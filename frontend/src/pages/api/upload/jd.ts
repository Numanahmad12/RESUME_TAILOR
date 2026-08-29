/**
 * Next.js API proxy: /api/upload/jd → FastAPI POST /api/upload/jd
 */
import type { NextApiRequest, NextApiResponse } from 'next';

export const config = {
  api: {
    bodyParser: false,
    sizeLimit: '20mb',
  },
};

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  const body = Buffer.concat(chunks);
  const contentType = req.headers['content-type'] ?? 'application/octet-stream';

  try {
    const backendRes = await fetch(`${BACKEND}/api/upload/jd`, {
      method: 'POST',
      headers: { 'Content-Type': contentType },
      body,
    });

    const data = await backendRes.json();
    return res.status(backendRes.status).json(data);
  } catch (e: any) {
    return res.status(502).json({ error: 'Backend unreachable', detail: e.message });
  }
}
