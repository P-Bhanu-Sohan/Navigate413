import React, { useState } from 'react';

export function TranslationPanel({ sessionId }) {
  const [language, setLanguage] = useState('en');
  const [translation, setTranslation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleTranslate = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          target_language: language
        })
      });

      if (!response.ok) {
        throw new Error('Translation failed');
      }

      const data = await response.json();
      setTranslation(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'zh', name: 'Mandarin' },
    { code: 'hi', name: 'Hindi' }
  ];

  return (
    <div className="card">
      <h3 className="text-xl font-bold mb-4">Translation</h3>
      
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Target Language
        </label>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          disabled={loading}
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring focus:ring-blue-200"
        >
          {languages.map(lang => (
            <option key={lang.code} value={lang.code}>
              {lang.name}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={handleTranslate}
        disabled={loading || language === 'en'}
        className="btn-primary w-full mb-4"
      >
        {loading ? 'Translating...' : 'Translate'}
      </button>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm mb-4">
          {error}
        </div>
      )}

      {translation && language !== 'en' && (
        <div className="p-4 bg-green-50 border border-green-200 rounded">
          <p className="text-xs text-gray-600 mb-2">
            <strong>Translated to {translation.language}:</strong>
          </p>
          <p className="text-sm text-gray-700">
            {translation.translated_text}
          </p>
          <p className="text-xs text-gray-500 mt-2 italic">
            {translation.context_note}
          </p>
        </div>
      )}

      {language === 'en' && (
        <div className="p-3 bg-gray-50 border border-gray-200 rounded text-gray-600 text-sm">
          English is the original language. Select another language to translate.
        </div>
      )}
    </div>
  );
}
