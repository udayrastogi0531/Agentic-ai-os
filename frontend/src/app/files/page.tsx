"use client";

/**
 * Uday AI — Files & RAG Document Page
 *
 * Premium interface for document upload, management, and interactive Q&A.
 */

import { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import useAuth from "@/hooks/useAuth";
import api from "@/lib/api";
import type { UploadedFile } from "@/types";

export default function FilesPage() {
  useAuth(); // Require authentication
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Selected file for Q&A panel
  const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);

  // Load files
  const fetchFiles = async () => {
    try {
      const response = (await api.getFiles()) as { files: UploadedFile[] };
      setFiles(response.files || []);
    } catch (err) {
      console.error("Failed to load files:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  // Handle Upload
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (!fileList || fileList.length === 0) return;

    const file = fileList[0];
    setIsUploading(true);
    setUploadError("");

    try {
      await api.uploadFile(file);
      await fetchFiles();
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Failed to upload file");
    } finally {
      setIsUploading(false);
    }
  };

  // Handle Delete
  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this file? This will remove its index from long-term memory.")) return;

    try {
      await api.deleteFile(id);
      if (selectedFile?.id === id) {
        setSelectedFile(null);
        setAnswer("");
      }
      await fetchFiles();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete file");
    }
  };

  // Handle Query
  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !question.trim() || isQuerying) return;

    setIsQuerying(true);
    setAnswer("");

    try {
      const result = (await api.queryFile(selectedFile.id, question)) as {
        answer: string;
      };
      setAnswer(result.answer);
    } catch (err) {
      setAnswer(`❌ Error: ${err instanceof Error ? err.message : "Failed to query document"}`);
    } finally {
      setIsQuerying(false);
    }
  };

  // Format file size
  const formatBytes = (bytes: number, decimals = 2) => {
    if (!+bytes) return "0 Bytes";
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
  };

  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
      <Sidebar />
      <main className="flex-1 flex" style={{ marginLeft: "var(--sidebar-width)" }}>
        {/* Main Panel */}
        <div className="flex-1 flex flex-col min-w-0 border-r border-[var(--border-color)]">
          <header className="sticky top-0 z-30 glass-strong px-8 py-5 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border-color)" }}>
            <div>
              <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>📁 Files & Documents</h1>
              <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>Upload documents and ask questions about them</p>
            </div>
            <div>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-white transition-all duration-200 hover:scale-105"
                style={{
                  background: "var(--gradient-primary)",
                  cursor: isUploading ? "not-allowed" : "pointer",
                }}
              >
                {isUploading ? "Uploading..." : "📤 Upload File"}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg"
                onChange={handleUpload}
              />
            </div>
          </header>

          <div className="px-8 py-6 space-y-6 overflow-y-auto flex-1">
            {uploadError && (
              <div className="p-4 rounded-xl text-sm border flex items-center gap-2" style={{ background: "rgba(239, 68, 68, 0.1)", borderColor: "var(--error)", color: "var(--error)" }}>
                ⚠️ {uploadError}
              </div>
            )}

            {/* Supported Types */}
            <div className="flex gap-3">
              {["PDF", "DOCX", "TXT", "MD", "Images"].map((type) => (
                <span key={type} className="px-3 py-1.5 rounded-lg text-xs font-medium" style={{ background: "var(--bg-tertiary)", color: "var(--text-secondary)" }}>
                  {type}
                </span>
              ))}
            </div>

            {/* Drop Zone / Empty state if no files */}
            {files.length === 0 ? (
              <div
                className="flex flex-col items-center justify-center py-20 rounded-2xl border-2 border-dashed transition-all duration-200 cursor-pointer"
                style={{ borderColor: "var(--border-color)", background: "var(--bg-card)" }}
                onClick={() => fileInputRef.current?.click()}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-color)"; }}
              >
                <span className="text-5xl mb-4">📄</span>
                <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>Drop files here or click to upload</h3>
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>PDF, DOCX, TXT, Markdown, or Images up to 50MB</p>
                <p className="text-xs mt-4" style={{ color: "var(--text-muted)" }}>Files are processed and embedded for intelligent Q&A</p>
              </div>
            ) : (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>Your Documents ({files.length})</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {files.map((file) => {
                    const isSelected = selectedFile?.id === file.id;
                    return (
                      <div
                        key={file.id}
                        onClick={() => {
                          setSelectedFile(file);
                          setAnswer("");
                          setQuestion("");
                        }}
                        className="p-5 rounded-2xl transition-all duration-200 border cursor-pointer flex flex-col justify-between hover:scale-[1.02]"
                        style={{
                          background: isSelected ? "var(--bg-hover)" : "var(--bg-card)",
                          borderColor: isSelected ? "var(--accent-primary)" : "var(--border-color)",
                        }}
                      >
                        <div>
                          <div className="flex items-start justify-between mb-3">
                            <span className="text-2xl">
                              {file.file_type === "pdf" ? "📕" : file.file_type === "docx" ? "📘" : "📄"}
                            </span>
                            <div className="flex gap-1">
                              <button
                                onClick={async (e) => {
                                  e.stopPropagation();
                                  try {
                                    await api.downloadFile(file.id, file.original_filename);
                                  } catch (err) {
                                    alert(err instanceof Error ? err.message : "Download failed");
                                  }
                                }}
                                className="p-1 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors text-sm"
                                title="Download File"
                              >
                                📥
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDelete(file.id);
                                }}
                                className="p-1 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors"
                                style={{ color: "var(--error)" }}
                                title="Delete File"
                              >
                                🗑️
                              </button>
                            </div>
                          </div>
                          <h3 className="text-sm font-semibold truncate max-w-xs" style={{ color: "var(--text-primary)" }}>
                            {file.original_filename}
                          </h3>
                          <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                            Size: {formatBytes(file.file_size)} • Chunks: {file.chunk_count}
                          </p>
                        </div>
                        <div className="flex items-center justify-between mt-4">
                          <span
                            className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold"
                            style={{
                              background: file.status === "ready" ? "rgba(16,185,129,0.15)" : "rgba(245,158,11,0.15)",
                              color: file.status === "ready" ? "var(--success)" : "var(--warning)",
                            }}
                          >
                            {file.status}
                          </span>
                          <span className="text-xs font-semibold" style={{ color: "var(--accent-primary)" }}>
                            Ask questions →
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Selected Document Q&A Sidebar */}
        <div
          className={`transition-all duration-300 overflow-hidden flex flex-col glass-strong ${
            selectedFile ? "w-[400px]" : "w-0"
          }`}
        >
          {selectedFile && (
            <div className="flex flex-col h-full w-[400px]">
              <header className="px-6 py-5 border-b border-[var(--border-color)] flex items-center justify-between">
                <div>
                  <h3 className="font-bold truncate max-w-[280px]" style={{ color: "var(--text-primary)" }}>
                    {selectedFile.original_filename}
                  </h3>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>Interactive RAG Q&A</p>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="p-1 hover:bg-[var(--bg-hover)] rounded-lg text-lg"
                  style={{ color: "var(--text-secondary)" }}
                >
                  ✕
                </button>
              </header>

              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {answer ? (
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                      Response
                    </h4>
                    <div
                      className="p-4 rounded-xl text-sm border prose whitespace-pre-wrap"
                      style={{
                        background: "var(--bg-card)",
                        borderColor: "var(--border-color)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {answer}
                    </div>
                    <button
                      onClick={() => setAnswer("")}
                      className="text-xs font-semibold transition-all"
                      style={{ color: "var(--accent-primary)" }}
                    >
                      ← Ask another question
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <span className="text-4xl mb-4">💬</span>
                    <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                      Ask me any question about the contents of this document.
                    </p>
                  </div>
                )}
              </div>

              {/* Input section */}
              <div className="p-4 border-t border-[var(--border-color)]" style={{ background: "var(--bg-secondary)" }}>
                <form onSubmit={handleQuery} className="flex gap-2">
                  <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask Uday AI..."
                    disabled={isQuerying}
                    className="flex-1 rounded-xl px-4 py-2.5 text-sm outline-none"
                    style={{
                      background: "var(--bg-tertiary)",
                      border: "1px solid var(--border-color)",
                      color: "var(--text-primary)",
                    }}
                  />
                  <button
                    type="submit"
                    disabled={!question.trim() || isQuerying}
                    className="px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition-all"
                    style={{
                      background: "var(--gradient-primary)",
                      opacity: question.trim() && !isQuerying ? 1 : 0.5,
                      cursor: question.trim() && !isQuerying ? "pointer" : "not-allowed",
                    }}
                  >
                    {isQuerying ? "..." : "Send"}
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
