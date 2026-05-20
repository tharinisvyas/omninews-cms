import { useState, useEffect } from 'react';

function App() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch data from your local Flask backend
    fetch('http://127.0.0.1:5001/api/news')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch data');
        return res.json();
      })
      .then((data) => {
        // Safe check to ensure we always have an array for .map()
        let fetchedArticles = [];
        if (data && Array.isArray(data.articles)) {
            fetchedArticles = data.articles;
        } else if (Array.isArray(data)) {
            fetchedArticles = data;
        }
        setArticles(fetchedArticles);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const handlePublish = (e) => {
    alert("Article published to live feed!");
    e.target.innerText = "✓ Published";
    e.target.disabled = true;
    e.target.className = "mt-4 bg-gray-500 text-white font-bold py-2 px-6 rounded-lg cursor-not-allowed w-full shadow-inner";
  };

  // Safe Render Helper: Prevents crashes if AI sends objects instead of strings
  const renderContent = (content) => {
      if (!content) return "No content generated.";
      if (typeof content === 'string') return <li>{content}</li>;
      if (Array.isArray(content)) {
          return content.map((item, i) => (
              <li key={i}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
          ));
      }
      return <li>{JSON.stringify(content)}</li>;
  };

  return (
    <div className="flex h-screen bg-gray-100 font-sans">
      {/* Sidebar */}
      <div className="w-64 bg-slate-900 text-white p-6 shadow-lg fixed h-full z-10">
        <h1 className="text-2xl font-bold mb-8 tracking-tight">OmniNews Agentic CMS</h1>
        <nav className="space-y-4">
          <a href="#" className="block text-slate-300 hover:text-white transition">Live Feed</a>
          <a href="#" className="block text-blue-400 font-semibold">Curation Queue</a>
          <a href="#" className="block text-slate-300 hover:text-white transition">Published</a>
        </nav>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 ml-64 p-8 overflow-y-auto">
        <h2 className="text-3xl font-bold text-gray-800 mb-6">Pending Curation</h2>

        {loading && <p className="text-lg text-blue-600 font-semibold animate-pulse">AI Agent is processing live news...</p>}
        {error && <p className="text-lg text-red-600 font-semibold p-4 bg-red-50 rounded-lg border border-red-200">Error: {error}</p>}

        <div className="space-y-8">
          {articles.map((article, index) => (
            <div key={index} className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-200 p-6 flex flex-col md:flex-row gap-6">
              
              {/* Left Column: Raw Data */}
              <div className="md:w-1/3 border-b md:border-b-0 md:border-r border-gray-200 pb-6 md:pb-0 md:pr-6">
                <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                  {article.source?.name || article.source || 'News Feed'}
                </span>
                <h3 className="text-xl font-bold mt-2 mb-4 text-gray-900 leading-tight">
                  {article.title || 'Untitled Article'}
                </h3>
                {article.imageUrl && (
                  <img src={article.imageUrl} alt="News thumbnail" className="w-full h-40 object-cover rounded-lg mb-4 shadow-sm" />
                )}
                <button
                  onClick={handlePublish}
                  className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg transition duration-200 shadow-md w-full"
                >
                  Approve & Publish
                </button>
              </div>

              {/* Right Column: AI Liquid Content */}
              <div className="md:w-2/3 space-y-4">
                {article.liquid_content ? (
                  <>
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                      <h4 className="font-bold text-blue-900 mb-2">AI Executive Summary</h4>
                      <ul className="list-disc pl-5 text-gray-800 space-y-1 text-sm">
                        {renderContent(article.liquid_content.executive_summary)}
                      </ul>
                    </div>

                    <div className="bg-amber-50 p-4 rounded-lg border border-amber-100">
                      <h4 className="font-bold text-amber-900 mb-2">Event Timeline</h4>
                      <ul className="list-decimal pl-5 text-gray-800 space-y-1 text-sm">
                        {renderContent(article.liquid_content.timeline)}
                      </ul>
                    </div>

                    <div className="bg-purple-50 p-4 rounded-lg border border-purple-100">
                      <h4 className="font-bold text-purple-900 mb-2">Suggested Social Hook</h4>
                      <p className="text-gray-800 italic text-sm">
                        "{typeof article.liquid_content.social_caption === 'string' 
                          ? article.liquid_content.social_caption 
                          : JSON.stringify(article.liquid_content.social_caption)}"
                      </p>
                    </div>
                  </>
                ) : (
                  <div className="h-full flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200 border-dashed p-6">
                    <p className="text-gray-500 italic">No AI Liquid Content generated for this article.</p>
                  </div>
                )}
              </div>

            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;