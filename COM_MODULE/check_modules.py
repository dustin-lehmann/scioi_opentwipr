import os

"""
this module checks automatically if any of the needed files are not downloaded yet and installs those missing
"""


class UpdateModules:
    def __init__(self):
        self.module_list_pip = ['crc8', 'cobs']
        self.module_list_apt = ['numpy']
        self.check_for_updates()

    def check_for_updates(self):
        # os.system('ls -l')
        os.system('sudo apt-get update')
        os.system('sudo apt-get upgrade -y')
        os.system('sudo apt install python3-pip')
        #        os.system('sudo apt-get python3 -y')
        for module in self.module_list_pip:
            # os.system('pip install ' + x)
            os.system('pip install {}'.format(module))
        for module in self.module_list_apt:
            # os.system('sudo apt-get install python3-'+ x +' -y')
            os.system('sudo apt-get install python3-{} -y'.format(module))

        print(len(self.module_list_pip))


if __name__ == "__main__":
    UpdateModules()
