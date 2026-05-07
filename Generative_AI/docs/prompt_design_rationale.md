# Prompt Design Rationale

## Phishing URL Detection, Generative AI Integration

This document explains the reasoning behind each of the four prompt templates, how findings from Phase 1 shaped the design decisions, observations from the testing process, and relevant references.

---

## 1. Thought Process Behind Each Template

### Template 1: Technical Security Report (Zero-Shot)

The first question we needed to answer was whether Gemini could produce a structured security report from instructions alone, without any examples. We based the output format on real SOC triage workflows (Verdict, Indicator Analysis, Risk Assessment) because that structure is already standard in incident response reports. Since Gemini's training data very likely includes security reports, zero-shot prompting was a reasonable starting point to test whether the model could follow that format without extra guidance.

T1 also serves as a baseline. If the model produces a usable report from instructions alone, then any quality improvement seen in T2 or T4 (which include examples) can be credited to the prompting technique rather than to the instructions themselves.

### Template 2: Plain-Language Explanation (One-Shot)

T2 targets a different audience: non-technical users who see phishing warnings in their browser or email. The main challenge was fitting the explanation into 2–3 sentences without losing the reasoning that tells the user *why* a link is dangerous, not just *that* it is.

We chose one-shot prompting because we needed tight control over both tone and length. The example we wrote uses simple words like "scam" instead of "phishing campaign" and "secure connection" instead of "TLS certificate," and the model consistently matched that vocabulary level in its outputs. A zero-shot approach would have risked the model falling back to technical language, which would defeat the purpose of a user-facing warning.

### Template 3: Feature-Driven Technical Report (Chain-of-Thought)

T3 started from a practical question: if a security analyst reads the explanation, can they check every claim against the actual feature values? This means the model needs to go through each feature one at a time, judge whether its value is normal or suspicious, and only then reach a conclusion.

The four-step reasoning structure is fixed on purpose:

1. State the feature and its value.
2. Judge whether the value is normal or suspicious.
3. Count how many features support versus contradict the prediction.
4. Give an overall risk assessment.

Step 3 turned out to be the most important part. It forces the model to point out when the evidence is mixed rather than just agreeing with whatever the classifier predicted, which is a common problem in explanation-generation tasks.

### Template 4: Comparative Analysis (Few-Shot)

Templates 1 through 3 all explain the prediction on its own. T4 takes a different approach: it places the analyzed URL next to a typical legitimate URL so that suspicious differences stand out right away. This is similar to how phishing awareness training works in practice. Showing a fake login page side by side with a real one makes the differences clear in a way that describing them in text does not.

We gave the model two complete examples (one phishing URL, one legitimate URL) for two reasons. First, the comparison table format is specific enough that instructions alone would produce inconsistent layouts. Second, showing both outcomes prevents the model from assuming every URL is phishing, which we noticed in early zero-shot experiments with table-based output.

---

## 2. How Domain Knowledge Influenced Design

### The IsHTTPS Bias

Phase 1 analysis showed that the training dataset contains very few legitimate HTTP URLs. Because of this, the classifier treats the absence of HTTPS as a strong phishing signal. This works in most cases but fails for sites like neverssl.com, which are legitimate and intentionally use plain HTTP.

This finding shaped the prompt design in two ways. First, every template includes the instruction "Do not speculate beyond the provided features," which stops the LLM from adding its own opinions about HTTP safety on top of the classifier's already biased prediction. Second, T3's Step 3 (the supporting-versus-contradicting count) was added specifically so that at least one template could flag when the evidence is mixed, rather than simply backing up the classifier's output.

### Lexical-Only Feature Scope

Phase 1 uses only features that can be calculated from the URL string itself: no page content, no screenshots, no SSL certificate details. The prompts needed to stay within that same scope. We enforced this with the "Do not speculate beyond the provided features" rule in every template and made sure none of the example outputs mention page-level signals like visual layout or certificate issuers.

### Feature Importance Ranking

The Logistic Regression coefficients from Phase 1 show that URLLength, DomainLength, and IsHTTPS are the three strongest predictors. Instead of asking the LLM to treat all 11 features equally, we built a `{top_features}` placeholder into every template. This points the model's attention toward the features that matter most to the classifier's decision, making the explanations more focused and useful.

---

## 3. Lessons Learned During Testing

### Lesson 1: One-shot prompting limits depth, not just style

The example in T2 was four sentences long. During testing, the model matched that length almost exactly every time, even for URLs with complex feature combinations that probably needed more explanation. One-shot prompting works well for controlling tone and format, but it can also set an unintended cap on how much detail the model provides, and that cap is hard to lift through instructions alone.

### Lesson 2: Chain-of-thought reasoning catches contradictions

All four templates were tested on neverssl.com, a legitimate site that uses HTTP. T3 was the only template that pointed out the contradiction: some features suggested phishing while others did not, and the model said so directly. T1, T2, and T4 all produced confident phishing explanations with no uncertainty noted. This was the strongest evidence for choosing T3 as the primary template.

### Lesson 3: Few-shot prompting gives the most consistent formatting

T4's comparison table came out with the same structure across all three test URLs and across multiple runs. T1 (zero-shot), on the other hand, sometimes changed its section headings or reordered the report between runs. For cases where the output needs to be parsed or displayed in a fixed UI layout, few-shot prompting is the most reliable option.

### Lesson 4: Temperature and word limits affect each other

At temperature 0.3, outputs stayed within the expected length ranges consistently. In early experiments at temperature 0.7, T1 and T3 sometimes went past their word limits. Using a low temperature together with explicit word limits in the prompt gave the most predictable results.

### Lesson 5: Scoring per test case shows that performance depends on the scenario

We initially gave each template one set of scores averaged across all test cases. This hid the fact that T2 scored well on the phishing URL but poorly on the edge case (neverssl.com). Breaking the scores out per test case (4 templates × 3 URLs = 12 rows) showed that template performance changes depending on the scenario. This is why we recommend T3 for detailed analysis and T4 as a quick-view alternative, rather than picking one template for everything.

---

## 4. References

Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S., Herbert-Voss, A., Krueger, G., Henighan, T., Child, R., Ramesh, A., Ziegler, D. M., Wu, J., Winter, C., ... Amodei, D. (2020). Language models are few-shot learners. In *Advances in Neural Information Processing Systems 33* (NeurIPS 2020). https://arxiv.org/abs/2005.14165

Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q., & Zhou, D. (2022). Chain-of-thought prompting elicits reasoning in large language models. In *Advances in Neural Information Processing Systems 35* (NeurIPS 2022). https://arxiv.org/abs/2201.11903

OpenAI. (2024). Prompt engineering guide. OpenAI documentation. https://platform.openai.com/docs/guides/prompt-engineering

Google. (2025). Gemini API documentation. Google AI for Developers. https://ai.google.dev/docs

Holtzman, A., Buys, J., Du, L., Forbes, M., & Choi, Y. (2020). The curious case of neural text degeneration. In *Proceedings of the 8th International Conference on Learning Representations* (ICLR 2020). https://arxiv.org/abs/1904.09751

Google. (2025). google-generativeai: Python client for the Google Generative AI API. Python Package Index. https://pypi.org/project/google-generativeai/

textstat developers. (n.d.). textstat: Easy-to-use text statistics library. Python Package Index. Retrieved April 26, 2026, from https://pypi.org/project/textstat/
