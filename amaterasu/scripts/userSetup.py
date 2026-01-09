# ==============================================================================
#
# Startup
#
# ==============================================================================
import sys

sys.dont_write_bytecode = True


def main() -> None:
    '''Start Amaterasu.'''
    import amaterasu

    amaterasu.main()


if __name__ == '__main__':
    main()
