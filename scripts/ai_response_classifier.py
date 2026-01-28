"""
ai_response_classifier.py
Auto-classifies HR responses using AI (OpenAI, Gemini, etc.)
"""

import os
import pandas as pd
import logging

# Dummy classifier for placeholder
# In production, replace with actual AI API calls

def classify_response(text):
    """Classify HR response text into categories."""
    # Placeholder logic
    text = text.lower()
    if any(word in text for word in ["interview", "schedule", "round"]):
        return "interview"
    if any(word in text for word in ["offer", "selected", "congratulations"]):
        return "offer"
    if any(word in text for word in ["reject", "unfortunately", "not selected"]):
        return "rejection"
    if any(word in text for word in ["thank", "received", "acknowledge"]):
        return "acknowledgment"
    return "needs_review"

def main():
    logging.basicConfig(level=logging.INFO)
    replies_path = os.path.join("data", "hr_replies.csv")
    if not os.path.exists(replies_path):
        logging.error(f"Replies file not found: {replies_path}")
        return
    df = pd.read_csv(replies_path)
    if "response_text" not in df.columns:
        logging.error("Missing 'response_text' column in replies file.")
        return
    df["classification"] = df["response_text"].fillna("").apply(classify_response)
    out_path = os.path.join("data", "hr_replies_classified.csv")
    df.to_csv(out_path, index=False)
    logging.info(f"Classified responses saved to {out_path}")

if __name__ == "__main__":
    main()
