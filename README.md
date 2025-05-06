## Overview
**artistify** is a soundtrack generation system that takes a textual narrative, segments it into scenes, detects the emotional *vibe* of each scene, and assigns appropriate songs using semantic similarity. It integrates NLP-based processing with ESA vector space modelling and artist-specific lyric retrieval to recommend the best musical match for each scene.

## Run Instructions:
You will need a few API Keys to run this application as it makes use of three different services: ngrok, Spotify and Genius.            
Specifically you will need 2 ngrok tokens, one each for frontend API and backend API.       
Since this application is designed as a web application, this setup is a one-time setup and the rest is handled on request basis.       
The places where the API keys have to be added have been marked in the following files for your convenience.            
                    
Once you have the API keys, add them to the following files:        
1. Spotify and Genius API keys have to be added to the ".env" file in the backend folder.           
2. Ngrok API keys have to be added to the docker-compose.yml in the main directory. 

## System Objectives
- Automatically generate scene-wise music assignments from a storyline.
- Allow optional artist input to personalise the song recommendations.
- Return similarity-based justification for each song-scene match.

## Architecture Overview
**Frontend/API Consumer** → **/generate_soundtrack API** →
- `Scene Segmentation (BERT-based)`
- `ESA Vector Generation (TF-IDF + Wikipedia Corpus)`
- `Artist Recommendation (kNN on pre-computed vectors)`
- `Song Retrieval (Genius Lyrics API)`
- `Song Assignment (Hungarian Algorithm)`

→ **Response JSON with scene-song mappings**

## Components and Design Rationale

### Scene Segmentation (`process_storyline.py`)
Scenes are segmented using Sentence-BERT embeddings. Adjacent sentences are compared using cosine similarity. If the similarity drops below a threshold, a new scene begins.

**Rationale**: Chosen over rule-based segmentation for flexibility and generalisation across domains.

### Vibe Representation (`esa.py`)
Each scene is transformed into a semantic vector using Explicit Semantic Analysis (ESA) based on a lemmatised Wikipedia-derived corpus.

**Rationale**: ESA offers interpretable, concept-based embeddings and avoids the opaqueness of deep learning models while maintaining decent performance.

### Artist Selection (`model.py`)
If the user does not provide an artist, a nearest-neighbour classifier is used to suggest one by comparing scene vectors with pre-computed ESA vectors of artists.

**Rationale**: Semantic matching allows artist selection that aligns with narrative mood, offering meaningful relevance beyond genre tags.

### Song Retrieval (`genius_handler.py`, Genius API)
Top songs for the chosen artist are fetched from the Genius API. Lyrics are cleaned and passed through the ESA encoder to generate vectors.

**Rationale**: Genius offers wide coverage and reliable API access. Lyrics-based ESA ensures lyrical mood alignment.

### Song Assignment (`generate_soundtrack.py`)
Using cosine similarity between scenes and song vectors, the Hungarian algorithm ensures optimal one-to-one assignment.

**Rationale**: The Hungarian algorithm guarantees a global optimum, avoiding greedy local mismatches.

## Monitoring and Metrics
Prometheus metrics monitor:
- Request count
- Time for each major sub-process (scene splitting, vector generation, etc.)

**Rationale**: Enables performance tuning and bottleneck detection via Grafana/Prometheus dashboards.

## Technology Stack
- **FastAPI**: Lightweight, asynchronous API framework
- **NLP**: NLTK, Sentence-Transformers, Wikipedia API
- **Lyrics**: Genius API
- **Similarity/Vectorisation**: Scikit-learn, NumPy
- **Monitoring**: Prometheus Client
- **Frontend UI**: Flutter
- **Hosting**: ngrok

## Extensibility
- Swap ESA for more modern models (e.g., BERT, USE)
- Add multi-song per scene or song transition smoothing
- Expand recommendation system with genre, tempo, or theme filters

## Design Summary
**artistify** offers a modular, interpretable, and efficient architecture for semantic soundtrack generation. Its design prioritises explainability, simplicity, and extensibility. While ESA and cosine similarity provide a solid baseline, the system supports future upgrades to transformer-based models or hybrid retrieval strategies.
