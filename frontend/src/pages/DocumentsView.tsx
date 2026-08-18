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
      alert(`Document OCR Processing Error: ${err.message}`);
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

  return (
    <div className="space-y-6 font-sans">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-lg font-bold text-slate-100">Document Intelligence & OCR Workspace</h2>
        <p className="text-xs text-slate-400">
          Extract native text, perform Tesseract OCR page rendering, and parse structured invoice/contract metadata.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Attachment Browser */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Email Attachments ({attachments.length})
          </h3>

          {isLoading ? (
            <div className="text-xs text-slate-500 py-8 text-center">Loading attachments...</div>
          ) : attachments.length === 0 ? (
            <div className="text-xs text-slate-500 py-8 text-center">No email attachments found in mailbox.</div>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
              {attachments.map((att) => (
                <div
                  key={att.id}
                  onClick={() => handleSelectAttachment(att)}
                  className={`p-3 rounded-lg border cursor-pointer transition ${
                    selectedAttachment?.id === att.id
                      ? 'bg-slate-800 border-purple-500/50'
                      : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-200 truncate max-w-[180px]">
                      {att.filename}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {(att.size_bytes / 1024).toFixed(1)} KB
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono">
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
