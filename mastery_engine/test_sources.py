"""
Evaluate source description quality - do they show relevance to the lesson?
"""

from engine import MasteryEngine

TEST_LESSONS = [
    {
        "topic": "Traffic Gating with Readiness and Liveness Probes",
        "urac_blueprint": {
            "understand": "Kubernetes uses two distinct probes: Liveness and Readiness. Liveness failures restart containers; Readiness failures remove pods from service endpoints.",
            "apply": "Configure probes for a web app that needs 30s to warm up its cache",
        }
    },
    {
        "topic": "Understanding P/E Ratios in Stock Valuation",
        "urac_blueprint": {
            "understand": "The P/E ratio compares stock price to earnings per share, showing how much investors pay for each dollar of earnings.",
            "apply": "Analyze if a tech stock with P/E of 45 is overvalued vs industry average of 25",
        }
    },
]

def test():
    engine = MasteryEngine()

    for lesson in TEST_LESSONS:
        print(f"\n{'='*70}")
        print(f"LESSON: {lesson['topic']}")
        print(f"{'='*70}")
        print(f"\nCore concept: {lesson['urac_blueprint']['understand']}")
        print(f"Application: {lesson['urac_blueprint']['apply']}")

        engine.module_plans = [{
            "module_order": 1,
            "original_module": {"title": "Test"},
            "lesson_plan": {
                "module_id": 1,
                "module_context_bridge": "",
                "lesson_plan": [lesson],
                "acquired_competencies": []
            }
        }]
        engine.current_module_idx = 0
        engine.current_lesson_idx = 0
        engine.clear_attributions_cache()

        result = engine.get_source_attributions(use_cache=False)

        print(f"\n📚 SOURCES ({result.get('fetch_time_seconds')}s):\n")

        for i, attr in enumerate(result.get('attributions', []), 1):
            print(f"[{i}] {attr['concept']}")
            print(f"    {attr['description']}")
            print()

        print("─"*70)
        print("EVALUATE: Do descriptions explain WHY this source helps the lesson?")
        print("─"*70)

if __name__ == "__main__":
    test()
