import random
import string

from config import ROOT_DIR, main_configs
from logotype import print_logotype


def create_server_user():
    print_logotype()
    cycle_run = True
    while cycle_run:
        print("Enter client name:")
        client_name = input()
        print("\"%s\" Let's use this name? y/n" % (client_name,))
        while True:
            answer = input()
            if answer[0] == "y" or answer[0] == "Y":
                cycle_run = False
                break
            elif answer[0] == "n" or answer[0] == "N":
                break
        if cycle_run:
            continue
        client_token = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(30))
        print("\"%s\" Client token." % (client_token,))
        print("Data written to file clients.")


if __name__ == '__main__':
    create_server_user()


