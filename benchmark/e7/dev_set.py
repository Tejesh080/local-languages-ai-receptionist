"""E7 DEVELOPMENT SET. Hand-written by the resolver author and USED to design/fix resolver rules (run 1 -> run 2).
It is NOT an independent benchmark. Independent synthetic check: holdout_set.py. Decisive evidence: real E4 transcripts."""
# (observed text, truth id | None for "should not match" | set for "ambiguous by design")
NAME_CASES = [
    ("Srinivas Reddy", "adv1"), ("Srinivas Ready", "adv1"), ("Sreenivas Reddy", "adv1"), ("Srinivasa Reddi", "adv1"),
    ("శ్రీనివాస్ రెడ్డి", "adv1"), ("శ్రీనివాస రెడ్డి గారు", "adv1"), ("Srinivas Rao", "adv2"), ("Srinivas Row", "adv2"),
    ("శ్రీనివాస్ రావు", "adv2"), ("Shrinivas Rao garu", "adv2"), ("Lakshmi Naidu", "adv3"), ("Laxmi Naidoo", "adv3"),
    ("లక్ష్మి నాయుడు", "adv3"), ("Lakshmi Nayudu madam", "adv3"), ("Venkat Reddy", "c01"), ("Venkat Ready", "c01"),
    ("Venkat Rao", "c02"), ("వెంకట్ రావు", "c02"), ("Ravi Naidu", "c03"), ("Ravi Naidoo", "c03"), ("Priya Sharma", "c04"),
    ("ప్రియ శర్మ", "c04"), ("Suresh Babu", "c05"), ("సురేష్ బాబు", "c05"), ("Anjali Chowdary", "c06"), ("Anjali Choudhary", "c06"),
    ("Mahesh Goud", "c07"), ("Mahesh Gowd", "c07"), ("Kiran Kumar", "c08"), ("కిరణ్ కుమార్", "c08"), ("Sai Teja", "c09"),
    ("Harika Yadav", "c10"), ("హారిక యాదవ్", "c10"),
    ("Srinivas garu", {"adv1", "adv2"}), ("Venkat garu", {"c01", "c02"}), ("Reddy garu", {"adv1", "c01"}),
    ("Durga Prasad", None), ("Chandrasekhar", None), ("Nagendra Babu", None), ("Swathi Varma", None), ("Rambabu", None),
]
SERVICE_CASES = [
    ("general service", "general_service"), ("full service", "general_service"), ("సర్వీసింగ్", "general_service"),
    ("జనరల్ సర్వీస్", "general_service"), ("oil change", "oil_change"), ("ఆయిల్ మార్చాలి", "oil_change"),
    ("engine oil change", "oil_change"), ("brake check", "brake_inspection"), ("బ్రేక్ చెక్", "brake_inspection"),
    ("brakes", "brake_inspection"), ("AC service", "ac_repair"), ("ఏసీ కూలింగ్", "ac_repair"), ("A C repair", "ac_repair"),
    ("battery change", "battery_replacement"), ("బ్యాటరీ", "battery_replacement"), ("alignment", "wheel_alignment"),
    ("వీల్ అలైన్మెంట్", "wheel_alignment"), ("wheel balancing", "wheel_alignment"),
    ("clutch plate", None), ("denting painting", None), ("insurance claim", None),
]
REG_CASES = [
    ("TS 09 EA 4521", "TS09EA4521"), ("టి ఎస్ జీరో నైన్ ఈ ఏ ఫోర్ ఫైవ్ టూ వన్", "TS09EA4521"), ("TS09 EA 4527", "TS09EA4527"),
    ("AP 39 BK 7788", "AP39BK7788"), ("TG 08 C 1234", "TG08C1234"), ("22 BH 1234 AB", "22BH1234AB"),
    ("TS 09 EA 452", {"TS09EA4521", "TS09EA4527"}),            # truncated: must not pick silently
    ("TS 07 FJ 331", {"TS07FJ3301", "TS07FJ3310"}),
    ("TS 09 EA 4528", None),                                   # one-digit STT error: valid but not on file
    ("AP 39 BK 7789", None),
]


