import type { NextApiRequest, NextApiResponse } from 'next';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

export const config = {
  api: {
    responseLimit: false,
  },
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    let backendUrl = `${BACKEND}/api/export`;

    if (req.method === 'GET') {
      const qs = new URLSearchParams(req.query as Record<string, string>).toString();
      if (qs) backendUrl += `?${qs}`;

      const backendRes = await fetch(backendUrl);
      if (!backendRes.ok) {
        const errText = await backendRes.text();
        return res.status(backendRes.status).send(errText);
      }

      const buf = Buffer.from(await backendRes.arrayBuffer());
      const ct = backendRes.headers.get('content-type') || 'application/pdf';
      const cd = backendRes.headers.get('content-disposition');

      res.setHeader('Content-Type', ct);
      if (cd) res.setHeader('Content-Disposition', cd);
      return res.status(backendRes.status).send(buf);
    }

    if (req.method === 'POST') {
      const backendRes = await fetch(backendUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body),
      });

      if (!backendRes.ok) {
        const errText = await backendRes.text();
        return res.status(backendRes.status).send(errText);
      }

      const buf = Buffer.from(await backendRes.arrayBuffer());
      const ct = backendRes.headers.get('content-type') || 'application/pdf';
      const cd = backendRes.headers.get('content-disposition');

      res.setHeader('Content-Type', ct);
      if (cd) res.setHeader('Content-Disposition', cd);
      return res.status(backendRes.status).send(buf);
    }

    return res.status(405).json({ error: 'Method not allowed' });
  } catch (e: any) {
    return res.status(502).json({ error: 'Backend unreachable', detail: e.message });
  }
}
