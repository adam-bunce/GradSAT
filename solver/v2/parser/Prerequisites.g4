grammar Prerequisites;

expression
    : andExpr
    | orExpr
    | expression AND expression
    | expression OR expression
    | LPAREN expression RPAREN
    | course
    ;

andExpr
    : course (AND course)+
    ;

orExpr
    : course (OR course)+
    ;

course
    : COURSE
    ;

fragment DIGIT: '0'.. '9';
fragment LETTER: 'a'..'z' | 'A'..'Z';
COURSE: LETTER+ SPACE? DIGIT+ LETTER+;
OR: ('OR' | 'or');
AND: ('AND' | 'and');
LPAREN: '(';
RPAREN: ')';
WHITESPACE: [ \t\n\r]+ -> skip ;
SPACE: ' ';
