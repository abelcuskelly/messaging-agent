"""
Automated Quality Checks for Agent Responses
Validates response quality, coherence, relevance, and safety
"""

import os
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import structlog
from google.cloud import language_v1
import json

logger = structlog.get_logger()


@dataclass
class QualityScore:
    """Quality score for an agent response."""
    overall_score: float  # 0.0 to 1.0
    coherence_score: float
    relevance_score: float
    safety_score: float
    sentiment_score: float
    length_score: float
    grammar_score: float
    passed: bool
    issues: List[str]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class CoherenceChecker:
    """Check response coherence and readability."""
    
    def check(self, response: str, context: str = "") -> Tuple[float, List[str]]:
        """
        Check response coherence.
        
        Returns:
            Tuple of (score, issues)
        """
        issues = []
        score = 1.0
        
        # Check minimum length
        if len(response) < 10:
            issues.append("Response too short")
            score -= 0.3
        
        # Check maximum length
        if len(response) > 1000:
            issues.append("Response too long")
            score -= 0.2
        
        # Check for incomplete sentences
        if not response.strip().endswith(('.', '!', '?')):
            issues.append("Incomplete sentence")
            score -= 0.1
        
        # Check for repeated words
        words = response.lower().split()
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.5:
                issues.append("High word repetition")
                score -= 0.2
        
        # Check for proper capitalization
        sentences = re.split(r'[.!?]+', response)
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and not sentence[0].isupper():
                issues.append("Capitalization issue")
                score -= 0.1
                break
        
        return max(score, 0.0), issues


class RelevanceChecker:
    """Check response relevance to user query."""
    
    def check(self, user_message: str, response: str) -> Tuple[float, List[str]]:
        """
        Check response relevance.
        
        Returns:
            Tuple of (score, issues)
        """
        issues = []
        score = 1.0
        
        # Extract key terms from user message
        user_terms = set(re.findall(r'\b\w+\b', user_message.lower()))
        response_terms = set(re.findall(r'\b\w+\b', response.lower()))
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'i', 'you', 'me', 'my'}
        user_terms -= stop_words
        response_terms -= stop_words
        
        if not user_terms:
            return score, issues
        
        # Calculate term overlap
        overlap = user_terms & response_terms
        overlap_ratio = len(overlap) / len(user_terms)
        
        if overlap_ratio < 0.2:
            issues.append("Low relevance to user query")
            score -= 0.4
        elif overlap_ratio < 0.4:
            issues.append("Moderate relevance")
            score -= 0.2
        
        # Check for generic responses
        generic_phrases = [
            "i don't know",
            "i'm not sure",
            "i cannot help",
            "sorry, i can't"
        ]
        
        response_lower = response.lower()
        if any(phrase in response_lower for phrase in generic_phrases):
            issues.append("Generic/unhelpful response")
            score -= 0.3
        
        return max(score, 0.0), issues


class SafetyChecker:
    """Check response safety and appropriateness."""
    
    def __init__(self):
        self.unsafe_patterns = [
            r'\b(fuck|shit|damn|hell)\b',
            r'\b(idiot|stupid|dumb)\b',
            r'\b(hate|kill|die)\b',
        ]
        
        self.pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{16}\b',  # Credit card
            r'\b\d{3}-\d{3}-\d{4}\b',  # Phone number
        ]
    
    def check(self, response: str) -> Tuple[float, List[str]]:
        """
        Check response safety.
        
        Returns:
            Tuple of (score, issues)
        """
        issues = []
        score = 1.0
        
        # Check for unsafe content
        for pattern in self.unsafe_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                issues.append("Inappropriate language detected")
                score -= 0.5
                break
        
        # Check for PII leakage
        for pattern in self.pii_patterns:
            if re.search(pattern, response):
                issues.append("Potential PII leakage")
                score -= 0.8
                break
        
        # Check for financial advice (liability)
        financial_terms = ['invest', 'stock', 'guaranteed', 'profit']
        if any(term in response.lower() for term in financial_terms):
            issues.append("Potential financial advice")
            score -= 0.3
        
        return max(score, 0.0), issues


class SentimentChecker:
    """Check response sentiment."""
    
    def __init__(self):
        try:
            self.client = language_v1.LanguageServiceClient()
            self.use_api = True
        except:
            self.use_api = False
            logger.warning("Google NL API not available, using basic sentiment")
    
    def check(self, response: str) -> Tuple[float, List[str]]:
        """
        Check response sentiment.
        
        Returns:
            Tuple of (score, issues)
        """
        issues = []
        
        if self.use_api:
            try:
                document = language_v1.Document(
                    content=response,
                    type_=language_v1.Document.Type.PLAIN_TEXT
                )
                sentiment = self.client.analyze_sentiment(
                    request={'document': document}
                ).document_sentiment
                
                # Convert sentiment to score (0.0 to 1.0)
                # Sentiment score is -1 to 1, we want positive sentiment
                score = (sentiment.score + 1) / 2
                
                if sentiment.score < -0.5:
                    issues.append("Negative sentiment detected")
                
                return score, issues
                
            except Exception as e:
                logger.error("Sentiment analysis failed", error=str(e))
        
        # Basic sentiment check
        negative_words = ['unfortunately', 'cannot', 'unable', 'sorry', 'problem']
        positive_words = ['great', 'excellent', 'happy', 'help', 'available']
        
        response_lower = response.lower()
        neg_count = sum(1 for word in negative_words if word in response_lower)
        pos_count = sum(1 for word in positive_words if word in response_lower)
        
        if neg_count > pos_count + 2:
            issues.append("Overly negative tone")
            score = 0.5
        else:
            score = 0.8
        
        return score, issues


class GrammarChecker:
    """Check basic grammar and formatting."""
    
    def check(self, response: str) -> Tuple[float, List[str]]:
        """
        Check response grammar.
        
        Returns:
            Tuple of (score, issues)
        """
        issues = []
        score = 1.0
        
        # Check for double spaces
        if '  ' in response:
            issues.append("Multiple consecutive spaces")
            score -= 0.1
        
        # Check for missing spaces after punctuation
        if re.search(r'[.!?,][a-zA-Z]', response):
            issues.append("Missing space after punctuation")
            score -= 0.1
        
        # Check for repeated punctuation
        if re.search(r'[.!?]{3,}', response):
            issues.append("Excessive punctuation")
            score -= 0.1
        
        # Check for all caps (shouting)
        if response.isupper() and len(response) > 10:
            issues.append("All caps text")
            score -= 0.2
        
        return max(score, 0.0), issues


class QualityAssurance:
    """Main quality assurance system."""
    
    def __init__(
        self,
        min_overall_score: float = 0.7,
        min_coherence: float = 0.6,
        min_relevance: float = 0.5,
        min_safety: float = 0.9
    ):
        """
        Initialize QA system.
        
        Args:
            min_overall_score: Minimum overall score to pass
            min_coherence: Minimum coherence score
            min_relevance: Minimum relevance score
            min_safety: Minimum safety score
        """
        self.min_overall_score = min_overall_score
        self.min_coherence = min_coherence
        self.min_relevance = min_relevance
        self.min_safety = min_safety
        
        # Initialize checkers
        self.coherence_checker = CoherenceChecker()
        self.relevance_checker = RelevanceChecker()
        self.safety_checker = SafetyChecker()
        self.sentiment_checker = SentimentChecker()
        self.grammar_checker = GrammarChecker()
        
        logger.info("Quality assurance system initialized")
    
    def check_response(
        self,
        user_message: str,
        agent_response: str,
        context: Optional[str] = ""
    ) -> QualityScore:
        """
        Perform comprehensive quality check on agent response.
        
        Args:
            user_message: User's input message
            agent_response: Agent's response
            context: Optional conversation context
            
        Returns:
            QualityScore with detailed metrics
        """
        all_issues = []
        
        # Run all checks
        coherence_score, coherence_issues = self.coherence_checker.check(agent_response, context)
        all_issues.extend(coherence_issues)
        
        relevance_score, relevance_issues = self.relevance_checker.check(user_message, agent_response)
        all_issues.extend(relevance_issues)
        
        safety_score, safety_issues = self.safety_checker.check(agent_response)
        all_issues.extend(safety_issues)
        
        sentiment_score, sentiment_issues = self.sentiment_checker.check(agent_response)
        all_issues.extend(sentiment_issues)
        
        grammar_score, grammar_issues = self.grammar_checker.check(agent_response)
        all_issues.extend(grammar_issues)
        
        # Calculate length score
        length = len(agent_response)
        if 50 <= length <= 500:
            length_score = 1.0
        elif length < 50:
            length_score = length / 50
            all_issues.append("Response too short")
        else:
            length_score = max(0.5, 1.0 - (length - 500) / 1000)
            if length > 1000:
                all_issues.append("Response too long")
        
        # Calculate overall score (weighted average)
        overall_score = (
            coherence_score * 0.25 +
            relevance_score * 0.25 +
            safety_score * 0.20 +
            sentiment_score * 0.15 +
            grammar_score * 0.10 +
            length_score * 0.05
        )
        
        # Determine if passed
        passed = (
            overall_score >= self.min_overall_score and
            coherence_score >= self.min_coherence and
            relevance_score >= self.min_relevance and
            safety_score >= self.min_safety
        )
        
        quality_score = QualityScore(
            overall_score=overall_score,
            coherence_score=coherence_score,
            relevance_score=relevance_score,
            safety_score=safety_score,
            sentiment_score=sentiment_score,
            length_score=length_score,
            grammar_score=grammar_score,
            passed=passed,
            issues=all_issues
        )
        
        logger.debug("Quality check completed",
                    overall_score=overall_score,
                    passed=passed,
                    issues_count=len(all_issues))
        
        return quality_score
    
    def batch_check(
        self,
        conversations: List[Dict[str, str]]
    ) -> List[QualityScore]:
        """
        Batch quality check for multiple conversations.
        
        Args:
            conversations: List of dicts with 'user_message' and 'agent_response'
            
        Returns:
            List of QualityScore objects
        """
        scores = []
        
        for conv in conversations:
            score = self.check_response(
                user_message=conv.get("user_message", ""),
                agent_response=conv.get("agent_response", ""),
                context=conv.get("context", "")
            )
            scores.append(score)
        
        logger.info("Batch quality check completed",
                   total=len(conversations),
                   passed=sum(1 for s in scores if s.passed))
        
        return scores
    
    def get_quality_report(self, scores: List[QualityScore]) -> Dict[str, Any]:
        """Generate quality report from multiple scores."""
        if not scores:
            return {"error": "No scores provided"}
        
        total = len(scores)
        passed = sum(1 for s in scores if s.passed)
        
        # Aggregate scores
        avg_overall = sum(s.overall_score for s in scores) / total
        avg_coherence = sum(s.coherence_score for s in scores) / total
        avg_relevance = sum(s.relevance_score for s in scores) / total
        avg_safety = sum(s.safety_score for s in scores) / total
        avg_sentiment = sum(s.sentiment_score for s in scores) / total
        avg_grammar = sum(s.grammar_score for s in scores) / total
        
        # Collect all issues
        all_issues = []
        for score in scores:
            all_issues.extend(score.issues)
        
        # Count issue types
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Sort by frequency
        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        report = {
            "summary": {
                "total_checked": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": passed / total
            },
            "average_scores": {
                "overall": avg_overall,
                "coherence": avg_coherence,
                "relevance": avg_relevance,
                "safety": avg_safety,
                "sentiment": avg_sentiment,
                "grammar": avg_grammar
            },
            "top_issues": [
                {"issue": issue, "count": count, "percentage": count / total}
                for issue, count in top_issues
            ],
            "score_distribution": {
                "excellent": sum(1 for s in scores if s.overall_score >= 0.9) / total,
                "good": sum(1 for s in scores if 0.7 <= s.overall_score < 0.9) / total,
                "fair": sum(1 for s in scores if 0.5 <= s.overall_score < 0.7) / total,
                "poor": sum(1 for s in scores if s.overall_score < 0.5) / total
            }
        }
        
        return report


class RegressionTester:
    """Test for quality regression between model versions."""
    
    def __init__(self, qa_system: QualityAssurance):
        self.qa_system = qa_system
        self.baseline_scores: Dict[str, List[QualityScore]] = {}
    
    def set_baseline(self, model_version: str, test_cases: List[Dict[str, str]]):
        """Set baseline quality scores for a model version."""
        scores = self.qa_system.batch_check(test_cases)
        self.baseline_scores[model_version] = scores
        
        logger.info("Baseline set for model",
                   version=model_version,
                   test_cases=len(test_cases))
    
    def test_regression(
        self,
        model_version: str,
        test_cases: List[Dict[str, str]],
        baseline_version: str
    ) -> Dict[str, Any]:
        """
        Test for quality regression.
        
        Returns:
            Regression test results
        """
        if baseline_version not in self.baseline_scores:
            raise ValueError(f"No baseline found for version '{baseline_version}'")
        
        # Get new scores
        new_scores = self.qa_system.batch_check(test_cases)
        baseline_scores = self.baseline_scores[baseline_version]
        
        # Compare scores
        new_avg = sum(s.overall_score for s in new_scores) / len(new_scores)
        baseline_avg = sum(s.overall_score for s in baseline_scores) / len(baseline_scores)
        
        regression_detected = new_avg < baseline_avg - 0.05  # 5% threshold
        
        result = {
            "model_version": model_version,
            "baseline_version": baseline_version,
            "new_average_score": new_avg,
            "baseline_average_score": baseline_avg,
            "difference": new_avg - baseline_avg,
            "regression_detected": regression_detected,
            "test_cases": len(test_cases),
            "passed": not regression_detected
        }
        
        if regression_detected:
            logger.warning("Quality regression detected",
                          model=model_version,
                          baseline=baseline_version,
                          difference=new_avg - baseline_avg)
        else:
            logger.info("No regression detected",
                       model=model_version,
                       improvement=new_avg - baseline_avg)
        
        return result


# Global QA system
_qa_system: Optional[QualityAssurance] = None


def get_qa_system() -> QualityAssurance:
    """Get or create global QA system."""
    global _qa_system
    
    if _qa_system is None:
        _qa_system = QualityAssurance()
        logger.info("Quality assurance system initialized")
    
    return _qa_system
