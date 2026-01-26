# ==============================================================================
#
# Startup
#
# Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.
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
