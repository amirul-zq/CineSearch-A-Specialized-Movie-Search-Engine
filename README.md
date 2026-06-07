# CineSearch - Specialized Movie Search Engine

CineSearch is a custom-built, specialized academic search engine designed to index and search movie metadata. Built entirely from scratch in Python, it implements standard information retrieval concepts without relying on high-level pre-built search libraries like Elasticsearch, Whoosh, or Lucene. 

It satisfies all core requirements of the Specialized Search Engine assignment and includes a premium, interactive web interface.
---

## Features

1. **Custom Inverted Index:**
   * Indexes a database of 65 popular movies.
   * Maps terms to document IDs, frequencies, and specific word offset positions.
   * Supports multi-field indexing (`title`, `plot`, `genres`, `director`, and `cast`) with customizable field weight boosting (e.g., matching a term in the `title` carries more weight than matching it in the `plot`).

2. **Custom Text Preprocessing Pipeline:**
   * Removes punctuation while intelligently preserving word hyphens and apostrophes (essential for terms like `sci-fi` or `director's`).
   * Eliminates common English stopwords using a curated dictionary list.
   * Implements a custom, rule-based English word stemmer (`CustomStemmer`) to reduce terms to their base forms (e.g., mapping `travels` and `traveling` to `travel`).

3. **Ranked Vector Space Model Retrieval:**
   * Compares document and query vectors using **Cosine Similarity**.
   * Computes Term Frequency (TF) using log weighting: $1 + \log(\text{tf})$.
   * Computes Inverse Document Frequency (IDF) using log normalization: $\log(1 + N/\text{df})$.
   * Employs document length normalization vectors to correct bias toward longer documents.

4. **Boolean Retrieval Engine:**
   * Processes set-based query execution for terms combined with `AND`, `OR`, and `NOT` operators.
   * Implements standard operator precedence: `NOT` has highest precedence, followed by `AND`, then `OR` (e.g., `nolan AND NOT sci-fi`).

5. **Dynamic Snippet Generation & Highlighting:**
   * Scans the document's plot description and extracts the sentence that contains the highest concentration of query terms.
   * Dynamically wraps matched terms (including stemmed equivalents) in HTML `<mark>` tags for visual highlighting.

6. **Cinematic Web Interface (Bonus Section ⭐):**
   * Premium, responsive dark-themed visual design with glassmorphic cards and smooth animations.
   * **Live Stats Board:** Displays index size metrics (Total Documents, Vocabulary Size, and Total Postings) dynamically fetched from the engine.
   * **Search Portal:** Toggleable modes between Ranked TF-IDF and Boolean Search with search suggestions, query metadata (execution time, document counts, cosine scores), and pop-up details modals.
   * **Inverted Index Explorer:** Academic panel allowing users to inspect the internal postings data structure. Querying any word displays its root stem, document frequency, and an interactive table of doc IDs, term frequencies, and exact word offset positions per field.

---

## Project Structure

```text
search_engine/
├── app.py                  # Flask web server & API controller
├── search_engine.py        # Custom preprocessor, indexer, ranker, and snippet highlighter
├── movies_dataset.json     # Curated JSON movie dataset (65 documents)
├── README.md               # Project documentation
├── templates/
│   └── index.html          # Frontend page structure (HTML5)
└── static/
    ├── style.css           # Styling tokens, cinematic dark mode, and layout
    └── app.js              # Single-page application logic, fetch calls, and modal triggers
```

---

## Installation & Running Locally

### Prerequisites
* Python 3.8 or higher
* Flask (`pip install Flask`)

### Running the Server
1. Clone the repository or navigate to the folder.
2. Ensure Flask is installed:
   ```bash
   pip install Flask
   ```
3. Start the Flask application:
   ```bash
   python app.py
   ```
4. Open your web browser and navigate to:
   ```text
   http://127.0.0.1:5000
   ```

---

## API Endpoints Reference

### 1. Execute Search Query
* **Endpoint:** `/api/search`
* **Method:** `GET`
* **Parameters:**
  * `q` (string, required): The search query text.
  * `mode` (string, optional): Search mode, either `ranked` (default) or `boolean`.
* **Example:** `/api/search?q=space&mode=ranked`

### 2. Inspect Inverted Index Postings
* **Endpoint:** `/api/index-debug`
* **Method:** `GET`
* **Parameters:**
  * `word` (string, required): Word to search in the index dictionary.
* **Example:** `/api/index-debug?word=dream`

### 3. Retrieve Index Metrics
* **Endpoint:** `/api/stats`
* **Method:** `GET`
* **Response Format:**
  ```json
  {
    "total_documents": 65,
    "vocab_size": 1153,
    "total_postings": 1858
  }
  ```
