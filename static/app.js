// CineSearch Frontend Controller

// Global state
let currentTab = 'search';
let activeSearchResults = {}; // Map of id -> movie object

document.addEventListener('DOMContentLoaded', () => {
    fetchIndexStats();
    setupInputListeners();
});

// Fetch overall index statistics for header dashboard
async function fetchIndexStats() {
    try {
        const response = await fetch('/api/stats');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('stat-docs').textContent = data.total_documents;
            document.getElementById('stat-vocab').textContent = data.vocab_size;
            document.getElementById('stat-postings').textContent = data.total_postings;
        }
    } catch (error) {
        console.error('Error fetching statistics:', error);
    }
}

// Listen to input changes to show/hide clear button
function setupInputListeners() {
    const searchInput = document.getElementById('search-input');
    const clearBtn = document.getElementById('clear-search-btn');
    
    searchInput.addEventListener('input', () => {
        if (searchInput.value.length > 0) {
            clearBtn.style.display = 'block';
        } else {
            clearBtn.style.display = 'none';
        }
    });
}

// Switch tabs: 'search' or 'explorer'
function switchTab(tab) {
    if (tab === currentTab) return;
    currentTab = tab;
    
    // Toggle active buttons
    document.getElementById('tab-btn-search').classList.toggle('active', tab === 'search');
    document.getElementById('tab-btn-explorer').classList.toggle('active', tab === 'explorer');
    
    // Toggle active views
    document.getElementById('view-search').classList.toggle('active', tab === 'search');
    document.getElementById('view-explorer').classList.toggle('active', tab === 'explorer');
}

// Set text inside search placeholder based on mode selection
function updateSearchPlaceholder() {
    const mode = document.querySelector('input[name="search-mode"]:checked').value;
    const searchInput = document.getElementById('search-input');
    
    if (mode === 'boolean') {
        searchInput.placeholder = "Enter boolean query: e.g. 'nolan AND space', 'romance OR drama', 'action AND NOT sci-fi'";
    } else {
        searchInput.placeholder = "Enter keywords: e.g. 'space travel', 'mind thief', 'nolan dream'";
    }
}

// Clear search input and restore welcome state
function clearSearch() {
    const searchInput = document.getElementById('search-input');
    searchInput.value = '';
    document.getElementById('clear-search-btn').style.display = 'none';
    
    document.getElementById('search-status-bar').style.display = 'none';
    document.getElementById('search-results-list').innerHTML = '';
    document.getElementById('search-welcome-state').style.display = 'flex';
    searchInput.focus();
}

// Pre-fill a query and search immediately
function fillAndSearch(text) {
    const searchInput = document.getElementById('search-input');
    searchInput.value = text;
    document.getElementById('clear-search-btn').style.display = 'block';
    
    // Submit form programmatically
    const mockEvent = { preventDefault: () => {} };
    performSearch(mockEvent);
}

// Main search execution
async function performSearch(event) {
    event.preventDefault();
    
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;
    
    const mode = document.querySelector('input[name="search-mode"]:checked').value;
    
    // UI Loading State
    document.getElementById('search-welcome-state').style.display = 'none';
    document.getElementById('search-status-bar').style.display = 'none';
    document.getElementById('search-results-list').innerHTML = '';
    document.getElementById('search-loader').style.display = 'flex';
    
    try {
        const url = `/api/search?q=${encodeURIComponent(query)}&mode=${mode}`;
        const response = await fetch(url);
        
        if (!response.ok) throw new Error('Search request failed');
        
        const data = await response.json();
        
        // Hide loader
        document.getElementById('search-loader').style.display = 'none';
        
        // Render stats
        const statusBar = document.getElementById('search-status-bar');
        const resultsText = document.getElementById('status-results-text');
        
        const textMode = mode === 'boolean' ? 'Boolean Set matching' : 'Cosine TF-IDF matching';
        resultsText.textContent = `Found ${data.results_count} movie${data.results_count === 1 ? '' : 's'} in ${data.time_ms}ms using ${textMode}`;
        statusBar.style.display = 'flex';
        
        // Populate results
        const resultsList = document.getElementById('search-results-list');
        activeSearchResults = {}; // reset cache
        
        if (data.results_count === 0) {
            resultsList.innerHTML = `
                <div class="welcome-state">
                    <i class="fa-solid fa-face-frown welcome-icon"></i>
                    <h2>No Matching Documents</h2>
                    <p>No records in our inverted index matched your query terms. Try refining your spelling or boolean terms.</p>
                </div>
            `;
            return;
        }
        
        data.results.forEach(res => {
            // Save to details cache
            activeSearchResults[res.id] = res;
            
            const card = document.createElement('div');
            card.className = 'movie-card';
            card.onclick = () => openModal(res.id);
            
            // Build genres
            const genreTags = res.genres.map(g => `<span class="genre-tag">${g}</span>`).join('');
            
            // Build matched terms (if standard ranked mode)
            let matchedSection = '';
            if (mode === 'ranked' && res.matched_terms && res.matched_terms.length > 0) {
                const termsTags = res.matched_terms.map(t => `<span class="matched-term-tag">${t}</span>`).join(', ');
                matchedSection = `
                    <div class="matched-info">
                        <strong>Matched:</strong> 
                        <span class="matched-terms-list">${termsTags}</span>
                    </div>
                `;
            }
            
            // Score badges
            const simScoreBadge = mode === 'ranked' ? `<span class="similarity-score">Score: ${res.score}</span>` : '';
            
            card.innerHTML = `
                <div class="movie-header-row">
                    <div class="movie-title-block">
                        <h3>${res.title} <span class="year">(${res.year})</span></h3>
                    </div>
                    <div class="score-badge-block">
                        ${simScoreBadge}
                        <span class="rating-badge">
                            <i class="fa-solid fa-star"></i> ${res.rating}
                        </span>
                    </div>
                </div>
                
                <div class="genres-row">
                    ${genreTags}
                </div>
                
                <div class="snippet-block">
                    ${res.snippet}
                </div>
                
                <div class="movie-footer-row">
                    <div class="director-info">
                        <strong>Director:</strong> ${res.director}
                    </div>
                    ${matchedSection}
                </div>
            `;
            
            resultsList.appendChild(card);
        });
        
    } catch (error) {
        console.error('Search error:', error);
        document.getElementById('search-loader').style.display = 'none';
        document.getElementById('search-results-list').innerHTML = `
            <div class="welcome-state">
                <i class="fa-solid fa-circle-exclamation welcome-icon" style="color: var(--accent-cyan);"></i>
                <h2>Search Query Error</h2>
                <p>There was a processing exception matching your terms. Please check your query syntax for unbalanced operators.</p>
            </div>
        `;
    }
}

// Inverted Index Explorer - handle enter key
function handleExplorerKeypress(event) {
    if (event.key === 'Enter') {
        inspectTerm();
    }
}

// Fetch term details from Inverted Index API and render postings list
async function inspectTerm() {
    const word = document.getElementById('explorer-input').value.trim();
    if (!word) return;
    
    document.getElementById('explorer-welcome-state').style.display = 'none';
    document.getElementById('explorer-data-view').style.display = 'none';
    document.getElementById('explorer-loader').style.display = 'flex';
    
    try {
        const response = await fetch(`/api/index-debug?word=${encodeURIComponent(word)}`);
        if (!response.ok) throw new Error('Explorer API failed');
        
        const data = await response.json();
        
        document.getElementById('explorer-loader').style.display = 'none';
        
        if (data.postings.length === 0) {
            document.getElementById('explorer-welcome-state').style.display = 'flex';
            document.getElementById('explorer-welcome-state').innerHTML = `
                <i class="fa-solid fa-magnifying-glass-minus welcome-icon"></i>
                <h2>Term Not Found</h2>
                <p>The term "<strong>${word}</strong>" (stemmed to "<strong>${data.stemmed || word}</strong>") does not exist in our inverted index vocabulary dictionary.</p>
            `;
            return;
        }
        
        // Update meta
        document.getElementById('exp-queried-word').textContent = data.word;
        document.getElementById('exp-stemmed-word').textContent = data.stemmed;
        document.getElementById('exp-df').textContent = `${data.postings.length} document${data.postings.length === 1 ? '' : 's'}`;
        
        // Build table
        const tbody = document.getElementById('postings-table-body');
        tbody.innerHTML = '';
        
        data.postings.forEach(p => {
            const tr = document.createElement('tr');
            
            // Build occurrences details
            let occHtml = '<div class="occurrences-grid">';
            for (const [field, positions] of Object.entries(p.fields)) {
                occHtml += `
                    <div class="occurrence-item">
                        <span class="occ-field-label">${field}</span>
                        <span class="occ-positions">[${positions.join(', ')}]</span>
                    </div>
                `;
            }
            occHtml += '</div>';
            
            tr.innerHTML = `
                <td class="doc-id-cell">${p.doc_id}</td>
                <td>
                    <h4>${p.title}</h4>
                </td>
                <td>
                    <span class="tf-badge">TF: ${p.freq}</span>
                </td>
                <td>
                    ${occHtml}
                </td>
            `;
            
            tbody.appendChild(tr);
        });
        
        document.getElementById('explorer-data-view').style.display = 'block';
        
    } catch (error) {
        console.error('Explorer error:', error);
        document.getElementById('explorer-loader').style.display = 'none';
    }
}

// Modal management
function openModal(movieId) {
    const movieData = activeSearchResults[movieId];
    if (!movieData) return;
    
    document.getElementById('modal-title').textContent = movieData.title;
    document.getElementById('modal-year').textContent = `(${movieData.year})`;
    document.getElementById('modal-rating-val').textContent = movieData.rating;
    document.getElementById('modal-director').textContent = movieData.director;
    document.getElementById('modal-cast').textContent = movieData.cast.join(', ');
    
    // Highlighted plot or standard plot outline
    document.getElementById('modal-plot').innerHTML = movieData.snippet || movieData.plot;
    
    // Build genres tags
    const genresListContainer = document.getElementById('modal-genres');
    genresListContainer.innerHTML = movieData.genres.map(g => `<span class="genre-tag">${g}</span>`).join('');
    
    // Display modal
    document.getElementById('movie-modal').classList.add('active');
}

function closeModal(event) {
    if (event.target === document.getElementById('movie-modal')) {
        closeModalDirectly();
    }
}

function closeModalDirectly() {
    document.getElementById('movie-modal').classList.remove('active');
}
