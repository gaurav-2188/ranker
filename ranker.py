import json
import csv
import gzip
import os
from datetime import datetime

# Adjust this to point to the actual dataset file (candidates.jsonl.gz or sample_candidates.json)
DATASET_PATH = "sample_candidates.json" 
OUTPUT_CSV = "team_submission.csv"

def is_valid_engineering_title(title):
    """
    Trap Prevention: Filters out non-engineers who keyword-stuff their skills.
    Returns a multiplier.
    """
    title_lower = title.lower()
    # Immediate disqualifiers (The "Marketing Manager" trap)
    bad_keywords = ['marketing', 'hr', 'sales', 'recruiter', 'manager', 'designer', 'support', 'writer', 'executive']
    if any(b in title_lower for b in bad_keywords):
        return 0.0 
    
    # Positive signals
    good_keywords = ['ai', 'machine learning', 'ml', 'data', 'software', 'backend', 'engineer', 'scientist']
    if any(g in title_lower for g in good_keywords):
        return 1.0
        
    return 0.5 # Neutral

def compute_candidate_score(candidate):
    profile = candidate.get('profile', {})
    signals = candidate.get('redrob_signals', {})
    skills = candidate.get('skills', [])
    career = candidate.get('career_history', [])

    candidate_id = candidate.get('candidate_id')
    title = profile.get('current_title', 'Unknown')
    yoe = profile.get('years_of_experience', 0)

    # 1. Role / Title Match (Avoiding keyword stuffer traps)
    role_multiplier = is_valid_engineering_title(title)
    if role_multiplier == 0.0:
        return 0.0, f"Filtered: Title '{title}' indicates non-engineering role despite skills."

    # 2. Experience Match (Target: 5-9 years per JD)
    exp_score = 0.0
    if 5 <= yoe <= 9:
        exp_score = 1.0
    elif 3 <= yoe < 5 or 9 < yoe <= 12:
        exp_score = 0.8
    else:
        exp_score = 0.4

    # 3. Skills Match (Looking for ML Systems, RAG, Embeddings, LLMs)
    target_skills = ['python', 'pytorch', 'tensorflow', 'llm', 'rag', 'machine learning', 'nlp', 'pinecone', 'aws', 'spark', 'embeddings']
    matched_skills = [s.get('name') for s in skills if s.get('name', '').lower() in target_skills]
    skill_score = min(len(matched_skills) / 6.0, 1.0) # Max out at 6 relevant skills

    # 4. Behavioral Signals (The "Ghost" trap)
    # A perfect candidate who doesn't respond is useless.
    response_rate = signals.get('recruiter_response_rate', 0.0)
    recent_activity_multiplier = 1.0
    
    # Check if they've been active recently (penalize if inactive)
    last_active = signals.get('last_active_date')
    if last_active:
        try:
            # Assuming current date context around late 2024/2025 for dataset
            last_active_date = datetime.strptime(last_active, "%Y-%m-%d")
            if last_active_date.year < 2024:
                recent_activity_multiplier = 0.5
        except ValueError:
            pass

    behavioral_multiplier = response_rate * recent_activity_multiplier

    # Final Score Calculation
    base_score = (exp_score * 0.3) + (skill_score * 0.7)
    final_score = base_score * role_multiplier * behavioral_multiplier

    # Generate Reasoning per submission spec
    reasoning = f"{title} with {yoe} yrs exp; {len(matched_skills)} core AI skills; response rate {response_rate:.2f}."
    
    return final_score, reasoning

def load_candidates(filepath):
    print(f"Loading candidates from {filepath}...")
    candidates = []
    if filepath.endswith('.gz'):
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            for line in f:
                candidates.append(json.loads(line))
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
    return candidates

def main():
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Could not find {DATASET_PATH}")
        return

    candidates = load_candidates(DATASET_PATH)
    scored_candidates = []

    print("Scoring candidates...")
    for cand in candidates:
        score, reasoning = compute_candidate_score(cand)
        scored_candidates.append({
            'candidate_id': cand['candidate_id'],
            'score': score,
            'reasoning': reasoning
        })

    # Sort rules: Monotonically non-increasing score. Tie-breaker: candidate_id ascending.
    # Python sorts tuples element by element. -score handles descending, candidate_id handles ascending tie-break.
    scored_candidates.sort(key=lambda x: (-x['score'], x['candidate_id']))

    # Take top 100
    top_100 = scored_candidates[:100]

    print(f"Writing top 100 candidates to {OUTPUT_CSV}...")
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['candidate_id', 'rank', 'score', 'reasoning'])
        for rank, cand in enumerate(top_100, start=1):
            # Format score to 4 decimal places to match sample_submission.csv
            formatted_score = f"{cand['score']:.4f}"
            writer.writerow([cand['candidate_id'], rank, formatted_score, cand['reasoning']])

    print("Done! Run validate_submission.py to ensure format is correct.")

if __name__ == "__main__":
    main()
