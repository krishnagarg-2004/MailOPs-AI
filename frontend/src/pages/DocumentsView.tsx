import React, { useEffect, useState } from 'react';
import { Download, FileText, Search } from 'lucide-react';
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
    <div className="space-y-5 font-sans">
      <div className="flex flex-wrap items-center justify-between border-b border-white/[0.06] pb-3.5 gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2 tracking-tight">
            <span>Document Intelligence & OCR Workspace</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.04] text-zinc-400 border border-white/[0.08] tracking-wider">
              Tesseract OCR
            </span>
          </h2>
          <p className="text-xs text-zinc-500 mt-0.5">
            Extract native text, perform OCR page rendering, and parse structured invoice/contract metadata.
          </p>
        </div>

        {extraction?.extracted_text && (
          <button
            onClick={handleDownloadOcrText}
            className="flex items-center gap-1.5 text-xs bg-white/[0.04] hover:bg-white/[0.08] text-zinc-200 border border-white/[0.08] hover:border-white/[0.14] px-3 py-1.5 rounded-lg transition font-medium shadow-sm active:scale-95"
            title="Download extracted plaintext file"
          >
            <Download className="w-3.5 h-3.5 text-zinc-400" />
            <span>Download OCR Text (.txt)</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left Column: Attachment Browser */}
        <div className="bg-[#0e0e12] border border-white/[0.07] rounded-xl p-3.5 space-y-3 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]">
          <div className="flex items-center justify-between">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
              Attachments ({filteredAttachments.length})
            </h3>
            <span className="text-[10px] text-zinc-500 font-mono px-2 py-0.5 rounded bg-white/[0.03] border border-white/[0.06] tabular-nums">
              Total: {attachments.length}
            </span>
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search attachments..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#121216] border border-white/[0.07] rounded-lg text-xs pl-8 pr-3 py-1.5 text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-red-500/60 transition"
            />
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1 text-[10px]">
            {(['ALL', 'PDF', 'IMAGE', 'DOCX'] as const).map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`px-2.5 py-1 rounded-md font-medium transition ${
                  categoryFilter === cat
                    ? 'bg-white/[0.08] text-white border border-white/[0.12] font-semibold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)]'
                    : 'bg-white/[0.02] text-zinc-400 hover:text-white border border-white/[0.05]'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="text-xs text-zinc-500 py-12 text-center space-y-2">
              <span className="w-3.5 h-3.5 border-2 border-red-500 border-t-transparent rounded-full animate-spin inline-block"></span>
              <p>Loading attachments...</p>
            </div>
          ) : filteredAttachments.length === 0 ? (
            <div className="text-xs text-zinc-500 py-12 text-center">No matching attachments found.</div>
          ) : (
            <div className="space-y-1.5 max-h-[500px] overflow-y-auto pr-1">
              {filteredAttachments.map((att) => (
                <div
                  key={att.id}
                  onClick={() => handleSelectAttachment(att)}
                  className={`p-2.5 rounded-lg border cursor-pointer transition-all duration-150 ${
                    selectedAttachment?.id === att.id
                      ? 'bg-[#15151b] border-l-2 border-l-red-500 border-t-white/[0.1] border-r-white/[0.1] border-b-white/[0.1] shadow-sm'
                      : 'bg-[#0a0a0d] border-white/[0.05] hover:border-white/[0.1] hover:bg-white/[0.03]'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-0.5">
                    <span className="font-medium text-zinc-200 truncate max-w-[170px]">
                      {att.filename}
                    </span>
                    <span className="text-[10px] text-zinc-500 font-mono tabular-nums">
                      {(att.size_bytes / 1024).toFixed(1)} KB
                    </span>
                  </div>
                  <p className="text-[10px] text-zinc-500 font-mono truncate">
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
            <div className="bg-[#0e0e12] border border-white/[0.07] rounded-xl p-16 text-center text-xs text-zinc-500 space-y-2.5 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]">
              <div className="w-10 h-10 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mx-auto text-zinc-500">
                <FileText className="w-5 h-5" />
              </div>
              <p>Select an attachment to view extracted OCR page text or run business metadata extraction.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
