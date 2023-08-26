def hello_function():
    def num_func(num: int) -> int:
        return num
    return num_func


hello = hello_function()
print(hello(50))
