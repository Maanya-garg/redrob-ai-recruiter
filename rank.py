#!/usr/bin/env python
"""
Redrob AI Recruiter CLI Entrypoint
Parses job descriptions, streams candidates, scores and ranks them deterministically,
generates explanations, and writes the top candidates to structured reports.
"""

import argparse
import csv
import heapq
import json
import os
import sys
import time

from src.jd_parser import JDParser
from src.ranking_engine import RankingEngine
from src.reason_generator import ReasonGenerator


def main():
    parser = argparse.ArgumentParser(description="Redrob Data & AI Recruiter Ranking CLI")
    parser.add_argument(
        "--jd",
        type=str,
        default="data/job_description.md",
        help="Path to the Job Description Markdown file"
    )
    parser.add_argument(
        "--candidates",
        type=str,
        default="data/candidates.jsonl",
        help="Path to the Candidates JSONL database file"
    )
    parser.add_argument(
        "-k",
        "--limit",
        type=int,
        default=20,
        help="Number of top candidates to display in the CLI"
    )
    parser.add_argument(
        "--export-limit",
        type=int,
        default=1000,
        help="Number of top candidates to export to the output files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save output reports"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("      REDROB AI RECRUITER - CANDIDATE RANKING ENGINE      ")
    print("=" * 60)

    # 1. Parse Job Description
    print(f"[*] Reading Job Description from: {args.jd}")
    jd = JDParser.parse_file(args.jd)
    print(f"[+] Target Title: {jd.title}")
    print(f"[+] Experience required: {jd.min_years_experience} years")
    print(f"[+] Required skills: {', '.join(jd.required_skills)}")
    print(f"[+] Required signals: {', '.join(jd.required_features)}")
    if jd.salary_budget_max_lpa:
        print(f"[+] Salary budget cap: {jd.salary_budget_max_lpa} LPA")
    print(f"[+] Preferred work mode: {jd.preferred_work_mode}")
    print("-" * 60)

    # 2. Streaming Candidate Processing
    if not os.path.exists(args.candidates):
        print(f"[!] Candidates file not found at: {args.candidates}")
        # Try sample file fallback if available
        sample_path = "data/sample_candidates.json"
        if os.path.exists(sample_path):
            print(f"[*] Falling back to sample file: {sample_path}")
            # Load sample file (JSON list format instead of JSONL)
            try:
                with open(sample_path, "r", encoding="utf-8") as f:
                    sample_data = json.load(f)
                candidates_to_score = sample_data
            except Exception as e:
                print(f"[!] Error reading sample candidates: {e}")
                sys.exit(1)
        else:
            print("[!] Sample candidates file not found. Exiting.")
            sys.exit(1)
    else:
        candidates_to_score = None

    print(f"[*] Commencing candidate processing... This may take a moment.")
    start_time = time.time()

    top_k_heap = []  # Min-heap to keep top unblocked candidates
    blocked_candidates = []
    processed_count = 0
    blocked_count = 0
    unblocked_count = 0

    if candidates_to_score is not None:
        # Process from sample array
        for cand_json in candidates_to_score:
            processed_count += 1
            try:
                scored = RankingEngine.score_candidate(cand_json, jd)
                if scored["is_blocked"]:
                    blocked_candidates.append(scored)
                    blocked_count += 1
                else:
                    unblocked_count += 1
                    # Heap item: (final_score, candidate_id, scored_record)
                    heapq.heappush(top_k_heap, (scored["final_score"], scored["candidate_id"], scored))
                    if len(top_k_heap) > args.export_limit:
                        heapq.heappop(top_k_heap)
            except Exception as e:
                print(f"Error scoring sample candidate {cand_json.get('candidate_id')}: {e}")
    else:
        # Stream from large candidates.jsonl file
        stream = RankingEngine.stream_score_candidates(args.candidates, jd)
        for scored in stream:
            processed_count += 1
            if processed_count % 10000 == 0:
                print(f"[*] Processed {processed_count} candidates...")
                
            if scored["is_blocked"]:
                blocked_count += 1
                # To keep memory footprint low, only save first 100 blocked candidates for debug report
                if len(blocked_candidates) < 100:
                    blocked_candidates.append(scored)
            else:
                unblocked_count += 1
                heapq.heappush(top_k_heap, (scored["final_score"], scored["candidate_id"], scored))
                if len(top_k_heap) > args.export_limit:
                    heapq.heappop(top_k_heap)

    elapsed_time = time.time() - start_time
    print(f"[+] Processing completed in {elapsed_time:.2f} seconds.")
    print(f"[+] Total processed candidates: {processed_count}")
    print(f"[+] Valid candidates: {unblocked_count}")
    print(f"[+] Blocked candidates: {blocked_count}")
    print("-" * 60)

    # 3. Sort Results
    # Get top unblocked candidates sorted descending by score
    sorted_unblocked = sorted(
        [item[2] for item in top_k_heap],
        key=lambda x: x["final_score"],
        reverse=True
    )

    # 4. Generate Explanations for the Top Candidates shown in CLI
    cli_limit = min(args.limit, len(sorted_unblocked))
    print(f"\nRANKINGS: TOP {cli_limit} UNBLOCKED CANDIDATES\n")
    
    for i, scored in enumerate(sorted_unblocked[:cli_limit], 1):
        explanation = ReasonGenerator.generate(scored, jd)
        # Store explanation in record for file export
        scored["explanation"] = explanation
        
        print(f"{i}. [{scored['final_score']}/100] {scored['name']} ({scored['candidate_id']})")
        print(f"   Current: {scored['current_role']} at {scored['current_company']} ({scored['years_experience']} yrs exp)")
        print(f"   Tech: {scored['sub_scores']['technical']['score']} | Career: {scored['sub_scores']['career']['score']} | Behaviour: {scored['sub_scores']['behaviour']['score']} | Risk: {scored['sub_scores']['risk']['score']}")
        print(f"   Recommendation: {explanation.recommendation}")
        print("   Strengths:")
        for strg in explanation.strengths[:3]:
            print(f"     + {strg}")
        print("   Weaknesses:")
        for weak in explanation.weaknesses[:2]:
            print(f"     - {weak}")
        print("-" * 60)

    # 5. Export Reports
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 5a. Export JSON Report
    json_path = os.path.join(args.output_dir, "ranked_candidates.json")
    export_list = []
    for scored in sorted_unblocked:
        if "explanation" not in scored:
            scored["explanation"] = ReasonGenerator.generate(scored, jd)
        
        # Format object for clean JSON serialization
        export_list.append({
            "rank": len(export_list) + 1,
            "candidate_id": scored["candidate_id"],
            "name": scored["name"],
            "headline": scored["headline"],
            "current_role": scored["current_role"],
            "current_company": scored["current_company"],
            "years_experience": scored["years_experience"],
            "final_score": scored["final_score"],
            "sub_scores": {
                "technical": scored["sub_scores"]["technical"]["score"],
                "career": scored["sub_scores"]["career"]["score"],
                "behaviour": scored["sub_scores"]["behaviour"]["score"],
                "risk": scored["sub_scores"]["risk"]["score"]
            },
            "recommendation": scored["explanation"].recommendation,
            "strengths": scored["explanation"].strengths,
            "weaknesses": scored["explanation"].weaknesses
        })
        
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(export_list, jf, indent=2)
        print(f"[+] Saved structured JSON report to: {json_path}")
    except Exception as e:
        print(f"[!] Error saving JSON report: {e}")

    # 5b. Export CSV Report
    csv_path = os.path.join(args.output_dir, "ranked_candidates.csv")
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as cf:
            writer = csv.writer(cf)
            # Headers
            writer.writerow([
                "Rank", "Candidate ID", "Name", "Current Role", "Current Company",
                "Years Experience", "Final Score", "Technical Score", "Career Score",
                "Behaviour Score", "Risk Score", "Recommendation", "Top Strength", "Top Weakness"
            ])
            for item in export_list:
                top_strength = item["strengths"][0] if item["strengths"] else "N/A"
                top_weakness = item["weaknesses"][0] if item["weaknesses"] else "N/A"
                writer.writerow([
                    item["rank"], item["candidate_id"], item["name"], item["current_role"], item["current_company"],
                    item["years_experience"], item["final_score"], item["sub_scores"]["technical"],
                    item["sub_scores"]["career"], item["sub_scores"]["behaviour"], item["sub_scores"]["risk"],
                    item["recommendation"], top_strength, top_weakness
                ])
        print(f"[+] Saved CSV report to: {csv_path}")
    except Exception as e:
        print(f"[!] Error saving CSV report: {e}")


if __name__ == "__main__":
    main()
