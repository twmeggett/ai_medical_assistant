from backend.models.prompts import PromptVersion

MED_CHAT_USER_V1 = PromptVersion(
    content=(
        "<user_message>{message}</user_message>\n\n"
        "Before responding,reason through this step by step inside <thinking> tags.\n"
        "Then provide your response, grounding each key claim in a direct quote from the source material using the format:\n"
        "> \"[quote]\" — Author et al., Journal Name, Year"
    ),
    version="1.0",
    sprint=2,
    optimized_for="chain-of-thought reasoning with source-grounded quotes",
    notes="Wraps user message in XML tag, requires step-by-step thinking and direct citation quotes before responding",
)

MED_CHAT_USER_V2 = PromptVersion(
    content="""
    Here are examples of how to respond to medical research questions:

    <example>
    <input>What is the evidence for beta-blockers in heart failure with reduced ejection fraction?</input>
    <thinking>
    The question asks about beta-blocker evidence in HFrEF. Key trials to consider: MERIT-HF (metoprolol), CIBIS-II (bisoprolol), COPERNICUS (carvedilol).
    All three showed mortality benefit. I should cite specific findings and note ESC/ACC guideline endorsement.
    </thinking>
    <output>
    Beta-blockers are a Class I recommendation in HFrEF, supported by three landmark RCTs:

    **Mortality reduction:** The MERIT-HF trial demonstrated a 34% relative risk reduction in all-cause mortality with metoprolol succinate versus placebo.
    > "Treatment with metoprolol CR/XL resulted in a 34% reduction in total mortality" — MERIT-HF Study Group, Lancet, 1999

    **Bisoprolol evidence:** CIBIS-II reported a 34% reduction in all-cause mortality in NYHA III–IV patients.
    > "Bisoprolol significantly reduced all-cause mortality... hazard ratio 0.66" — CIBIS-II Investigators, Lancet, 1999

    **Severe HF:** COPERNICUS extended this benefit to LVEF <25%, with carvedilol reducing mortality by 35%.
    > "Carvedilol produced a 35% reduction in the risk of death" — Packer et al., NEJM, 2001

    Current ACC/AHA guidelines recommend carvedilol, metoprolol succinate, or bisoprolol — evidence-based agents only.
    </output>
    </example>

    <example>
    <input>What are the latest guidelines on anticoagulation in atrial fibrillation?</input>
    <thinking>
    Current AF anticoagulation guidance centres on stroke risk stratification via CHA₂DS₂-VASc, DOAC preference over warfarin,
    and HAS-BLED for bleeding risk. I should reference the 2023 ACC/AHA/ACCP/HRS guidelines and key DOAC trial data.
    </thinking>
    <output>
    Anticoagulation in AF is guided by stroke risk stratification and DOAC-first recommendations:

    **Risk stratification:** CHA₂DS₂-VASc score ≥2 in men or ≥3 in women warrants anticoagulation.
    > "Oral anticoagulation is recommended for patients with AF and CHA₂DS₂-VASc score ≥2 in men" — Joglar et al., JACC, 2023

    **DOAC preference:** DOACs are preferred over vitamin K antagonists for non-valvular AF due to superior safety profiles.
    > "For patients with nonvalvular AF... NOACs are recommended over warfarin" — Joglar et al., JACC, 2023

    **Bleeding risk:** HAS-BLED should inform shared decision-making but should not routinely be used to withhold anticoagulation.
    > "Bleeding risk scores should not be used as the primary reason to withhold anticoagulation" — Hindricks et al., European Heart Journal, 2021
    </output>
    </example>

    <example>
    <input>Is there evidence for corticosteroids in septic shock?</input>
    <thinking>
    Evidence is mixed. CORTICUS (2008) showed no mortality benefit. APROCCHSS (2018) and ADRENAL (2018) had conflicting results
    on 90-day mortality. Surviving Sepsis Campaign 2021 guidelines suggest hydrocortisone for refractory shock.
    I should acknowledge the conflicting evidence honestly.
    </thinking>
    <output>
    Evidence for corticosteroids in septic shock is conflicting — I will present it transparently:

    **Against routine use:** The CORTICUS RCT found no 28-day mortality benefit with hydrocortisone.
    > "Hydrocortisone did not improve survival or reversal of shock in the overall population" — Sprung et al., NEJM, 2008

    **Conditional benefit:** APROCCHSS reported reduced 90-day mortality with hydrocortisone plus fludrocortisone in vasopressor-dependent shock.
    > "Treatment with hydrocortisone plus fludrocortisone was associated with lower 90-day mortality" — Annane et al., NEJM, 2018

    **ADRENAL counterpoint:** The concurrent ADRENAL trial found faster shock reversal but no 90-day mortality difference with hydrocortisone alone.
    > "Hydrocortisone did not result in lower 90-day mortality than placebo" — Venkatesh et al., NEJM, 2018

    **Current guidance:** The Surviving Sepsis Campaign 2021 recommends IV hydrocortisone (200 mg/day) for adults with septic shock
    refractory to adequate fluid resuscitation and vasopressors — acknowledging low certainty of evidence.
    </output>
    </example>

    Now respond to the following question using the same format:

    <user_message>{message}</user_message>

    Reason through your response inside <thinking> tags, then provide your answer inside <output> tags,
    grounding each key claim in a direct quote using the format:
    > "[quote]" — Author et al., Journal Name, Year
    """,
    version="2.0",
    sprint=2,
    optimized_for="few-shot prompting with chain-of-thought reasoning and source-grounded citations",
    notes="Added 3 medical few-shot examples with <input>/<thinking>/<output> XML structure covering HFrEF, AF anticoagulation, and septic shock corticosteroids",
    changed_from="1.0",
)

ACTIVE_MED_CHAT_USER_PROMPT = MED_CHAT_USER_V1
