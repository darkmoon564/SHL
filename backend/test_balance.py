from engine import engine

queries = [
    "Need a Java developer who is good in collaborating with external teams and stakeholders.",
    "Accounts payable specialist",
    "Leadership and personality assessment"
]

print("--- Testing Balance Logic ---")
for q in queries:
    print(f"\nQuery: {q}")
    results = engine.search(q, limit=5)
    for r in results:
        print(f" - [{r['category']}] {r['assessment_name']} ({r['score']:.3f})")
