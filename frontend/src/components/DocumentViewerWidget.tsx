import React, { useEffect, useState } from 'react';
import { Sparkles, AlertCircle } from 'lucide-react';
import { BusinessDocumentExtractionResult, DocumentExtractionResult } from '../types/document';

interface DocumentViewerWidgetProps {
  filename: string;
  extraction?: DocumentExtractionResult;
  businessExtraction?: BusinessDocumentExtractionResult;
  onTriggerProcess?: () => void;
  onTriggerBusinessAnalysis?: () => void;
}

export const DocumentViewerWidget: React.FC<DocumentViewerWidgetProps> = ({
  filename,
  extraction,
  businessExtraction,
  onTriggerProcess,
  onTriggerBusinessAnalysis,
}) => {
  const [activeTab, setActiveTab] = useState<'text' | 'business'>('text');

  useEffect(() => {
    setActiveTab('text');
  }, [filename]);

  return (
    <div className="bg-[#0e0e12] border border-white/[0.07] rounded-xl p-4 sm:p-5 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)] space-y-4 text-[#ededed] font-sans">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] pb-3">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Document Intelligence</span>
          <span className="text-xs font-mono font-medium bg-[#121216] px-2.5 py-1 rounded-md text-zinc-200 border border-white/[0.08]">
            {filename}
          </span>
          {extraction?.is_ocr_applied ? (
            <span className="text-[10px] bg-red-950/40 text-red-400 border border-red-500/20 px-2 py-0.5 rounded-full font-mono">
              OCR (Tesseract)
            </span>
          ) : extraction ? (
            <span className="text-[10px] bg-white/[0.04] text-zinc-300 border border-white/[0.08] px-2 py-0.5 rounded-full font-mono">
              Native Text
            </span>
          ) : null}
        </div>

        <div className="flex items-center gap-2">
          {(!extraction || extraction.status === 'FAILED') && (
            <button
              onClick={onTriggerProcess}
              className="text-xs bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white px-3 py-1.5 rounded-lg transition font-medium shadow-sm active:scale-95 flex items-center gap-1.5"
            >
              <Sparkles className="w-3 h-3" />
              <span>{extraction?.status === 'FAILED' ? 'Retry Extraction' : 'Extract Text & OCR'}</span>
            </button>
          )}
          {extraction && !businessExtraction && (
            <button
              onClick={onTriggerBusinessAnalysis}
              className="text-xs bg-[#121216] hover:bg-[#16161c] text-zinc-300 hover:text-white border border-white/[0.08] px-3 py-1.5 rounded-lg transition font-medium active:scale-95 flex items-center gap-1.5"
            >
              <Sparkles className="w-3 h-3 text-red-400" />
              <span>Analyze Metadata</span>
            </button>
          )}
        </div>
      </div>

      {/* Status Warning if Failed */}
      {extraction?.status === 'FAILED' && (
        <div className="bg-red-950/30 border border-red-500/20 rounded-lg p-3 text-xs text-red-300 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <span><strong>Extraction Error:</strong> {extraction.error_message || 'Document processing failed.'}</span>
        </div>
      )}

      {/* Tabs */}
      {extraction && (
        <>
          <div className="flex items-center gap-1.5 text-xs border-b border-white/[0.06] pb-2">
            <button
              onClick={() => setActiveTab('text')}
              className={`px-3 py-1.5 rounded-md font-medium transition ${
                activeTab === 'text'
                  ? 'bg-white/[0.08] text-white border border-white/[0.12] font-semibold shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Extracted Text ({extraction.char_count} chars
              {extraction.page_count ? `, ${extraction.page_count} pages` : ''})
            </button>

            {businessExtraction && (
              <button
                onClick={() => setActiveTab('business')}
                className={`px-3 py-1.5 rounded-md font-medium transition ${
                  activeTab === 'business'
                    ? 'bg-white/[0.08] text-white border border-white/[0.12] font-semibold shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                Structured Metadata ({businessExtraction.document_category})
              </button>
            )}
          </div>

          {/* Tab Content: Extracted Text */}
          {activeTab === 'text' && (
            <div className="bg-[#0a0a0d] p-4 rounded-lg border border-white/[0.05] max-h-80 overflow-y-auto font-mono text-xs text-zinc-300 leading-relaxed whitespace-pre-wrap">
              {extraction.extracted_text || 'No text extracted.'}
            </div>
          )}

          {/* Tab Content: Business Metadata */}
          {activeTab === 'business' && businessExtraction && (
            <div className="bg-[#0a0a0d] p-4 rounded-lg border border-white/[0.05] space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-2.5 pb-3 border-b border-white/[0.05]">
                <div className="bg-[#121216] p-3 rounded-lg border border-white/[0.06]">
                  <span className="text-zinc-500 block text-[10px] uppercase font-medium">Party / Vendor</span>
                  <strong className="text-zinc-100 text-xs mt-0.5 block">
                    {businessExtraction.vendor_or_party || 'N/A'}
                  </strong>
                </div>
                <div className="bg-[#121216] p-3 rounded-lg border border-white/[0.06]">
                  <span className="text-zinc-500 block text-[10px] uppercase font-medium">Invoice / Ref #</span>
                  <strong className="text-zinc-100 text-xs mt-0.5 block font-mono">
                    {businessExtraction.document_reference_number || 'N/A'}
                  </strong>
                </div>
                <div className="bg-[#121216] p-3 rounded-lg border border-white/[0.06]">
                  <span className="text-zinc-500 block text-[10px] uppercase font-medium">Financial Total</span>
                  <strong className="text-red-400 text-xs mt-0.5 block font-mono tabular-nums">
                    {businessExtraction.financial_total !== undefined &&
                      businessExtraction.financial_total !== null
                      ? `$${businessExtraction.financial_total.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                      : 'N/A'}
                  </strong>
                </div>
                <div className="bg-[#121216] p-3 rounded-lg border border-white/[0.06]">
                  <span className="text-zinc-500 block text-[10px] uppercase font-medium">Due Date</span>
                  <strong className="text-zinc-100 text-xs mt-0.5 block font-mono tabular-nums">
                    {businessExtraction.due_or_expiration_date
                      ? new Date(businessExtraction.due_or_expiration_date).toLocaleDateString()
                      : 'N/A'}
                  </strong>
                </div>
              </div>

              {/* Raw JSON Details */}
              <div>
                <span className="text-zinc-500 text-[10px] font-medium uppercase tracking-wider block mb-1">
                  Extracted Payload Attributes
                </span>
                <pre className="bg-[#08080a] p-3 rounded-lg border border-white/[0.05] font-mono text-[11px] text-zinc-300 overflow-x-auto leading-relaxed">
                  {JSON.stringify(businessExtraction.extracted_data, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
