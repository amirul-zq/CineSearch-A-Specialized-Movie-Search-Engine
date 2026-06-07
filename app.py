import time
from flask import Flask, render_template, request, jsonify
from search_engine import InvertedIndex, SnippetGenerator

app = Flask(__name__)

# Initialize Inverted Index at startup
dataset_path = "movies_dataset.json"
index = InvertedIndex(dataset_path)
snippet_gen = SnippetGenerator(index.preprocessor.stemmer)

@app.route("/")
def index_page():
    return render_template("index.html")

@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    mode = request.args.get("mode", "ranked").lower()
    
    if not query:
        return jsonify({
            "query": query,
            "mode": mode,
            "results_count": 0,
            "time_ms": 0,
            "results": []
        })

    # Start timing
    start_time = time.perf_counter()
    
    if mode == "boolean":
        results = index.search_boolean(query)
    else:
        results = index.search_ranked(query)
        
    end_time = time.perf_counter()
    time_ms = round((end_time - start_time) * 1000, 2)
    
    # Process results and generate snippets
    processed_results = []
    # Query words for snippet generation
    query_words = index.preprocessor.tokenize(query)
    # Exclude logic operators from highlighting in snippet
    query_words = [w for w in query_words if w.upper() not in ("AND", "OR", "NOT")]
    
    for r in results:
        movie = r["movie"]
        snippet = snippet_gen.generate_snippet(movie["plot"], query_words)
        
        processed_results.append({
            "id": movie["id"],
            "title": movie["title"],
            "director": movie["director"],
            "year": movie["year"],
            "genres": movie["genres"],
            "rating": movie["rating"],
            "cast": movie["cast"],
            "score": r["score"],
            "matched_terms": r["matched_terms"],
            "snippet": snippet
        })
        
    return jsonify({
        "query": query,
        "mode": mode,
        "results_count": len(processed_results),
        "time_ms": time_ms,
        "results": processed_results
    })

@app.route("/api/index-debug")
def api_index_debug():
    word = request.args.get("word", "").strip()
    if not word:
        return jsonify({
            "word": word,
            "stemmed": "",
            "postings": []
        })
        
    details = index.get_postings_details(word)
    return jsonify({
        "word": word,
        "stemmed": details["stemmed"],
        "postings": details["postings"]
    })

@app.route("/api/stats")
def api_stats():
    # Calculate index metrics
    total_docs = len(index.movies)
    vocab_size = len(index.index)
    
    # Count postings: sum of doc entries across all vocabulary terms
    total_postings = sum(len(postings) for postings in index.index.values())
    
    return jsonify({
        "total_documents": total_docs,
        "vocab_size": vocab_size,
        "total_postings": total_postings
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
