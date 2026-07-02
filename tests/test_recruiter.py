"""
Verification Tests for Redrob Candidate Recruiter Engine
"""

import json
import os
import unittest

from src.profile_builder import CandidateProfileBuilder
from src.feature_extractor import FeatureExtractor
from src.jd_parser import JDParser
from src.ranking_engine import RankingEngine
from src.reason_generator import ReasonGenerator


class TestRecruiterEngine(unittest.TestCase):

    def setUp(self):
        self.sample_file = "data/sample_candidates.json"
        self.assertTrue(os.path.exists(self.sample_file), "Sample candidates file must exist")
        
        with open(self.sample_file, "r", encoding="utf-8") as f:
            self.sample_candidates = json.load(f)
            
        self.jd = JDParser.get_default_requirements()

    def test_profile_builder_no_error(self):
        """Verify that all sample profiles parse without NameError (fixes certifications bug)."""
        for i, cand in enumerate(self.sample_candidates):
            try:
                profile = CandidateProfileBuilder.build(cand)
                self.assertIsNotNone(profile)
                self.assertEqual(profile.candidate_id, cand.get("candidate_id"))
                
                # Check certifications parsed
                raw_certs = cand.get("certifications", [])
                self.assertEqual(len(profile.certifications), len(raw_certs))
                
                # Check school tiers and grades are parsed
                for j, edu in enumerate(profile.education):
                    raw_edu = cand.get("education", [])[j]
                    self.assertEqual(edu.tier, raw_edu.get("tier", "unknown"))
                    self.assertEqual(edu.grade, raw_edu.get("grade"))
            except Exception as e:
                self.fail(f"Failed to parse candidate at index {i}: {e}")

    def test_feature_extractor(self):
        """Verify that feature extraction works and computes signals between 0.0 and 1.0."""
        for cand in self.sample_candidates:
            profile = CandidateProfileBuilder.build(cand)
            features = FeatureExtractor.extract(profile)
            
            # Check range of features
            for attr in [
                "production_ml", "retrieval_search", "recommendation_systems",
                "ranking_systems", "vector_databases", "embeddings",
                "leadership", "product_company", "services_only",
                "open_source", "candidate_activity"
            ]:
                val = getattr(features, attr)
                self.assertTrue(0.0 <= val <= 1.0, f"Feature {attr} value {val} out of bounds")

    def test_ranking_engine(self):
        """Verify that scoring compiles and outputs bounded final scores."""
        for cand in self.sample_candidates:
            scored = RankingEngine.score_candidate(cand, self.jd)
            self.assertTrue(0.0 <= scored["final_score"] <= 100.0)
            self.assertIn("technical", scored["sub_scores"])
            self.assertIn("career", scored["sub_scores"])
            self.assertIn("behaviour", scored["sub_scores"])
            self.assertIn("risk", scored["sub_scores"])

    def test_reason_generator(self):
        """Verify that the explanation generator produces structured content."""
        for cand in self.sample_candidates:
            scored = RankingEngine.score_candidate(cand, self.jd)
            explanation = ReasonGenerator.generate(scored, self.jd)
            
            self.assertTrue(len(explanation.strengths) > 0)
            self.assertIsNotNone(explanation.recommendation)
            
            # If candidate is blocked, verify blocker is listed in weaknesses
            if scored["is_blocked"]:
                self.assertTrue(any("BLOCKER" in w for w in explanation.weaknesses))


if __name__ == "__main__":
    unittest.main()
