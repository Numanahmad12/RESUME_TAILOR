/**
 * Next.js API proxy: /api/generate-tailored → FastAPI POST /api/generate-tailored
 * Forwards multipart FormData untouched and streams the file response back.
 */
import type { NextApiRequest, NextApiResponse } from 'next';

export const config = {
  api: { bodyParser: false },
};

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const chunks: Buffer[] = [];
    for await (const chunk of req as unknown as AsyncIterable<Buffer>) {
      chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
    }

    const backendRes = await fetch(`${BACKEND}/api/generate-tailored`, {
      method: 'POST',
      headers: {
        'content-type': (req.headers['content-type'] as string) ?? 'application/x-www-form-urlencoded',
      },
      body: Buffer.concat(chunks),
    });

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
