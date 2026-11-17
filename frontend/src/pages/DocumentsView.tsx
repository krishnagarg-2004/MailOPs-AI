import React, { useEffect, useState } from 'react';
import { DocumentViewerWidget } from '../components/DocumentViewerWidget';
import { useToast } from '../context/ToastContext';
import { api } from '../services/api';
import { BusinessDocumentExtractionResult, DocumentExtractionResult } from '../types/document';

interface AttachmentItem {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
}

export const DocumentsView: React.FC = () => {
  const { toast } = useToast();
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
      toast.success('OCR & text extraction completed!');
    } catch (err: any) {
      toast.error(`OCR Extraction Error: ${err.message}`);
    }
  };

  const handleAnalyzeBusinessDoc = async () => {
    if (!selectedAttachment) return;
    try {
      const result = await api.analyzeBusinessDocument(selectedAttachment.id);
      setBusinessExtraction(result);
      toast.success('Business document analysis completed!');
    } catch (err: any) {
      toast.error(`Business Document AI Analysis Error: ${err.message}`);
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
      <div className="flex flex-wrap items-center justify-between border-b border-zinc-800 pb-4 gap-3">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span>Document Intelligence & OCR Workspace</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950/60 text-red-400 border border-red-800/60 uppercase tracking-wider font-semibold">Tesseract OCR</span>
          </h2>
          <p className="text-xs text-zinc-400">
            Extract native text, perform Tesseract OCR page rendering, and parse structured invoice/contract metadata.
          </p>
        </div>

        {extraction?.extracted_text && (
          <button
            onClick={handleDownloadOcrText}
            className="flex items-center gap-1.5 text-xs bg-red-950/40 hover:bg-red-900/60 text-red-300 border border-red-800/60 hover:border-red-600 px-3 py-1.5 rounded-lg transition font-medium shadow-sm"
            title="Download extracted plaintext file"
          >
            <span>📥</span> Download OCR Text (.txt)
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Attachment Browser with Search & Categories */}
        <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 space-y-3 shadow-lg">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Attachments ({filteredAttachments.length})
            </h3>
            <span className="text-[10px] text-zinc-500 font-mono">Total: {attachments.length}</span>
          </div>

          {/* Search Box */}
          <input
            type="text"
            placeholder="Search attachments..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-800 rounded-lg text-xs px-3 py-1.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/30"
          />

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1 text-[10px]">
            {(['ALL', 'PDF', 'IMAGE', 'DOCX'] as const).map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`px-2 py-0.5 rounded font-medium transition ${
                  categoryFilter === cat
                    ? 'bg-red-600 text-white font-semibold shadow-sm'
                    : 'bg-zinc-900 text-zinc-400 hover:text-white border border-zinc-800'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="text-xs text-zinc-500 py-8 text-center">Loading attachments...</div>
          ) : filteredAttachments.length === 0 ? (
            <div className="text-xs text-zinc-500 py-8 text-center">No matching attachments found.</div>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
              {filteredAttachments.map((att) => (
                <div
                  key={att.id}
                  onClick={() => handleSelectAttachment(att)}
                  className={`p-3 rounded-lg border cursor-pointer transition ${
                    selectedAttachment?.id === att.id
                      ? 'bg-zinc-900 border-l-4 border-l-red-500 border-y border-r border-zinc-800 shadow-md'
                      : 'bg-zinc-900/60 border-zinc-800/80 hover:border-zinc-700'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-zinc-200 truncate max-w-[170px]">
                      {att.filename}
                    </span>
                    <span className="text-[10px] text-zinc-500 font-mono">
                      {(att.size_bytes / 1024).toFixed(1)} KB
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-400 font-mono truncate">
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
            <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-12 text-center text-xs text-zinc-500">
              Select an attachment to view extracted OCR page text or run business metadata extraction.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
