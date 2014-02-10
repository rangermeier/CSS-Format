import sublime, sublime_plugin, re

class LessFormatCommand(sublime_plugin.TextCommand):
    def run(self, edit, action='compact'):
        view = self.view

        if view.is_loading():
            sublime.status_message("Waiting for loading.")
            return False

        selection = view.sel()[0]
        if len(selection) > 0:
            self.format_selection(edit, action)
        else:
            self.format_whole_file(edit, action)

    def format_selection(self, edit, action):
        view = self.view
        regions = []
        for sel in view.sel():
            region = sublime.Region(
                view.line(min(sel.a, sel.b)).a,  # line start of first line
                view.line(max(sel.a, sel.b)).b   # line end of last line
            )
            code = view.substr(region)
            code = self.process_rules(code, action)
            view.replace(edit, region, code)

    def format_whole_file(self, edit, action):
        view = self.view
        region = sublime.Region(0, view.size())
        code = view.substr(region)
        code = self.process_rules(code, action)
        view.replace(edit, region, code)

    def process_rules(self, code, action):

        actions = {
            'format'    : self.format_rules,
            'indent'   : self.indent_rules
        }

        if action:
            code = actions[action](code)
        else:
            code = actions.format(code)
            code = actions.indent(code)

        return code


    def format_rules(self, code):
        code = re.sub(r"\s*([\{\}:;,])\s*", r"\1", code)        # remove \s before and after characters {}:;,
        code = re.sub(r";\s*;", ";", code)                      # remove superfluous ;

        code = re.sub(r"\/\*\s*([\s\S]+?)\s*\*\/", r"/* \1 */", code)   # add space before and after comment content
        code = re.sub(r"\}\s*(\/\*[\s\S]+?\*\/)\s*", r"}\n\1\n", code)  # add \n before and after outside comment
        code = re.sub(r",(\S)", r", \1", code)                          # add space after ,
        code = re.sub(r"([A-Za-z-]):([^;\{]+[;\}])", r"\1: \2", code)   # add space after properties' :
        code = re.sub(r"(http[s]?:) \/\/", r"\1//", code)               # fix space after http[s]:
        code = re.sub(r"\s*!important", r" !important", code)           # add space before !important

        
        code = re.sub(r"\{\s*(?=([^\"]*\"[^\"]*\")*[^\"]*$)", r" {\n", code)        # add space before { , and add \n after {
        code = re.sub(r"((@media|@[\w-]*keyframes)[^\{]+\{)\s*", r"\1\n", code)     # remove \t after @media {
        code = re.sub(r"(\S);([^\}])", r"\1;\n\2", code)                            # add \n after ;
        code = re.sub(r"\;\s*(\/\*[^\n]*\*\/)\s*", r"; \1\n\t", code)               # fix comment after ;
        code = re.sub(r"\}\s*(?=([^\"]*\"[^\"]*\")*[^\"]*$)", r"\n}\n", code)       # add \n before and after }

        code = re.sub(r"(@import[^;]+;)\s*", r"\1\n", code)     # add \n and remove \t after @import
        code = re.sub(r"^\s*(\S+(\s+\S+)*)\s*$", r"\1", code)   # remove superfluous \s

        return code


    def indent_rules(self, code):

        code = re.sub(r"^\s*(\S+(\s+\S+)*)$", r"\1", code)  # remove \s at begin of lines

        # get indentation settings
        settings = self.view.settings()
        use_spaces = settings.get("translate_tabs_to_spaces")
        tab_size = int(settings.get("tab_size", 8))
        indent_characters = "\t"
        if use_spaces:
            indent_characters = " " * tab_size

        level = 0
        indented = []
        # iterate over lines
        for line in code.split('\n'):
            line = line.strip()
            # increment indentation if there is a } (not in comment, not in quotes)
            if re.search(r"[^(\/\/)|(\/\*)]*}\s*(?=([^\"]*\"[^\"]*\")*[^\"]*$)", line):
                level -= 1

            # add spaces at beginning of non-empty lines
            if line:
                line = indent_characters * level + line

            # decrement indentation if there is a } (not in comment, not in quotes)
            if re.search(r"[^(\/\/)|(\/\*)]*{\s*(?=([^\"]*\"[^\"]*\")*[^\"]*$)", line):
                level += 1

            indented.append(line)

        code = "\n".join(indented)

        return code
