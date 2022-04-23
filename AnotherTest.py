hello = "test"


def check():
    global hello
    hello = "eee"
    print(hello)


check()
