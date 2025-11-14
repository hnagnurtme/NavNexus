import { SuggestedDocument } from '@/types';
import { Download } from 'lucide-react';

interface SuggestedDocumentsProps {
  documents: SuggestedDocument[];
}

export const SuggestedDocuments: React.FC<SuggestedDocumentsProps> = ({ documents }) => (
  <section className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
    <div className="mb-3 flex items-center gap-2 text-white">
      <Download width={16} height={16} />
      <h4 className="text-xs font-semibold uppercase tracking-widest">Suggested Uploads</h4>
    </div>
    <ul className="space-y-3">
      {documents.map((doc) => (
        <li key={doc.title} className="rounded-2xl border border-white/10 bg-black/30 p-3">
          <p className="text-base font-semibold text-white">{doc.title}</p>
          <p className="mt-1 text-xs text-white/60">{doc.reason}</p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-emerald-300">
            <a
              href={doc.uploadUrl}
              className="rounded-full border border-emerald-500/40 px-3 py-1 hover:bg-emerald-500/10"
            >
              Upload
            </a>
            {doc.previewUrl && (
              <a
                href={doc.previewUrl}
                className="rounded-full border border-white/20 px-3 py-1 text-white/70 hover:bg-white/10"
              >
                Preview
              </a>
            )}
          </div>
        </li>
      ))}
    </ul>
  </section>
);
