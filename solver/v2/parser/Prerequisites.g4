grammar Prerequisites;

expression returns [list result]
    : LPAREN e=expression RPAREN {$result=$e.result}
    | e1=expression AND e2=expression {$result=[[*v1, *v2] for v1 in $e1.result for v2 in $e2.result]}
    | e1=expression OR e2=expression {$result=[$e1.result, $e2.result]}
    | c=COURSE {$result=[$c.text]}
    ;


fragment DIGIT: '0'.. '9';
fragment LETTER: 'a'..'z' | 'A'..'Z';
// COURSE: LETTER+ SPACE? DIGIT+ LETTER+;
COURSE: LETTER;
OR: ('OR' | 'or');
AND: ('AND' | 'and');
LPAREN: '(';
RPAREN: ')';
WHITESPACE: [ \t\n\r]+ -> skip ;
SPACE: ' ';
