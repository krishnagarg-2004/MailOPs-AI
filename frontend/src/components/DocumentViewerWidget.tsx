import React, { useState } from 'react';
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

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4 text-slate-100 font-sans">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Document Intelligence</span>
          <span className="text-xs font-mono font-semibold bg-slate-800 px-2.5 py-0.5 rounded text-slate-200">
            {filename}
          </span>
          {extraction?.is_ocr_applied ? (
            <span className="text-[10px] bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded font-medium">
              OCR (Tesseract)
            </span>
          ) : extraction ? (
            <span className="text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded font-medium">
              Native Text
            </span>
          ) : null}
        </div>

        <div className="flex items-center gap-2">
          {!extraction && (
            <button
              onClick={onTriggerProcess}
              className="text-xs bg-purple-600/20 text-purple-300 border border-purple-500/40 px-3 py-1 rounded hover:bg-purple-600/30 transition font-medium"
            >
              Extract Text & OCR
            </button>
          )}
          {extraction && !businessExtraction && (
            <button
              onClick={onTriggerBusinessAnalysis}
              className="text-xs bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 px-3 py-1 rounded hover:bg-indigo-600/30 transition font-medium"
            >
              Analyze Business Metadata
            </button>
          )}
        </div>
      </div>

      {/* Status Warning if Failed */}
      {extraction?.status === 'FAILED' && (
        <div className="bg-red-950/60 border border-red-800/80 rounded-lg p-3 text-xs text-red-300">
          <strong>Extraction Error:</strong> {extraction.error_message || 'Document processing failed.'}
        </div>
      )}

      {/* Tabs */}
      {extraction && (
        <>
          <div className="flex items-center gap-4 text-xs border-b border-slate-800">
            <button
              onClick={() => setActiveTab('text')}
              className={`pb-2 border-b-2 font-medium transition ${
                activeTab === 'text'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Extracted Text ({extraction.char_count} chars
              {extraction.page_count ? `, ${extraction.page_count} pages` : ''})
            </button>

            {businessExtraction && (
              <button
                onClick={() => setActiveTab('business')}
                className={`pb-2 border-b-2 font-medium transition ${
                  activeTab === 'business'
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Structured Business Metadata ({businessExtraction.document_category})
              </button>
            )}
          </div>

          {/* Tab Content: Extracted Text */}
          {activeTab === 'text' && (
            <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 max-h-72 overflow-y-auto font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
              {extraction.extracted_text || 'No text extracted.'}
            </div>
          )}

          {/* Tab Content: Business Metadata */}
          {activeTab === 'business' && businessExtraction && (
            <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 pb-3 border-b border-slate-900">
                <div>
                  <span className="text-slate-400 block text-[11px]">Vendor / Contracting Party</span>
                  <strong className="text-slate-200 text-sm">
                    {businessExtraction.vendor_or_party || 'N/A'}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Reference / Invoice #</span>
                  <strong className="text-slate-200 text-sm">
                    {businessExtraction.document_reference_number || 'N/A'}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Financial Total</span>
                  <strong className="text-emerald-400 text-sm">
                    {businessExtraction.financial_total !== undefined && businessExtraction.financial_total !== null
                      ? `$${businessExtraction.financial_total.toLocaleString()}`
                      : 'N/A'}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Due / Expiration Date</span>
                  <strong className="text-amber-400 text-sm">
                    {businessExtraction.due_or_expiration_date
                      ? new Date(businessExtraction.due_or_expiration_date).toLocaleDateString()
                      : 'N/A'}
                  </strong>
                </div>
              </div>

              {/* Raw JSON Details */}
              <div>
                <span className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider block mb-1">
                  Extracted Payload Attributes
                </span>
                <pre className="bg-slate-900 p-3 rounded font-mono text-[11px] text-slate-300 overflow-x-auto">
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
