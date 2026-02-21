import React, { useState } from 'react';
import { Upload, FileText } from 'lucide-react';

export function UploadZone({ onUploadComplete }) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = async (file) => {
    setUploading(true);
    setError(null);
    setProgress(20);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setProgress(40);
      
      pollForCompletion(data.session_id, data.file_name);
    } catch (err) {
      setError(err.message);
      setUploading(false);
      setProgress(0);
    }
  };

  const pollForCompletion = async (sessionId, fileName) => {
    const maxAttempts = 120;
    let attempts = 0;

    const poll = async () => {
      attempts++;
      try {
        const response = await fetch(`/api/session/${sessionId}`);
        const data = await response.json();

        if (data.processed_flag) {
          setProgress(100);
          setUploading(false);
          onUploadComplete(sessionId, fileName);
        } else if (attempts < maxAttempts) {
          setProgress(40 + (attempts / maxAttempts) * 50);
          setTimeout(poll, 2000);
        } else {
          setError('Processing timeout');
          setUploading(false);
          setProgress(0);
        }
      } catch (err) {
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        } else {
          setError('Failed to check processing status');
          setUploading(false);
          setProgress(0);
        }
      }
    };

    poll();
  };

  return (
    <div className="h-full flex flex-col">
      <div
        className={`flex-1 border-2 border-dashed rounded-xl p-8 text-center transition ${
          isDragActive
            ? 'border-crimson-400 bg-crimson-500/5'
            : 'border-slate-600 bg-slate-700/50 hover:border-slate-500'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="mb-4 flex justify-center">
          <div className={`p-3 rounded-lg transition ${isDragActive ? 'bg-crimson-500/20' : 'bg-slate-600/50'}`}>
            <Upload className={`w-8 h-8 transition ${isDragActive ? 'text-crimson-400' : 'text-slate-400'}`} />
          </div>
        </div>
        <p className="text-lg font-semibold text-slate-100 mb-2">
          Drop your PDF here
        </p>
        <p className="text-sm text-slate-400 mb-4">
          Financial aid letters, lease agreements, visa documents
        </p>
        <p className="text-sm text-slate-500 mb-6">
          or{' '}
          <label className="text-crimson-400 hover:text-crimson-300 font-medium cursor-pointer">
            browse to select
            <input
              type="file"
              className="hidden"
              onChange={handleFileChange}
              accept=".pdf"
              disabled={uploading}
            />
          </label>
        </p>
        <p className="text-xs text-slate-500">Maximum 50MB</p>

        {uploading && (
          <div className="mt-6 space-y-3">
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-crimson-500 to-coral-500 h-2 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p className="text-sm font-medium text-slate-300">
              Processing {Math.round(progress)}%
            </p>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
