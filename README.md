# Redrob Intelligent Candidate Discovery & Ranking System

This repository contains our team's submission for the Redrob Candidate Discovery Challenge. The system implements a rules based heuristic pipeline designed to parse a pool of 100,000 candidate profiles and extract the top 100 most viable matches for the Founding Senior AI Engineer role.

## Core Design & Strategy

The main challenge of this dataset isn't finding matches with the right skills, but filtering out candidates who look perfect on paper but are completely unavailable or misaligned with a Series A environment. Our ranking loop evaluates profiles through a strict filtering and down-weighting process:

1. **Title Filter Trap:** To counter keyword-stuffing profiles (e.g., non-technical roles with deep ML keyword sections), the pipeline applies a binary multipass check on titles. Non engineering titles (Marketing, Sales, HR, etc.) are immediately zeroed out.
2. **Experience Curve Matching:** The Job Description specifies a targeted 5–9 years window. The code scores candidates on an experience curve giving maximum weight to the 5-9 target bracket, dropping slightly for high-potential 3-4 or 10-12 year profiles, and steeply decaying elsewhere.
3. **Behavioral Availability Modifiers:** We combine the technical profile matching with a heavy multiplier based on the platform interaction data. Candidates with weak recruiter response rates or stagnant activity parameters are heavily down-weighted.

