import sys
import readchar


def clear_opc(list_len: int):
    # Limpia ambas líneas
    sys.stdout.write('\033[A' * 1 + '\r' + ' ' *
                     30 + '\n' + ' ' * 30 + '\r')
    sys.stdout.flush()

    # Mueve el cursor de vuelta arriba
    sys.stdout.write('\033[A' * (list_len))


def option_panel(options: list) -> int:
    selection = 0
    key = ''

    while True:
        for i in range(len(options)):
            sys.stdout.write(
                f'[{'x' if i == selection else ' '}] {options[i]}\n')

        sys.stdout.flush()
        key = readchar.readkey()

        if key == readchar.key.DOWN:
            if selection < len(options)-1:
                selection += 1

        if key == readchar.key.UP:
            if selection > 0:
                selection -= 1

        clear_opc(len(options))

        if key == readchar.key.ENTER:
            break

    # sys.stdout.write(f'Option {selection} was selected.\n')
    # sys.stdout.flush()
    return selection


if __name__ == '__main__':

    options = [
        'Option 1',
        'Option 2',
        'Option 3',
        'Option 4',
        'Option 5',
        'Option 6',
        'Option 7'
    ]
    selection: int = option_panel(options)
    print(f"Selection: {selection}")
