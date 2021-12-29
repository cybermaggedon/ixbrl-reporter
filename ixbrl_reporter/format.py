
# Number formatting, accountancy style.  Negative numbers appear in
# parentheses.

import string

class NegativeParenFormatter(string.Formatter):
    def format_field(self, value, format_spec):
        try:
            if value < 0:
                num = string.Formatter.format_field(self, -value, format_spec)
                return "(" + num + ")"
            else:
                num = string.Formatter.format_field(self, value, format_spec)
                return " " + num + " "
        except:
            return string.Formatter.format_field(self, value, format_spec)

