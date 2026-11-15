import React, { useEffect, useState } from 'react';
import { DocumentViewerWidget } from '../components/DocumentViewerWidget';
import { api } from '../services/api';
import { BusinessDocumentExtractionResult, DocumentExtractionResult } from '../types/document';

interface AttachmentItem {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
}

export const DocumentsView: React.FC = () => {
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [selectedAttachment, setSelectedAttachment] = useState<AttachmentItem | null>(null);
  const [extraction, setExtraction] = useState<DocumentExtractionResult | undefined>(undefined);
  const [businessExtraction, setBusinessExtraction] = useState<BusinessDocumentExtractionResult | undefined>(undefined);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Search & Category Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<'ALL' | 'PDF' | 'IMAGE' | 'DOCX'>('ALL');

  const fetchAttachments = async () => {
    try {
      setIsLoading(true);
      const threads = await api.getGmailThreads();
      const atts: AttachmentItem[] = [];
      threads.forEach((t) => {
        t.messages.forEach((m) => {
          if (m.attachments) {
            atts.push(...m.attachments);
          }
        });
      });
      setAttachments(atts);
      if (atts.length > 0) {
        handleSelectAttachment(atts[0]);
      }
    } catch {
      // Ignore background errors
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAttachments();
  }, []);

  const handleSelectAttachment = async (att: AttachmentItem) => {
    setSelectedAttachment(att);
    setExtraction(undefined);
    setBusinessExtraction(undefined);

    try {
      const ext = await api.getDocumentExtraction(att.id);
      setExtraction(ext);
    } catch {
      // Not extracted yet
    }

    try {
      const biz = await api.getBusinessDocumentExtraction(att.id);
      setBusinessExtraction(biz);
    } catch {
      // Not analyzed yet
    }
  };

  const handleProcessDocument = async () => {
    if (!selectedAttachment) return;
    try {
      const result = await api.processDocument(selectedAttachment.id);
      setExtraction(result);
    } catch (err: any) {
      alert(`OCR Extraction Error: ${err.message}`);
    }
  };

  const handleAnalyzeBusinessDoc = async () => {
    if (!selectedAttachment) return;
    try {
      const result = await api.analyzeBusinessDocument(selectedAttachment.id);
      setBusinessExtraction(result);
    } catch (err: any) {
      alert(`Business Document AI Analysis Error: ${err.message}`);
    }
  };

  const handleDownloadOcrText = () => {
    if (!extraction?.extracted_text || !selectedAttachment) return;
    const blob = new Blob([extraction.extracted_text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedAttachment.filename.replace(/\.[^/.]+$/, '')}_ocr_extracted.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Filtered Attachments
  const filteredAttachments = attachments.filter((att) => {
    const matchSearch =
      !searchQuery ||
      att.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      att.mime_type.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchSearch) return false;

    if (categoryFilter === 'PDF') {
      return att.mime_type.includes('pdf') || att.filename.endsWith('.pdf');
    }
    if (categoryFilter === 'IMAGE') {
      return att.mime_type.includes('image') || att.filename.match(/\.(png|jpe?g)$/i);
    }
    if (categoryFilter === 'DOCX') {
      return att.mime_type.includes('word') || att.filename.endsWith('.docx');
    }
    return true;
  });

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-4 gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-100">Document Intelligence & OCR Workspace</h2>
          <p className="text-xs text-slate-400">
            Extract native text, perform Tesseract OCR page rendering, and parse structured invoice/contract metadata.
          </p>
        </div>

        {extraction?.extracted_text && (
          <button
            onClick={handleDownloadOcrText}
            className="flex items-center gap-1.5 text-xs bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 px-3 py-1.5 rounded-lg transition font-medium"
            title="Download extracted plaintext file"
          >
            <span>📥</span> Download OCR Text (.txt)
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Attachment Browser with Search & Categories */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Attachments ({filteredAttachments.length})
            </h3>
            <span className="text-[10px] text-slate-500 font-mono">Total: {attachments.length}</span>
          </div>

          {/* Search Box */}
          <input
            type="text"
            placeholder="Search attachments..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg text-xs px-3 py-1.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1 text-[10px]">
            {(['ALL', 'PDF', 'IMAGE', 'DOCX'] as const).map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`px-2 py-0.5 rounded font-medium transition ${
                  categoryFilter === cat
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="text-xs text-slate-500 py-8 text-center">Loading attachments...</div>
          ) : filteredAttachments.length === 0 ? (
            <div className="text-xs text-slate-500 py-8 text-center">No matching attachments found.</div>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
              {filteredAttachments.map((att) => (
                <div
                  key={att.id}
                  onClick={() => handleSelectAttachment(att)}
                  className={`p-3 rounded-lg border cursor-pointer transition ${
                    selectedAttachment?.id === att.id
                      ? 'bg-slate-800 border-purple-500/50 shadow-xs'
                      : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-200 truncate max-w-[170px]">
                      {att.filename}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {(att.size_bytes / 1024).toFixed(1)} KB
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono truncate">
                    {att.mime_type}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Document Viewer Widget */}
        <div className="lg:col-span-2">
          {selectedAttachment ? (
            <DocumentViewerWidget
              filename={selectedAttachment.filename}
              extraction={extraction}
              businessExtraction={businessExtraction}
              onTriggerProcess={handleProcessDocument}
              onTriggerBusinessAnalysis={handleAnalyzeBusinessDoc}
            />
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-xs text-slate-500">
              Select an attachment to view extracted OCR page text or run business metadata extraction.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
