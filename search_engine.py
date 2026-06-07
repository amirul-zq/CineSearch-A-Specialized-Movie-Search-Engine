import json
import re
import math
import os

class CustomStemmer:
    """
    A custom rule-based stemmer to reduce words to their base form.
    Implemented from scratch to avoid external dependencies like NLTK/spaCy.
    """
    def __init__(self):
        # Common vowel check
        self.vowels = set("aeiouy")

    def _contains_vowel(self, word):
        return any(char in self.vowels for char in word)

    def stem(self, word):
        word = word.lower().strip()
        if len(word) <= 2:
            return word

        # 1. Plurals
        if word.endswith('sses'):
            word = word[:-2]
        elif word.endswith('ies'):
            word = word[:-3] + 'y'
        elif word.endswith('ss'):
            pass
        elif word.endswith('s'):
            # Don't strip if it ends in 'us', 'is', 'as' to protect words like 'bus', 'analysis'
            if not (word.endswith('us') or word.endswith('is') or word.endswith('as')):
                word = word[:-1]

        # 2. Participles and past tense
        if word.endswith('eed'):
            # e.g., agreed -> agree
            word = word[:-1]
        elif word.endswith('ing'):
            stem = word[:-3]
            if self._contains_vowel(stem):
                word = stem
                if word.endswith('at') or word.endswith('bl') or word.endswith('iz'):
                    word += 'e'
        elif word.endswith('ed'):
            stem = word[:-2]
            if self._contains_vowel(stem):
                word = stem
                if word.endswith('at') or word.endswith('bl') or word.endswith('iz'):
                    word += 'e'

        # 3. Adverbs
        if word.endswith('ly'):
            stem = word[:-2]
            if len(stem) > 2 and self._contains_vowel(stem):
                word = stem

        # 4. Standard suffixes
        if word.endswith('ation'):
            word = word[:-5] + 'ate'
        elif word.endswith('tional'):
            word = word[:-2]
        elif word.endswith('ment'):
            word = word[:-4]
        elif word.endswith('ness'):
            word = word[:-4]
        elif word.endswith('ful'):
            word = word[:-3]
        elif word.endswith('ive'):
            stem = word[:-3]
            if len(stem) > 2:
                word = stem + 'ive'

        return word


class TextPreprocessor:
    """
    Handles text cleaning, tokenization, stopword removal, and stemming.
    """
    def __init__(self):
        self.stemmer = CustomStemmer()
        # Curated list of common English stopwords
        self.stopwords = {
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
            "arent", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", 
            "but", "by", "cant", "cannot", "could", "couldnt", "did", "didnt", "do", "does", "doesnt", 
            "doing", "dont", "down", "during", "each", "few", "for", "from", "further", "had", "hadnt", 
            "has", "hasnt", "have", "havent", "having", "he", "hed", "hell", "hes", "her", "here", 
            "heres", "hers", "herself", "him", "himself", "his", "how", "hows", "i", "id", "ill", "im", 
            "ive", "if", "in", "into", "is", "isnt", "it", "its", "itself", "lets", "me", "more", "most", 
            "mustnt", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", 
            "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shant", "she", "shed", 
            "shell", "shes", "should", "shouldnt", "so", "some", "such", "than", "that", "thats", "the", 
            "their", "theirs", "them", "themselves", "then", "there", "theres", "these", "they", "theyd", 
            "theyll", "theyre", "theyve", "this", "those", "through", "to", "too", "under", "until", "up", 
            "very", "was", "wasnt", "we", "wed", "well", "were", "weve", "werent", "what", "whats", "when", 
            "whens", "where", "wheres", "which", "while", "who", "whos", "whom", "why", "whys", "with", 
            "wont", "would", "wouldnt", "you", "youd", "youll", "youre", "youve", "your", "yours", 
            "yourself", "yourselves"
        }

    def clean_text(self, text):
        """Removes punctuation and normalizes whitespace, preserving hyphens and apostrophes."""
        if not text:
            return ""
        # Remove punctuation, keep letters, numbers, hyphens, and apostrophes
        text = re.sub(r"[^\w\s\-']", ' ', text)
        return text.lower()

    def tokenize(self, text):
        """Splits clean text into individual tokens."""
        return self.clean_text(text).split()

    def preprocess(self, text):
        """Cleans, tokenizes, removes stopwords, and stems tokens."""
        tokens = self.tokenize(text)
        processed = []
        for t in tokens:
            if t not in self.stopwords and not t.isdigit():
                stemmed = self.stemmer.stem(t)
                if len(stemmed) > 1:
                    processed.append(stemmed)
        return processed


class InvertedIndex:
    """
    Inverted Index implementation.
    Maps term -> { doc_id: { field_name: [positions] } }
    """
    def __init__(self, movies_filepath):
        self.preprocessor = TextPreprocessor()
        self.movies = {}
        self.index = {}  # term -> { doc_id: { field: [positions] } }
        self.doc_lengths = {}  # doc_id -> vector_length
        self.field_weights = {
            "title": 3.0,
            "director": 2.0,
            "genres": 1.5,
            "cast": 1.5,
            "plot": 1.0
        }
        
        self.load_dataset(movies_filepath)
        self.build_index()
        self.precompute_doc_lengths()

    def load_dataset(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Dataset file not found at {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for m in data:
                self.movies[m['id']] = m

    def build_index(self):
        """Constructs the inverted index from the movie dataset."""
        self.index.clear()
        
        for doc_id, movie in self.movies.items():
            # Process each field
            for field, weight in self.field_weights.items():
                val = movie.get(field, "")
                if isinstance(val, list):
                    # For list fields like genres or cast, join them with spaces
                    text = " ".join(val)
                elif isinstance(val, int):
                    text = str(val)
                else:
                    text = val
                
                # Tokenize and preprocess
                tokens = self.preprocessor.preprocess(text)
                
                # Insert tokens into the inverted index
                for pos, term in enumerate(tokens):
                    if term not in self.index:
                        self.index[term] = {}
                    if doc_id not in self.index[term]:
                        self.index[term][doc_id] = {}
                    if field not in self.index[term][doc_id]:
                        self.index[term][doc_id][field] = []
                    
                    self.index[term][doc_id][field].append(pos)

    def get_term_doc_tf(self, term, doc_id):
        """
        Calculates the weighted term frequency of a term in a document.
        tf(t, d) = sum(count(t, d, f) * weight(f))
        """
        if term not in self.index or doc_id not in self.index[term]:
            return 0.0
        
        tf = 0.0
        fields_data = self.index[term][doc_id]
        for field, positions in fields_data.items():
            count = len(positions)
            weight = self.field_weights.get(field, 1.0)
            tf += count * weight
            
        return tf

    def get_doc_frequency(self, term):
        """Returns the number of documents containing the term."""
        if term not in self.index:
            return 0
        return len(self.index[term])

    def get_idf(self, term):
        """
        Calculates IDF: log(1 + N / df)
        """
        N = len(self.movies)
        df = self.get_doc_frequency(term)
        if df == 0:
            return 0.0
        return math.log(1 + (N / df))

    def precompute_doc_lengths(self):
        """Precomputes the Euclidean length of each document vector for cosine normalization."""
        self.doc_lengths.clear()
        
        # Aggregate all terms for each document
        all_doc_terms = {} # doc_id -> set of terms
        for term, postings in self.index.items():
            for doc_id in postings:
                if doc_id not in all_doc_terms:
                    all_doc_terms[doc_id] = set()
                all_doc_terms[doc_id].add(term)
        
        for doc_id in self.movies:
            length_sq = 0.0
            terms = all_doc_terms.get(doc_id, set())
            for term in terms:
                tf = self.get_term_doc_tf(term, doc_id)
                if tf > 0:
                    tf_weight = 1.0 + math.log(tf)
                    idf = self.get_idf(term)
                    length_sq += (tf_weight * idf) ** 2
            self.doc_lengths[doc_id] = math.sqrt(length_sq) if length_sq > 0 else 1.0

    def search_ranked(self, query_str):
        """
        Performs ranked retrieval using vector space model with TF-IDF cosine similarity.
        """
        query_terms = self.preprocessor.preprocess(query_str)
        if not query_terms:
            return []

        # Build query vector
        query_tf = {}
        for term in query_terms:
            query_tf[term] = query_tf.get(term, 0) + 1

        query_vector = {}
        query_length_sq = 0.0
        for term, freq in query_tf.items():
            # TF-IDF of query term
            tf_w = 1.0 + math.log(freq)
            idf = self.get_idf(term)
            val = tf_w * idf
            query_vector[term] = val
            query_length_sq += val ** 2
        
        query_length = math.sqrt(query_length_sq)
        if query_length == 0:
            return []

        # Compute dot product for candidate documents
        scores = {}  # doc_id -> dot_product
        matching_terms_in_doc = {} # doc_id -> list of matched terms (for UI)
        
        for term in query_vector:
            if term not in self.index:
                continue
            
            idf = self.get_idf(term)
            q_val = query_vector[term]
            
            for doc_id in self.index[term]:
                tf = self.get_term_doc_tf(term, doc_id)
                if tf > 0:
                    tf_w = 1.0 + math.log(tf)
                    doc_val = tf_w * idf
                    scores[doc_id] = scores.get(doc_id, 0.0) + (q_val * doc_val)
                    
                    if doc_id not in matching_terms_in_doc:
                        matching_terms_in_doc[doc_id] = []
                    matching_terms_in_doc[doc_id].append(term)

        # Normalize score to get Cosine Similarity
        results = []
        for doc_id, dot_product in scores.items():
            doc_len = self.doc_lengths.get(doc_id, 1.0)
            score = dot_product / (query_length * doc_len)
            
            # Map score to a readable value
            movie = self.movies[doc_id]
            results.append({
                "movie": movie,
                "score": round(score, 4),
                "matched_terms": matching_terms_in_doc[doc_id]
            })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def search_boolean(self, query_str):
        """
        Performs set-based Boolean retrieval for AND, OR, NOT operations.
        Supports complex queries like: "nolan AND space", "action OR drama", "nolan AND NOT sci-fi".
        Evaluates operators: NOT has highest precedence, then AND, then OR.
        """
        # Clean the query using the exact same preprocessor cleaning
        cleaned_query = self.preprocessor.clean_text(query_str)
        raw_tokens = cleaned_query.split()
        
        tokens = []
        for rt in raw_tokens:
            rt_upper = rt.upper()
            if rt_upper in ("AND", "OR", "NOT"):
                tokens.append(rt_upper)
            else:
                tokens.append(rt)
        
        if not tokens:
            return []

        # Helper to get matching doc IDs for a standard term (stemmed)
        def get_docs_for_term(term):
            stemmed = self.preprocessor.stemmer.stem(term)
            if stemmed in self.index:
                return set(self.index[stemmed].keys())
            return set()

        all_docs = set(self.movies.keys())

        # Step 1: Handle NOT operators (highest precedence)
        # Scan and replace 'NOT' + 'term' with the difference set
        i = 0
        while i < len(tokens):
            if tokens[i] == "NOT":
                if i + 1 < len(tokens):
                    next_token = tokens[i+1]
                    if isinstance(next_token, set):
                        result_set = all_docs - next_token
                    else:
                        result_set = all_docs - get_docs_for_term(next_token)
                    tokens[i] = result_set
                    del tokens[i+1]
                else:
                    # Trailing NOT is ignored/treated as term if invalid
                    tokens[i] = set()
            else:
                i += 1

        # Replace remaining raw word tokens with their document sets
        for idx, token in enumerate(tokens):
            if isinstance(token, str) and token not in ("AND", "OR"):
                tokens[idx] = get_docs_for_term(token)

        # Step 2: Handle AND operators (medium precedence)
        i = 0
        while i < len(tokens):
            if tokens[i] == "AND":
                if i - 1 >= 0 and i + 1 < len(tokens):
                    left = tokens[i-1]
                    right = tokens[i+1]
                    # Ensure they are sets
                    left_set = left if isinstance(left, set) else set()
                    right_set = right if isinstance(right, set) else set()
                    
                    tokens[i-1] = left_set.intersection(right_set)
                    del tokens[i:i+2]
                    i -= 1
                else:
                    # Invalid AND syntax
                    del tokens[i]
            else:
                i += 1

        # Step 3: Handle OR operators (lowest precedence)
        i = 0
        while i < len(tokens):
            if tokens[i] == "OR":
                if i - 1 >= 0 and i + 1 < len(tokens):
                    left = tokens[i-1]
                    right = tokens[i+1]
                    
                    left_set = left if isinstance(left, set) else set()
                    right_set = right if isinstance(right, set) else set()
                    
                    tokens[i-1] = left_set.union(right_set)
                    del tokens[i:i+2]
                    i -= 1
                else:
                    del tokens[i]
            else:
                i += 1

        # The final result is the union/intersection of whatever is left
        final_doc_ids = set()
        for token in tokens:
            if isinstance(token, set):
                final_doc_ids = final_doc_ids.union(token)

        # Build list of results
        results = []
        for doc_id in final_doc_ids:
            movie = self.movies[doc_id]
            # Since boolean search is binary, score is 1.0 (unranked match)
            results.append({
                "movie": movie,
                "score": 1.0,
                "matched_terms": []
            })
            
        return results

    def get_postings_details(self, word):
        """
        Returns debug postings list details for the index explorer UI.
        word -> list of { doc_id, doc_title, freq, positions, fields }
        """
        stemmed = self.preprocessor.stemmer.stem(word.lower().strip())
        if stemmed not in self.index:
            return {
                "stemmed": stemmed,
                "postings": []
            }
        
        postings = []
        doc_postings = self.index[stemmed]
        
        for doc_id, fields_data in doc_postings.items():
            movie = self.movies[doc_id]
            freq = sum(len(pos_list) for pos_list in fields_data.values())
            
            # Form field appearance list
            field_appearances = {}
            for field, pos_list in fields_data.items():
                field_appearances[field] = pos_list
                
            postings.append({
                "doc_id": doc_id,
                "title": movie["title"],
                "freq": freq,
                "fields": field_appearances
            })
            
        return {
            "stemmed": stemmed,
            "postings": sorted(postings, key=lambda x: x["freq"], reverse=True)
        }


class SnippetGenerator:
    """
    Generates sentence snippets from document plots with matching terms highlighted.
    """
    def __init__(self, stemmer):
        self.stemmer = stemmer

    def generate_snippet(self, plot, query_terms):
        """
        Extracts sentences containing the most query terms and highlights them.
        """
        if not plot:
            return ""

        # Preprocess query terms to standard stems
        stemmed_query_terms = {self.stemmer.stem(term) for term in query_terms}

        # Split plot into sentences (naive split on periods followed by space)
        sentences = re.split(r'\.\s+', plot)
        
        best_sentence = ""
        max_matches = -1
        
        for sentence in sentences:
            # Tokenize and stem sentence words
            words = re.findall(r'\b[\w\-\']+\b', sentence.lower())
            stemmed_words = {self.stemmer.stem(w) for w in words}
            
            # Count overlap
            matches = len(stemmed_words.intersection(stemmed_query_terms))
            if matches > max_matches:
                max_matches = matches
                best_sentence = sentence

        # If no sentence had matches or matches = 0, default to first sentence
        if max_matches <= 0:
            best_sentence = sentences[0]
        
        # Ensure sentence has a period if it originally had one
        best_sentence = best_sentence.strip()
        if not best_sentence.endswith('.'):
            best_sentence += '.'

        # Highlight matches
        highlighted = best_sentence
        
        # Find all words in the best sentence to highlight them
        words_in_sentence = re.findall(r'\b[\w\-\']+\b', best_sentence)
        
        # We replace matching terms with <mark class="highlight">term</mark>
        # To avoid double-replacing or breaking XML, we do a case-insensitive match on terms
        # and sort by length descending to replace longer words first.
        matched_words_to_replace = set()
        for word in words_in_sentence:
            if self.stemmer.stem(word) in stemmed_query_terms:
                matched_words_to_replace.add(word)
                
        # Sort by length descending
        sorted_replacements = sorted(list(matched_words_to_replace), key=len, reverse=True)
        
        for word in sorted_replacements:
            # Use regex word boundaries to avoid matching sub-strings
            pattern = re.compile(rf'\b({re.escape(word)})\b', re.IGNORECASE)
            highlighted = pattern.sub(r'<mark class="highlight">\1</mark>', highlighted)
            
        return highlighted
