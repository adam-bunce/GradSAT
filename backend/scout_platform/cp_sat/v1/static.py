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


# pretending electives have no pre-requisites/co-requisites for now
random_electives = [
    "CSCI1020U",  # for pre-reqs
    "CSCI1040U",  # for pre-reqs
    "MATH1850U",
    "CSCI2070U",
    "CSCI4601U",
    "CSCI2160U",  # digital media
    "CSCI3040U",  # idk
    "CSCI2030U",  # idk
    #
    "MATH2072U",
    "MATH2015U",
    "MATH3030U",
    "MATH4020U",
    "PHY2030U",
    "PHY2040U",
    "PHY2900U",
    "PHY2900U",
    "PHY3900U",
    "ENVS1000U",
    "ENVS2000U",
    "BIOL1000",
    "BIOL2000",
]

credit_restrictions: dict[str, list[str]] = {
    "CSCI1030U": ["BUSI1830U", "CSCI1020U", "CSCI1030U", "CSCI1600U"],
    "CSCI1060U": ["CSCI2030U", "INFR1100U", "ENGR1200U"],
    "PHY1020U": ["PHY1040U", "PHY1810U"],
    "MATH1000U": ["BUSI1900U", "MATH1010U"],
    "MATH1010U": ["BUSI1900U", "MATH1000U"],
    "PHY1010U": ["PHY1030U", "PHY1810U"],
    "PHY1030U": ["PHY1010U", "PHY1810U"],
    "CSCI2072U": ["MATH2070U", "MATH2072U"],
    "CSCI2110U": ["CSCI1010U", "ELEE2110U", "MATH2080U"],
    "MATH2050U": ["BUSI1900U", "MATH1850U"],
    "STAT2010U": ["BUSI1450U", "HLSC3800U", "SSCI2910U", "STAT2020U", "STAT2800U"],
    "CSCI3070U": ["SOFE3770U"],
    "CSCI3030U": ["SOFE3700U"],
    "CSCI4050U": ["INFR4320U", "SOFE3720U"],
    "CSCI4610U": ["SOFE3720"],
    "CSCI3090U": ["ENGR4860U", "SOFE4860U"],
    "CSCI4620U": ["ENGR4850U", "SOFE4850U"],
    "CSCI3060U": ["SOFE3980U"],
    "CSCI4020U": ["SOFE3960U"],
    "CSCI3020U": ["SOFE3850U"],
    "CSCI3310": ["CSCI3020U", "CSCI3150U"],
}

prerequisites: dict[str, list[str]] = {
    "CSCI1061U": [["CSCI1060U"]],
    # OR 1020U or 1030u
    "CSCI2050U": [["CSCI1020U"], ["CSCI1030U"]],
    "MATH1020U": [["MATH1000U"], ["MATH1010U"]],
    # [] or [, ]
    "PHY1020U": [["PHY1010U"], ["PHY1030U", "MATH1000U"]],
    # "MATH1000U": "advanced functions",
    # "MATH1010U": "grade 12 functions, grade 12 calc"
    # "phy1010u": "grade 12 calc and vectosr"
    # "PHY1030U": "advanced functions"
    "CSCI2000U": [["CSCI1030U", "MATH1020U"], ["CSCI1040U", "MATH1020U"]],
    "CSCI2010U": [["CSCI1060U"]],  # or a b+ in csci 1040???
    "CSCI2020U": [["CSCI2010U"]],
    "CSCI2040U": [["CSCI2020U"]],  # with concurrency is ok
    "CSCI2072U": [["CSCI2000U", "MATH1020U", "MATH2050U"]],
    # "CSCI2110U": "24 credit hours in area of specalization?!" how am i gonna handle that
    "MATH2050U": [["MATH1000U"], ["MATH1010U"]],
    "STAT2010U": [["MATH1020U"]],
    # y3/4
    "CSCI3070U": [["CSCI2010U", "CSCI2110U"]],
    # "CSCI4040U": "completed year 2 (be in year 3)" whats this mean though? credits, years, course level?
    # (CSCI1020U or CSCI1030U) or (CSCI2070U or MATH2072U) -> these are credit-restrictions maybe just treat as same course?
    # i think parsing this and then applying constraints based on how its parsed makes more sense
    # or brute force all combinations...?
    "CSCI3010U": [
        ["CSCI1020U", "CSCI2070U"],
        ["CSCI1020U", "MATH2072U"],
        ["CSCI1030U", "CSCI2070U"],
        ["CSCI1030U", "MATH2072U"],
    ],
    "CSCI3030U": [["CSCI2010U", "CSCI2020U"]],
    "CSCI4030U": [["STAT2010U", "CSCI3030U"]],
    "CSCI4050U": [["CSCI3070U", "MATH2050U"]],
    "CSCI4610U": [["STAT2010U", "CSCI3070U"]],
    "CSCI3090U": [["CSCI2010U", "MATH1850U"], ["CSCI2010U", "MATH2050U"]],
    "CSCI4110U": [["CSCI3090U"]],
    "CSCI4210U": [["CSCI3030U"]],
    "CSCI3230U": [["CSCI2020U"]],
    "CSCI4100U": [["CSCI2020U"]],
    "CSCI4160U": [["CSCI2160U", "CSCI3090U"]],
    "CSCI4620U": [["CSCI2040U"], ["CSCI3040U"]],
    "CSCI3055U": [["CSCI1060U", "CSCI2110U"], ["CSCI2030U", "CSCI2110U"]],
    "CSCI3060U": [["CSCI2020U", "CSCI3040U"], ["CSCI2020U", "CSCI2040U"]],
    "CSCI4020U": [["CSCI2050U"]],
    "CSCI4060U": [["CSCI3070U"]],
    "CSCI3020U": [["CSCI2010U", "CSCI2050U"]],
    "CSCI3150U": [["CSCI2050U"]],
    "CSCI3310U": [["CSCI2020U", "CSCI2050U"]],
    "CSCI4310U": [["CSCI3020U"], ["CSCI3310U"]],
    "CSCI4420U": [
        ["CSCI4410U"]
    ],  # thesis, also need post-requisite on 1sts semester of thesis
}


all_courses = [
    c
    for course in [y1_classes, y2_classes, y3_y4_classes, electives, random_electives]
    for c in course
]
