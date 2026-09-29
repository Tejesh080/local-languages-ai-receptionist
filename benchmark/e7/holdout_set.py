"""E7 HOLDOUT SET. Written 2026-09-30 AFTER the development runs and BEFORE any holdout run.
Rule: run once per frozen resolver version (scripts/e7_holdout.py enforces it). Never tune the resolver on its failures;
new failure patterns go into the development set and the next holdout must be freshly written.
Caveat: same author as the resolver, so it is less independent than third-party data. Real STT output is decisive."""

NAME_CASES = [
    ("Srinivaas Reddy", "adv1"), ("Sreenivasa Reddi garu", "adv1"), ("Srinivas Redy", "adv1"), ("శ్రీనివాసు రెడ్డి", "adv1"),
    ("శ్రీనివాస రెడ్డీ గారు", "adv1"), ("Srinivas Rao sir", "adv2"), ("Sreenivas Raw", "adv2"), ("శ్రీనివాస్ రావ్", "adv2"),
    ("Lachmi Naidu", "adv3"), ("Luxmi Naidu garu", "adv3"), ("లక్ష్మీ నాయుడు గారు", "adv3"), ("Venkata Reddy", "c01"),
    ("వెంకట్ రెడ్డి", "c01"), ("Wenkat Rao", "c02"), ("Ravi Nayudu", "c03"), ("Ravee Naidu", "c03"), ("Priyaa Sharma", "c04"),
    ("Priya Sarma", "c04"), ("Suresh Baabu", "c05"), ("Anjali Choudary", "c06"), ("Anjali Chowdhary", "c06"),
    ("అంజలి చౌదరి", "c06"), ("Mahesh Gowdu", "c07"), ("మహేష్ గౌడ్", "c07"), ("Kiran Kumaar", "c08"), ("Sai Theja", "c09"),
    ("సాయి తేజ", "c09"), ("Harika Yaadav", "c10"),
    ("Rao garu", {"adv2", "c02"}), ("Naidu garu", {"adv3", "c03"}), ("Srinivas sir", {"adv1", "adv2"}),
    ("Srikanth Reddy", None), ("Venkatesh Rao", None), ("Ravi Teja", None), ("Sai Kumar", None), ("Kiran Reddy", None),
    ("Lakshmi Prasanna", None),
]
SERVICE_CASES = [
    ("periodic maintenance", "general_service"), ("సర్వీస్ చేయించాలి", "general_service"), ("oil maarchali", "oil_change"),
    ("ఇంజిన్ ఆయిల్ చేంజ్", "oil_change"), ("brake pads check", "brake_inspection"), ("బ్రేకులు చెక్", "brake_inspection"),
    ("ac cooling problem", "ac_repair"), ("ఏసీ పనిచేయట్లేదు", "ac_repair"), ("battery down", "battery_replacement"),
    ("బ్యాటరీ మార్చాలి", "battery_replacement"), ("alignment balancing", "wheel_alignment"), ("వీల్ బ్యాలెన్సింగ్", "wheel_alignment"),
    ("tyre puncture", None), ("car wash", None), ("denting work", None), ("clutch overhaul", None),
]
REG_CASES = [
    ("TS09 E A 4521", "TS09EA4521"), ("T S zero nine E A four five two one", "TS09EA4521"),
    ("టీ ఎస్ సున్నా తొమ్మిది ఈ ఏ నాలుగు ఐదు రెండు ఒకటి", "TS09EA4521"), ("AP39 BK 7788", "AP39BK7788"),
    ("TG 08 C 1 2 3 4", "TG08C1234"), ("twenty two BH one two three four A B", "22BH1234AB"),
    ("TS 13 EZ 5566", "TS13EZ5566"), ("TS 07 FJ 33", {"TS07FJ3301", "TS07FJ3310"}), ("TS 09 EA 4512", None), ("AP 16 DD 9091", None),
]
