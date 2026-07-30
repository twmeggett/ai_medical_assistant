"""
(question, reference answer) pairs for backend/evals.py, grounded in the
articles actually ingested into article_chunks. Reference answers are the
ground truth ContextPrecision/ContextRecall are judged against, so keep them
accurate to what the source articles actually say. Extend this as more
articles are ingested.
"""

EVAL_SET = [
    {
        "question": (
            "Does high-dose atorvastatin or moderate-dose rosuvastatin more "
            "effectively reduce major adverse cardiovascular events in "
            "patients with coronary artery disease?"
        ),
        "reference": (
            "High-dose atorvastatin (80mg/day) significantly reduced MACE "
            "compared with moderate-dose rosuvastatin (20mg/day) in patients "
            "with established coronary artery disease — 9.4% vs 11.2% "
            "(HR 0.83, 95% CI 0.72-0.95, p=0.007) — driven by lower rates of "
            "non-fatal myocardial infarction. Atorvastatin also produced a "
            "greater LDL-C reduction but more new-onset diabetes."
        ),
    },
    {
        "question": (
            "In patients with atrial fibrillation and end-stage renal disease "
            "on haemodialysis, does apixaban reduce stroke or systemic "
            "embolism compared with warfarin, and what is the bleeding "
            "tradeoff?"
        ),
        "reference": (
            "Apixaban significantly reduced the composite of stroke or "
            "systemic embolism versus warfarin (4.1% vs 6.8% per year; "
            "HR 0.60, 95% CI 0.42-0.86, p=0.005), and also reduced major "
            "bleeding (6.2% vs 8.9% per year; HR 0.69, 95% CI 0.52-0.91, "
            "p=0.009), with lower haemorrhagic stroke rates as well "
            "(0.4% vs 1.2% per year)."
        ),
    },
    {
        "question": (
            "In patients with resistant hypertension and CKD stages 3-4, how "
            "much does dapagliflozin reduce 24-hour ambulatory systolic "
            "blood pressure compared with placebo, and what happened to "
            "eGFR decline?"
        ),
        "reference": (
            "Dapagliflozin reduced 24-hour ambulatory systolic blood "
            "pressure by 7.3 mmHg versus 1.4 mmHg with placebo (difference "
            "-5.9 mmHg; 95% CI -7.3 to -4.5; p<0.001), and attenuated eGFR "
            "decline (-1.2 vs -3.1 mL/min/1.73m² per year; p=0.003), though "
            "at the cost of more symptomatic hypotension and genital "
            "mycotic infections."
        ),
    },
    {
        "question": (
            "Does adding fludrocortisone to hydrocortisone reduce 90-day "
            "mortality in septic shock patients requiring prolonged "
            "noradrenaline, compared with hydrocortisone alone?"
        ),
        "reference": (
            "No — 90-day mortality was not significantly different between "
            "combination therapy and hydrocortisone alone (36.2% vs 40.1%; "
            "OR 0.85, 95% CI 0.66-1.09, p=0.20). However, vasopressor-free "
            "days were significantly greater with combination therapy "
            "(18.3 vs 16.7 days; p=0.03), and ICU length of stay did not "
            "differ."
        ),
    },
    {
        "question": (
            "Is IV esketamine non-inferior to electroconvulsive therapy for "
            "treatment-resistant depression at 4 weeks?"
        ),
        "reference": (
            "No, non-inferiority was not demonstrated. Mean MADRS reduction "
            "was -23.4 points with esketamine versus -26.1 points with ECT "
            "(difference 2.7 points; 95% CI 1.1-4.3), and response rates "
            "(≥50% MADRS reduction) were 61.4% with esketamine versus 72.1% "
            "with ECT. ECT also achieved higher remission rates (49.4% vs "
            "38.2%), though esketamine had a faster onset and a more "
            "favourable cognitive adverse effect profile."
        ),
    },
    {
        "question": (
            "What was the clinical benefit of continuous lecanemab treatment "
            "over 36 months compared with delayed-start treatment in early "
            "Alzheimer's disease, and what was the rate of ARIA-E?"
        ),
        "reference": (
            "At 36 months, continuous lecanemab treatment showed 32% less "
            "decline on CDR-SB compared with delayed-start treatment "
            "(difference -0.81 points; 95% CI -1.23 to -0.39; p<0.001), and "
            "76.3% of continuous-treatment patients reached near-"
            "amyloid-negative PET status. ARIA-E occurred in 37.2% of the "
            "continuous group versus 31.4% of the delayed-start group."
        ),
    },
    {
        "question": (
            "Did a 15-day course of nirmatrelvir-ritonavir improve long "
            "COVID symptom severity compared with placebo at 12 weeks, and "
            "did it meet the pre-specified threshold for clinical "
            "meaningfulness?"
        ),
        "reference": (
            "Nirmatrelvir-ritonavir produced a statistically significant "
            "reduction in PASC symptom severity score versus placebo "
            "(-18.4 vs -14.2 points; difference -4.2 points; 95% CI -6.8 to "
            "-1.6; p=0.002), but this fell short of the pre-specified "
            "8-point threshold for clinical meaningfulness in the overall "
            "population. Patients with detectable SARS-CoV-2 nucleocapsid "
            "antigen at baseline had a substantially larger benefit (-8.4 "
            "vs -1.9 points in antigen-negative patients)."
        ),
    },
    {
        "question": (
            "In first-line metastatic HER2-negative triple-negative breast "
            "cancer, does adding pembrolizumab to nab-paclitaxel improve "
            "progression-free and overall survival, and does the benefit "
            "depend on PD-L1 expression?"
        ),
        "reference": (
            "Yes, but only in patients with PD-L1 CPS ≥10. In that "
            "subgroup, pembrolizumab plus nab-paclitaxel improved median "
            "PFS (9.7 vs 5.6 months; HR 0.65, 95% CI 0.53-0.80, p<0.001) "
            "and median OS (23.0 vs 16.1 months; HR 0.73, 95% CI 0.57-0.93, "
            "p=0.011) versus chemotherapy alone. No significant PFS or OS "
            "benefit was observed in patients with PD-L1 CPS <10."
        ),
    },
    {
        "question": (
            "How does semaglutide 1.0mg weekly compare with dulaglutide "
            "1.5mg weekly for HbA1c reduction and weight loss in adults "
            "with inadequately controlled type 2 diabetes on metformin?"
        ),
        "reference": (
            "Semaglutide produced a greater HbA1c reduction than "
            "dulaglutide (-1.8% vs -1.3%; difference -0.5%; 95% CI -0.6 to "
            "-0.4; p<0.001) and greater weight loss (-5.9 kg vs -3.1 kg; "
            "p<0.001) over 52 weeks, though nausea was more frequent with "
            "semaglutide (23.4% vs 14.2%)."
        ),
    },
    {
        "question": (
            "In COPD patients with frequent exacerbations and blood "
            "eosinophils ≥300 cells/µL, does triple inhaled therapy reduce "
            "exacerbations compared with dual bronchodilation, and at what "
            "safety cost?"
        ),
        "reference": (
            "Triple therapy (ICS/LABA/LAMA) reduced the annualised "
            "moderate/severe exacerbation rate by 34% versus dual "
            "bronchodilation (0.81 vs 1.23 per year; rate ratio 0.66, 95% "
            "CI 0.59-0.74, p<0.001), and improved FEV1 at week 52 (+87 mL "
            "vs +36 mL, p<0.001). However, pneumonia rates were higher with "
            "triple therapy (7.1% vs 4.4%; p=0.002)."
        ),
    },
]
