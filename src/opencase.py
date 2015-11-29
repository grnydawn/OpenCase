from os import chdir
from time import time
from shutil import copyfile
from oc_utils import Logger, Config, Timeout, UserException, ProgramException, TimeoutException
from oc_state import State
from oc_parse import parse_srcfiles
from oc_case import Case, configure_searching, execute_refcase, execute_nextcase
from oc_output import generate_output

def main():
    parse_srcfiles()
    Logger.info('Source files are parsed.', stdout=True)

    configure_searching()
    Logger.info('Searching is configured.', stdout=True)

    execute_refcase()
    Logger.info('Reference case is executed.', stdout=True)

    chdir(Config.path['workdir'])

    continued = True
    while continued:
        continued = execute_nextcase()

    Logger.info('Completed.', stdout=True)


# starts HERE
if __name__ == "__main__":

    try:
        print ''
        State.operation['begin'] = time()
        if Config.misc['timeout']:
            with Timeout(seconds=Config.misc['timeout']):
                main()
        else:
            main()
    except UserException as e:
        print 'ERROR: %s'%str(e)
        Logger.info(e)

    except ProgramException as e:
        Logger.critical(e)

    except TimeoutException as e:
        Logger.critical(e)

    except Exception as e:
        Logger.critical(e)

    finally:
        State.operation['end'] = time()
        generate_output()
