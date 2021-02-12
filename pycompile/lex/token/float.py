import re
from typing import Pattern

from pycompile.lex.token.token import Token


class Float(Token):
    """
    _accepted_pattern is the float pattern we are looking for
    the actual regex is more complicated to capture only the following two cases:
        first look for:
            (([1-9][0-9]*)|0)\.((([0-9]*[1-9])|0)(e[\+\-]?([1-9][0-9]*|0)))
            which is floats like 120.3424765e10000
            to extract this pattern, include a negative lookahead to allow a 0 after the e only when it's a single 0
                (?!(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)e[\+-]?0[0-9])
        if there is no e involved, look for:
            (([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0))
            which is floats like 126.33
            to extract this pattern, include two negative lookaheads
                (?!(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)e[\+-]?0[0-9])
                this excludes cases where there is a valid float followed by an invalid e
                (?!(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)0+)
                this excludes cases where there is an invalid float (trailing 0s)

    it is included as a static property of Float just for clarity/readability
    """
    _accepted_pattern: str = '([1-9][0-9]*)|0)\.((([0-9]*[1-9])|0)(e[\+\-]?[1-9][0-9]*)?'
    # pattern: Pattern = re.compile('(?!(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)0+)^(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)(e[\+\-]?[1-9][0-9]*)?')
    # pattern: Pattern = re.compile('^((([1-9][0-9]*)|0)\.((([0-9]*[1-9])|0)(e[\+\-]?[1-9][0-9]*))|((?!(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)0+)(?!(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)e)(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)))')
    pattern: Pattern = re.compile('^((?!(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)e[\+-]?0[0-9])(([1-9][0-9]*)|0)\.((([0-9]*[1-9])|0)(e[\+\-]?([1-9][0-9]*|0)))|((?!(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)0+)(?!(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)e[\+-]?0[0-9])(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)))')
    # (?!(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)0+)^(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)
    # final good pattern
    # ^((([1-9][0-9]*)|0)\.((([0-9]*[1-9])|0)(e[\+\-]?[1-9][0-9]*))|((?!(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)0+)(?!(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)e)(([1-9][0-9]*)|0)\.(([0-9]*[1-9])|0)))
    """
    trying to create a pattern that won't match a float with trailing zeroes
    (?!)^(([1-9][0-9]*)|0)\.(([0]*[1-9]*)|0)0+(\s|[^1-9])
    """

    def __init__(self, code: str):
        super().__init__(Float.pattern.match(code).group(), 'floatnum')

    @staticmethod
    def match(code: str) -> bool:
        return Float.pattern.match(code) is not None
