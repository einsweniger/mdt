from rlcompleter import Completer



# import readline # optional, will allow Up/Down/History in the console
# import code
# vars = globals().copy()
# vars.update(locals())
# shell = code.InteractiveConsole(vars)
# shell.interact()


class MyCompleter(Completer):
    def complete(self, text, state):
        print(text)
        print(state)
        if state == 2:
            return None
        return text+str(state)