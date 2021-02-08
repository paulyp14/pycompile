from pycompile.lex.analyzer import LexicalAnalyzer


def main():
    cases = [
        "// single line comment",
        """/*
        multi line 
        comment
        */""",
        """/* /*
        Nested multiline
        /* another nested
        */
        */ hello
        about to end
        */
        """,
        '100.09 asd jh yo yo "gaga goo 129_plpl loo"',
        '"gaga goo 129_plpl loo" bababooboo',
    ]

    text = """==	+	|	(	;	if 	public	read
<>	-	&	)	,	then	private	write
<	*	!	{	.	else	func	return
>	/	?	}	:	integer	var	main
<=	=		[	::	float	class	inherits
>=			]		string	while	break
					void		continue
	




0
1
10
12
123
12345
	
1.23	
12.34	
120.34e10	
12345.6789e-123	

abc 	
abc1
a1bc	
abc_1abc	
abc1_abc	

/* this is a single line block comment */

/* this is a 
multiple line
block comment 
*/

// this is an inline comment

"this is a string literal\""""

    for case in cases:
        res = LexicalAnalyzer.next_token(case)
        print('hello')

    analyzer = LexicalAnalyzer()
    analyzer.tokenize(text)
    print('done')


if __name__ == '__main__':
    main()