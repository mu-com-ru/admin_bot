def alert_format(data):
    def func(x):
        return f'[{x[1]}] {x[0]}'
    return '\n'.join(map(func, data))