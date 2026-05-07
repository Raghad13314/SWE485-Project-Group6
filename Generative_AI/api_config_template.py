"""
api_config_template.py
Gemini API configuration template for the Phishing URL Detection system.

Setup:
    1. Go to https://aistudio.google.com/apikey
    2. Create a free API key
    3. Set it as an environment variable:
       export GEMINI_API_KEY="your-key-here"

"""

import os
import time
import google.generativeai as genai


# ---------------------------------------------------------------
# API Configuration
# ---------------------------------------------------------------

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY environment variable not set. "
        "See the setup instructions at the top of this file."
    )

genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash"
model = genai.GenerativeModel(MODEL_NAME)


# ---------------------------------------------------------------
# API Call Wrapper
# ---------------------------------------------------------------

def call_gemini(prompt, temperature=0.3, max_tokens=2048):
    """Send a prompt to the Gemini API and return the response text.

    Parameters
    ----------
    prompt : str
        The fully formatted prompt string.
    temperature : float
        Controls randomness. Lower values produce more consistent output.
    max_tokens : int
        Maximum number of tokens in the response.

    Returns
    -------
    dict
        Contains 'text', 'usage' (token counts), and 'latency' (seconds).
    """
    start_time = time.time()

    generation_config = genai.types.GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_tokens
    )

    response = model.generate_content(
        prompt,
        generation_config=generation_config
    )

    latency = time.time() - start_time

    usage_metadata = response.usage_metadata
    usage = {
        "prompt_tokens": usage_metadata.prompt_token_count,
        "completion_tokens": usage_metadata.candidates_token_count,
        "total_tokens": usage_metadata.total_token_count
    }

    return {
        "text": response.text.strip(),
        "usage": usage,
        "latency": round(latency, 2)
    }


# ---------------------------------------------------------------
# Template Runner
# ---------------------------------------------------------------

def format_features(feature_dict):
    """Convert a feature dictionary into a readable string."""
    lines = []
    for name, value in feature_dict.items():
        if isinstance(value, float):
            lines.append(f"  {name} = {value:.4f}")
        else:
            lines.append(f"  {name} = {value}")
    return "\n".join(lines)


def get_top_features(feature_dict, importances, n=3):
    """Return the top n features ranked by importance."""
    ranked = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    top = []
    for feat, imp in ranked[:n]:
        if feat in feature_dict:
            top.append((feat, feature_dict[feat], imp))
    return top


def format_top_features(top_features):
    """Format top features into a readable string for the prompt."""
    lines = []
    for feat, val, imp in top_features:
        if isinstance(val, float):
            lines.append(f"  {feat} = {val:.4f} (importance: {imp:.4f})")
        else:
            lines.append(f"  {feat} = {val} (importance: {imp:.4f})")
    return "\n".join(lines)


def run_template(template_str, url, prediction, confidence,
                 features=None, feature_importances=None):
    """Fill a template with the given inputs and call the API.

    Parameters
    ----------
    template_str : str
        The prompt template with {placeholders}.
    url : str
        The URL being analyzed.
    prediction : str
        "Phishing" or "Legitimate".
    confidence : float
        Confidence score between 0.0 and 1.0.
    features : dict, optional
        Full dictionary of extracted features.
    feature_importances : dict, optional
        Feature importance scores for ranking.

    Returns
    -------
    dict
        API response dict with 'text', 'usage', 'latency', and 'prompt'.
    """
    features_str = format_features(features) if features else "Not provided"
    top_features_str = "Not provided"

    if features and feature_importances:
        top_feats = get_top_features(features, feature_importances, n=3)
        top_features_str = format_top_features(top_feats)

    prompt = template_str.format(
        url=url,
        prediction=prediction,
        confidence=confidence,
        features=features_str,
        top_features=top_features_str
    )

    result = call_gemini(prompt)
    result["prompt"] = prompt
    return result
