grammar Prerequisites;

@lexer::members {
@staticmethod
def extract_year_standing(year_str: str) -> str:
    ysd: dict[str, str] = {
        "first": "first",
        "1st": "first",
        "1": "first",
        "second": "second",
        "2nd": "second",
        "2": "second",
        "third": "third",
        "3rd": "third",
        "3": "third",
        "fourth": "fourth",
        "4th": "fourth",
        "4": "fourth",
    }

    return ysd[year_str] + " year standing"
}

@parser::members {
@staticmethod
def in_program(program: str) -> str:
    print("in program", program)
    if program:
        return f" in {program}"
    else:
        return ""
}

expression returns [list result]
    : LPAREN e=expression RPAREN        {$result = $e.result }
    | e1=expression AND e2=expression   {$result = [[*v1, *v2] for v1 in $e1.result for v2 in $e2.result] }
    | e1=expression OR e2=expression    {$result = $e1.result + $e2.result }
    | c=COURSE                          {$result = [[$c.text]] }
    | ys=year_standing                  {$result = [[$ys.result]] }
    | ch=credit_hours                   {$result = [[$ch.text]] }
    ;

year_standing returns [str result]
    : (('year' (SPACE|'-') sy=STRING_YEAR) | (sy=STRING_YEAR (SPACE|'-') 'year'))
      SPACE 'standing' (SPACE 'in' SPACE pg=PROGRAMS)? {$result = $sy.text +  self.in_program($pg.text)}
    ;

credit_hours returns [str result]
    :  num=NUMBER SPACE? 'credit hours' (SPACE 'in' SPACE pg=PROGRAMS)? {$result = $num.text + ' credit hours' + self.in_program($pg.text)}
    ;


fragment DIGIT: '0'.. '9';
fragment LETTER: 'a'..'z' | 'A'..'Z';

NUMBER: DIGIT+;
COURSE: LETTER+ SPACE? DIGIT+ LETTER+;

OR: SPACE? ('OR' | 'or' | 'Or') SPACE?;
AND: SPACE? ('AND' | 'and' | 'And') SPACE?;

LPAREN: '(';
RPAREN: ')';

// space/whitespace order matters for ast?
// messes up: (ssci 2900u or ssci 2910u or ssci 2920u or lgls 2940u ) and (ssci 2810u or crmn 2830u or crmn 2850u or lgls 2200u or psyc 2030u or posc 2200u )
WHITESPACE: [ \t\n\r]+ -> skip ;
SPACE: ' ';

STRING_YEAR: ('first' |'1st'|'1' |
              'second'|'2nd'|'2'|
              'third' |'3rd'|'3' |
              'fourth'|'4th'|'4')
             { self.text = self.extract_year_standing(self.text) }
              ;

PROGRAMS: (
    'academic learning and success' |
    'automotive engineering' |
    'biology' |
    'business' |
    'chemistry' |
    'communication' |
    'computer science' |
    'criminology and justice' |
     'curriculum studies' |
     'economics' |
     'education' |
     'educational studies and digital technology' |
     'electrical engineering' |
     'energy systems and nuclear science' |
     'engineering' |
     'environmental science' |
     'forensic psychology' |
     'forensic science' |
    'health science' |
    'indigenous' |
    'information technology' |
    'integrated mathematics and computer science' |
     'kinesiology' |
     'legal studies' |
     'liberal studies' |
     'manufacturing engineering' |
     'mathematics' |
     'mechanical engineering' |
     'mechatronics engineering' |
     'medical laboratory science' |
     'neuroscience' |
     'nuclear' |
     'nursing' |
     'physics' |
     'political science' |
     'psychology' |
     'radiation science' |
     'science' |
     'science co-op' |
     'social science' |
     'sociology' |
     'software engineering' |
     'statistics' |
     'sustainable energy systems'
     );