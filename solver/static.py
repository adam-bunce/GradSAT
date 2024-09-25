y1_classes = [
    "CSCI1030U",
    "CSCI1060U",
    "CSCI1061U",
    "CSCI2050U",
    "MATH1020U",
    "PHY1020U",
    "MATH1000U",
    "MATH1010U",
    "PHY1010U",
    "PHY1030U",
]

# could take no electives until year later year but
# just do EXACT course map
y2_classes = [
    "CSCI2000U",
    "CSCI2010U",
    "CSCI2020U",
    "CSCI2040U",
    "CSCI2072U",
    "CSCI2110U",
    "MATH2050U",
    "STAT2010U",
]

electives = [
    "COMM1050U",
    "COMM1100U",
    "COMM1320U",
    "COMM2311U",
    "COMM2620U",
    "BUSI1600U",
    "BUSI1700U",
    "BUSI2000U",
    "BUSI2200U",
    "BUSI2311U",
]


y3_y4_classes = [
    # MUST
    "CSCI3070U",
    "CSCI4040U",
    # ONE OF
    "CSCI3010U",
    "CSCI3030U",
    "CSCI4030U",
    "CSCI4050U",
    "CSCI4610U",
    # ONE OF
    "CSCI3090U",
    "CSCI4110U",
    "CSCI4210U",
    "CSCI4220U",
    # ONE OF
    "CSCI3230U",
    "CSCI4100U",
    "CSCI4160U",
    "CSCI4620U",
    # ONE OF
    "CSCI3055U",
    "CSCI3060U",
    "CSCI4020U",
    "CSCI4060U",
    # ONE OF
    "CSCI3020U",
    "CSCI3150U",
    "CSCI3310U",
    "CSCI4310U",
    # THESIS, optional
    "CSCI4410U",
    "CSCI4420U",
]


all_decision_vars = [
    "y1",
    "y2",
    "y3",
    "y4",
    "y1_elective",
    "y2_elective",
    "y3_elective",
    "y4_elective",
]

elective_decision_vars = [
    "y1_elective",
    "y2_elective",
    "y3_elective",
    "y4_elective",
]

core_decision_vars = [
    "y1",
    "y2",
    "y3",
    "y4",
]


random_electives = [
    "MATH2015U",
    "MATH3030U",
    "MATH4020U",
    "PHY2030U",
    "PHY2040U",
    "PHY2900U",
    "PHY2900U",
    "PHY3900U",
    "ENVS1000U",
]


all_courses = [
    c
    for course in [y1_classes, y2_classes, y3_y4_classes, electives, random_electives]
    for c in course
]
