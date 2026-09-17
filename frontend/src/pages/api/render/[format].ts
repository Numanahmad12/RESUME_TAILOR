/**
 * Next.js API proxy: /api/render/[format] → FastAPI POST /api/render/{pdf|docx}
 * Streams binary PDF / DOCX file buffer directly back to the browser.
 */
import type { NextApiRequest, NextApiResponse } from 'next';

export const config = {
  api: { bodyParser: false },
};

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { format } = req.query;

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

if (format !== 'pdf' && format !== 'docx' && format !== 'latex') {
    return res.status(400).json({ error: 'Format must be pdf, docx, or latex' });
}

  // Collect raw request body
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  const body = Buffer.concat(chunks);
  const contentType = req.headers['content-type'] ?? 'application/x-www-form-urlencoded';

  try {
    const backendRes = await fetch(`${BACKEND}/api/render/${format}`, {
      method: 'POST',
      headers: { 'Content-Type': contentType },
      body,
    });

    if (!backendRes.ok) {
      const err = await backendRes.text();
      return res.status(backendRes.status).json({ error: err });
    }

    const defaultType = format === 'pdf' ? 'application/pdf' : format === 'docx' ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' : 'text/plain';
    const backendContentType = backendRes.headers.get('content-type') ?? defaultType;
    const disposition = backendRes.headers.get('content-disposition') ?? `attachment; filename="tailored_resume.${format}"`;

    res.setHeader('Content-Type', backendContentType);
    res.setHeader('Content-Disposition', disposition);

    const arrayBuffer = await backendRes.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    res.setHeader('Content-Length', buffer.length.toString());

    return res.end(buffer);
  } catch (e: any) {
    return res.status(502).json({ error: 'Backend unreachable', detail: e.message });
  }
}
