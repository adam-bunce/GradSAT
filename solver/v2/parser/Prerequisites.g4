grammar Prerequisites;

@parser::members{
def do_or(self, l: list[list] | list[str], r: list[list]| list[str]) -> list[list] | list[str]:
    def is_list_of_lists(lst):
        return isinstance(lst, list) and all(isinstance(item, list) for item in lst)

    left_new = []
    if is_list_of_lists(l):
        for value in l:
            left_new.append(value)
    else:
        left_new.append(l)

    right_new = []

    if is_list_of_lists(r):
        for value in r:
            right_new.append(value)
    else:
        left_new.append(r)

    res = []

    # sometimes empty list
    if right_new:
        res.extend(right_new)
    if left_new:
        res.extend(left_new)
    return res
}

expression returns [list result]
    : LPAREN e=expression RPAREN {$result=$e.result}
    | e1=expression AND e2=expression {$result=[[*v1, *v2] for v1 in $e1.result for v2 in $e2.result]}
    | e1=expression OR e2=expression {$result=self.do_or($e1.result, $e2.result)}
    | c=COURSE {$result=[[$c.text]]}
    ;


fragment DIGIT: '0'.. '9';
fragment LETTER: 'a'..'z' | 'A'..'Z';
COURSE: LETTER | LETTER+ SPACE? DIGIT+ LETTER+;
OR: ('OR' | 'or');
AND: ('AND' | 'and');
LPAREN: '(';
RPAREN: ')';
WHITESPACE: [ \t\n\r]+ -> skip ;
SPACE: ' ';
