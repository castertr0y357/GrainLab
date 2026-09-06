class AIPromptBuilder:
    """
    Mixin class providing AI prompt generation methods for Recipe Engines.
    Separated from BaseEngine to reduce logic complexity and isolate prompt tuning.
    """

    def get_ai_culinary_directive(self) -> str:
        return ""

    def get_diagnostic_insight(self, item_id: str) -> dict:
        from .insights_fallbacks import BREAD_FALLBACKS

        insight = BREAD_FALLBACKS.get(item_id)
        if not insight and item_id.startswith("grain_"):
            for k, val in BREAD_FALLBACKS.items():
                if k.startswith("grain_") and (k in item_id or item_id in k):
                    insight = val
                    break
        return insight or {
            "labor_roi": "Low Priority / Minor Textural Return",
            "last_10_percent_analysis": "An objective workspace configuration parameter. No significant performance anomalies or hidden labor opportunities detected.",
        }

    def get_ai_flavor_directive(self) -> str:
        return ""

    def get_ai_structural_directive(self) -> str:
        return ""

    def get_additive_scaling_directive(self) -> str:
        return "When generating ratios for inclusions or additives, use true baker's percentages (where flour = 100%). Default ranges are typically 10.0 to 30.0 for standard doughs. CRITICAL: For potent spices or herbs (e.g. garlic, oregano, cinnamon, pepper), strictly limit to 0.1 to 1.5 to avoid overpowering the profile. CRITICAL: For chemical leaveners (baking powder, baking soda), strictly limit to 1.0 to 5.0 to avoid chemical taste."
