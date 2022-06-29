import importlib

# Contrived example of generating a module named as a string
full_module_name = "serve"

# The file gets executed upon import, as expected.
mymodule = importlib.import_module(full_module_name)

# # Then you can use the module like normal
# base1_obj = mymodule.Base1()
# base1_obj.base1_func1()

class Klasa2(mymodule.Base1):
    def __init__(self):
        super()

    def klasa2_func1(self):
        print('klasa2_func1')
        self.base1_func1()

klasa2_obj = Klasa2()
klasa2_obj.klasa2_func1()