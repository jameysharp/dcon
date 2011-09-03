from pymeta.grammar import OMeta

blog_grammar = """

crlf ::= '\r' '\n' => "<br />"

doublecrlf ::= <crlf> <crlf> => "</p><p>"

not_crlf ::= ~<crlf> <anything>

single_star ::= '*' ~'*'

double_star ::= '*' '*'

bold ::= <double_star> (~<double_star> <nested_decos>)+:b <double_star>
    => "<b>%s</b>" % "".join(b)

italics ::= <single_star> (~<single_star> <nested_decos>)+:i <single_star>
    => "<i>%s</i>" % "".join(i)

underline ::= '_' (~'_' <nested_decos>)+:u '_' => "<u>%s</u>" % "".join(u)

crlfs ::= <doublecrlf> | <crlf>

quote ::= <crlfs>:head '>' <nested_decos>+:body <crlfs>:tail
    => '%s<span class="quote">&gt;%s</span>%s' % (head, "".join(body), tail)

decorations ::= <bold> | <italics> | <underline>

nested_decos ::= <decorations> | <not_crlf>

entities ::= <quote> | <crlfs> | <decorations>

paragraphs ::= (<entities> | <anything>)*:l => "<p>%s</p>" % "".join(l)

"""

html_grammar = """

less_than ::= '<' => "&lt;"

greater_than ::= '>' => "&gt;"

ampersand ::= '&' => "&amp;"

safe_entities ::= <less_than> | <greater_than> | <ampersand>

safe_paragraphs ::= (<safe_entities> | <entities> | <anything>)*:l
    => "<p>%s</p>" % "".join(l)

"""

class BlogGrammar(OMeta.makeGrammar(blog_grammar + html_grammar, globals())):
    pass
