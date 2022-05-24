from Communication.g_code.messages import *
from Communication.g_code.data import *
import re
from typing import List, Dict, Any
from layer_core_communication.core_messages import * #TODO: remove since this is just for testing!!


class GCODEParser:
    cmd_list: List[Dict[str, Any]]

    def __init__(self):
        self.cmd_list = []

    def parse(self, string):
        """
        parse the GCODE in a message that then can be sent
        :param string: GCODE that needs to be parsed
        :return: parsed message if string is valid, otherwise return M60
        """
        # delete old commands
        self.cmd_list.clear()
        # check for G-code, if string not valid set type to M60
        first_check = re.search('(?i)^([GM][0-9]{1,3})', string)
        if first_check is None:
            # Set message type to M60
            self.cmd_list = [{'type': 'M60'}]
            return self.cmd_list
        else:
            cmd = first_check.group(1).upper()

            # ------------------------------------------------------------------------------------------------ #
            #                                                G                                                 #
            # ------------------------------------------------------------------------------------------------ #

            # G0 - Configuration of the supervisor
            # example: G0 E(0,0,0,0,0,0,0,0,0)
            if cmd == 'G0':
                match = re.search(r'(?i)^G0\s?E\('
                                  '(?P<SV0>[01]),'
                                  '(?P<SV1>[01]),'
                                  '(?P<SV2>[01]),'
                                  '(?P<SV3>[01]),'
                                  '(?P<SV4>[01]),'
                                  '(?P<SV5>[01]),'
                                  '(?P<SV6>[01]),'
                                  '(?P<SV7>[01]),'
                                  '(?P<SV8>[01])\)\s*$', string)
                if match:
                    SV0 = int(match.groupdict()['SV0'])
                    SV1 = int(match.groupdict()['SV1'])
                    SV2 = int(match.groupdict()['SV2'])
                    SV3 = int(match.groupdict()['SV3'])
                    SV4 = int(match.groupdict()['SV4'])
                    SV5 = int(match.groupdict()['SV5'])
                    SV6 = int(match.groupdict()['SV6'])
                    SV7 = int(match.groupdict()['SV7'])
                    SV8 = int(match.groupdict()['SV8'])
    
                    sv_enable_list = [SV0, SV1, SV2, SV3, SV4, SV5, SV6, SV7, SV8]
                    sv_number = len(sv_enable_list)
    
                    msg = MSG_HOST_OUT_SV_CTRL(0, sv_number, sv_enable_list)
                    return msg
                else:
                    self.cmd_list = [{'type': 'M60'}]
                    return self.cmd_list

            # G1 - General control input
            elif cmd == 'G1':
                match = re.search(
                    r'(?i)(?:'
                    '\s?u\((?P<u1>[-+]?[0-9]{1,2}.?[0-9]{0,20}),(?P<u2>[-+]?[0-9]{1,2}.?[0-9]{0,20})\)|'
                    '\s?x(?P<x_velocity>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                    '\s?p(?P<p_velocity>[-+]?[0-9]{1,2}.?[0-9]{0,20}))+\s*$',
                    string)
                if match:
                    u1 = float(match.groupdict()['u1']) if match.groupdict()['u1'] else 0xFF
                    u2 = float(match.groupdict()['u2']) if match.groupdict()['u2'] else 0xFF
                    x_velocity = float(match.groupdict()['x_velocity']) if match.groupdict()['x_velocity'] else 0xFF
                    p_velocity = float(match.groupdict()['p_velocity']) if match.groupdict()['p_velocity'] else 0xFF

                    msg = MSG_HOST_OUT_CTRL_INPUT(0, (u1, u2), x_velocity, p_velocity)
                    return msg
                else:
                    self.cmd_list = [{'type': 'M60'}]
                    return self.cmd_list

            # G2 - Configuration of the state feedback controller
            elif cmd == 'G2':
                match = re.search(r'(?i)^G2\s?K\s?\('
                                  '(?P<K11>[-+]?[0-9]{1,2}.?[0-9]{0,20}),'
                                  '(?P<K21>[-+]?[0-9]{1,2}.?[0-9]{0,20}),'
                                  '(?P<K31>[-+]?[0-9]{1,2}.?[0-9]{0,20}),'
                                  '(?P<K41>[-+]?[0-9]{1,2}.?[0-9]{0,20}),'
                                  '(?P<K51>[-+]?[0-9]{1,2}.?[0-9]{0,20}),'
                                  '(?P<K61>[-+]?[0-9]{1,2}.?[0-9]{0,20}),'
                                  '(?P<K12>[-+]?[0-9]{1,2}.?[0-9]{0,20}),'
                                  '(?P<K22>[-+]?[0-9]{1,2}.?[0-9]{0,20}),'
                                  '(?P<K32>[-+]?[0-9]{1,2}.?[0-9]{0,20}),'
                                  '(?P<K42>[-+]?[0-9]{1,2}.?[0-9]{0,20}),'
                                  '(?P<K52>[-+]?[0-9]{1,2}.?[0-9]{0,20}),'
                                  '(?P<K62>[-+]?[0-9]{1,2}.?[0-9]{0,20})\)\s*$', string)
                if match:
                    K11 = float(match.groupdict()['K11'])
                    K21 = float(match.groupdict()['K21'])
                    K31 = float(match.groupdict()['K31'])
                    K41 = float(match.groupdict()['K41'])
                    K51 = float(match.groupdict()['K51'])
                    K61 = float(match.groupdict()['K61'])

                    K12 = float(match.groupdict()['K12'])
                    K22 = float(match.groupdict()['K22'])
                    K32 = float(match.groupdict()['K32'])
                    K42 = float(match.groupdict()['K42'])
                    K52 = float(match.groupdict()['K52'])
                    K62 = float(match.groupdict()['K62'])

                    K = np.array([[K11, K21, K31, K41, K51, K61],
                                  [K12, K22, K32, K42, K52, K62]])

                    msg = MSG_HOST_OUT_CTRL_SF_CONFIG(0, K)
                    return msg
                else:
                    self.cmd_list = [{'type': 'M60'}]
                    return self.cmd_list

            # G3 - Configuration of the xdot controller
            elif cmd == 'G3':
                match = re.search(r'(?i)(?:'
                                  '\s+p(?P<P>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                                  '\s+i(?P<I>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                                  '\s+d(?P<D>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                                  '\s+l(?P<enable_limit>[01])|'
                                  '\s+min(?P<min>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                                  '\s+max(?P<max>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                                  '\s+rl(?P<enable_rate_limit>[01])|'
                                  '\s+dmin(?P<dmin>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                                  '\s+dmax(?P<dmax>[-+]?[0-9]{1,2}.?[0-9]{0,20}))+\s*$', string)
                if match:
                    P = float(match.groupdict()['P']) if match.groupdict()['P'] is not None else 255
                    I = float(match.groupdict()['I']) if match.groupdict()['I'] is not None else 255
                    D = float(match.groupdict()['D']) if match.groupdict()['D'] is not None else 255
                    L = bool(int(match.groupdict()['enable_limit'])) if match.groupdict()[
                                                                            'enable_limit'] is not None else False
                    MIN = float(match.groupdict()['min']) if match.groupdict()['min'] is not None else 255
                    MAX = float(match.groupdict()['max']) if match.groupdict()['max'] is not None else 255
                    LR = bool(int(match.groupdict()['enable_rate_limit'])) if match.groupdict()[
                                                                                  'enable_rate_limit'] is not None else False
                    DMIN = float(match.groupdict()['dmin']) if match.groupdict()['dmin'] is not None else 255
                    DMAX = float(match.groupdict()['dmax']) if match.groupdict()['dmax'] is not None else 255

                    msg = MSG_HOST_OUT_CTRL_SC_X_CONFIG(0, P, I, D, L, MAX, MIN, LR, DMAX, DMIN)
                    return msg
                else:
                    self.cmd_list = [{'type': 'M60'}]
                    return self.cmd_list

            # G4 - Configuration of the psidot controller
            elif cmd == 'G4':
                match = re.search(r'(?i)(?:'
                                  '\s+p(?P<P>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                                  '\s+i(?P<I>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                                  '\s+d(?P<D>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                                  '\s+l(?P<enable_limit>[01])|'
                                  '\s+min(?P<min>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                                  '\s+max(?P<max>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                                  '\s+rl(?P<enable_rate_limit>[01])|'
                                  '\s+dmin(?P<dmin>[-+]?[0-9]{1,2}.?[0-9]{0,20})|'
                                  '\s+dmax(?P<dmax>[-+]?[0-9]{1,2}.?[0-9]{0,20}))+\s*$', string)
                if match:
                    P = float(match.groupdict()['P']) if match.groupdict()['P'] is not None else 255
                    I = float(match.groupdict()['I']) if match.groupdict()['I'] is not None else 255
                    D = float(match.groupdict()['D']) if match.groupdict()['D'] is not None else 255
                    L = bool(int(match.groupdict()['enable_limit'])) if match.groupdict()[
                                                                            'enable_limit'] is not None else False
                    MIN = float(match.groupdict()['min']) if match.groupdict()['min'] is not None else 255
                    MAX = float(match.groupdict()['max']) if match.groupdict()['max'] is not None else 255
                    LR = bool(int(match.groupdict()['enable_rate_limit'])) if match.groupdict()[
                                                                                  'enable_rate_limit'] is not None else False
                    DMIN = float(match.groupdict()['dmin']) if match.groupdict()['dmin'] is not None else 255
                    DMAX = float(match.groupdict()['dmax']) if match.groupdict()['dmax'] is not None else 255

                    msg = MSG_HOST_OUT_CTRL_SC_PSI_CONFIG(0, P, I, D, L, MAX, MIN, LR, DMAX, DMIN)
                    return msg
                else:
                    self.cmd_list = [{'type': 'M60'}]
                    return self.cmd_list

            # todo: remove this message since it is only for testing
            elif cmd == 'G5':
                msg = SetLEDMessage(0,1)
                return msg


            # ------------------------------------------------------------------------------------------------ #
            #                                                M                                                 #
            # ------------------------------------------------------------------------------------------------ #

            # M0 - Debug message (ML should respond with exactly the same string)
            elif cmd == 'M0':
                # UTF-8, 1 Byte max., meaning 40 Unicode characters up until codepoint 7F are allowed
                match = re.search(r'(?i)^(M0\s?)D"(.{1,40})"\s*$', string)
                if match:
                    for ch in match.group(2):
                        if hex(ord(ch)) >= '0x7f':
                            return 'M60'
                    debug_string = match.group(2)
                    msg = MSG_HOST_OUT_DEBUG(0, debug_string)
                    return msg
                else:
                    self.cmd_list = [{'type': 'M60'}]
                    return self.cmd_list

            # M1 - Change FSM state
            if cmd == 'M1':
                # Check for anything other than M1 S[0-4]
                match = re.search(r'(?i)^(M1\s?)S([0-4])\s*$', string)
                if match:
                    state_id = int(match.group(2))
                    msg = MSG_HOST_OUT_FSM(0, FSM_STATE(state_id))
                    return msg
                else:
                    self.cmd_list = [{'type': 'M60'}]
                    return self.cmd_list

            # M2 - Change controller state
            elif cmd == 'M2':
                # Check for anything other than M2 S[0-4]
                match = re.search(r'(?i)^(M2\s?)S([0-4])\s*$', string)
                if match:
                    controller_state = int(match.group(2))
                    msg = MSG_HOST_OUT_CTRL_STATE(0, CTRL_STATE(controller_state))
                    return msg
                else:
                    self.cmd_list = [{'type': 'M60'}]
                    return self.cmd_list

            # M3 - ML enable/disable logging
            elif cmd == 'M3':
                match = re.search(
                    r'(?i)^M3\s?(?:(?P<enable>E1)|(?P<disable>E0))\s?(?:F"(?(enable)(?P<filename>\w{1,40})|)(?:.csv)?")?\s*$',
                    string)
                if match:
                    logging_enable = True if match.groupdict()['enable'] else False
                    filename = match.groupdict()['filename'] if match.groupdict()['filename'] not in [None, ''] else 'log'
                    msg = MSG_HOST_OUT_LOGGING(0, logging_enable, filename)
                    return msg
                else:         
                    self.cmd_list = [{'type': 'M60'}]
                    return self.cmd_list

            # M4 - Reset LL state vector
            elif cmd == 'M4':
                match = re.search(
                    r'(?i)^M4\s*$', string)
                if match:
                    msg = MSG_HOST_OUT_RESET_STATE_VEC(0)
                    return msg
                else:
                    self.cmd_list = [{'type': 'M60'}]
                    return self.cmd_list                    

            # M5 - ML client message handler sleep
            elif cmd == 'M5':
                match = re.search(r'(?i)^\s?M5\s?T(?P<delay_s>[+]?[0-9]{1,2}.?[0-9]{0,20})\s*$', string)
                if match:
                    delay = float(match.groupdict()['delay_s'])
                    msg = MSG_HOST_OUT_DELAY(0, delay)
                    return msg
                else:
                    self.cmd_list = [{'type': 'M60'}]
                    return self.cmd_list

            # M61 - Write g-code documentation to terminal
            elif cmd == 'M61':
                match = re.search(r'(?i)^\s*M61\s*$', string)
                if match:
                    self.cmd_list = [{'type': 'M61'}]
                else:
                    self.cmd_list = [{'type': 'M60'}]

                return self.cmd_list

            # M62 - Clear terminal window
            elif cmd == 'M62':
                match = re.search(r'(?i)^\s*M62\s*$', string)
                if match:
                    self.cmd_list = [{'type': 'M62'}]
                else:
                    self.cmd_list = [{'type': 'M60'}]

                return self.cmd_list

            # M63 - Execute g-codes from file
            elif cmd == 'M63':
                match = re.search(r'(?i)^M63\s?(F"(?P<filename>\w{1,40})(?:.gcode)?")?\s*$', string)
                if match:
                    filename = match.groupdict()['filename'] if match.groupdict()['filename'] else 'general'
                    self.cmd_list = [{'type': 'M63', 'filename': filename}]
                else:
                    self.cmd_list = [{'type': 'M60'}]
                    
                return self.cmd_list

            # M64 - Display robot data
            elif cmd == 'M64':
                match = re.search(r'(?i)^\s*M64\s*$', string)
                if match:
                    self.cmd_list = [{'type': 'M64'}]
                else:
                    self.cmd_list = [{'type': 'M60'}]

                return self.cmd_list

            # M65 - Load experiment
            elif cmd == 'M65':
                match = re.search(r'(?i)^M65\s?(F"(?P<filename>\w{1,40})(?:.yaml)?")?\s*$', string)
                if match:
                    filename = match.groupdict()['filename'] if match.groupdict()['filename'] else None
                    self.cmd_list = [{'type': 'M65', 'filename': filename}]
                else:
                    self.cmd_list = [{'type': 'M60'}]

                return self.cmd_list

            # M66 - Start experiment
            elif cmd == 'M66':
                match = re.search(r'(?i)^M66\s?(F"(?P<filename>\w{1,40})(?:.yaml)?")?\s*$', string)
                if match:
                    filename = match.groupdict()['filename'] if match.groupdict()['filename'] else None
                    self.cmd_list = [{'type': 'M66', 'filename': filename}]
                else:
                    self.cmd_list = [{'type': 'M60'}]

                return self.cmd_list

            # M67 - Load and start experiment
            elif cmd == 'M67':
                match = re.search(r'(?i)^M67\s?(F"(?P<filename>\w{1,40})(?:.yaml)?")?\s*$', string)
                if match:
                    filename = match.groupdict()['filename'] if match.groupdict()['filename'] else None
                    self.cmd_list = [{'type': 'M67', 'filename': filename}]
                else:
                    self.cmd_list = [{'type': 'M60'}]

                return self.cmd_list

            # M68 - End experiment
            elif cmd == 'M68':
                match = re.search(r'(?i)^M68\s?(F"(?P<filename>\w{1,40})(?:.yaml)?")?\s*$', string)
                if match:
                    filename = match.groupdict()['filename'] if match.groupdict()['filename'] else None
                    self.cmd_list = [{'type': 'M68', 'filename': filename}]
                else:
                    self.cmd_list = [{'type': 'M60'}]

                return self.cmd_list

            # M69 - Load sequence
            elif cmd == 'M69':
                match = re.search(r'(?i)^M69\s?(F"(?P<filename>\w{1,40})(?:.csv)?")?\s*$', string)
                if match:
                    filename = match.groupdict()['filename'] if match.groupdict()['filename'] else None
                    self.cmd_list = [{'type': 'M69', 'filename': filename}]
                else:
                    self.cmd_list = [{'type': 'M60'}]

                return self.cmd_list

            # M70 - Start sequence
            elif cmd == 'M70':
                match = re.search(r'(?i)^M70\s?(F"(?P<filename>\w{1,40})(?:.csv)?")?\s*$', string)
                if match:
                    filename = match.groupdict()['filename'] if match.groupdict()['filename'] else None
                    self.cmd_list = [{'type': 'M70', 'filename': filename}]
                else:
                    self.cmd_list = [{'type': 'M60'}]

                return self.cmd_list

            # M71 - Load and start sequence
            elif cmd == 'M71':
                match = re.search(r'(?i)^M71\s?(F"(?P<filename>\w{1,40})(?:.csv)?")?\s*$', string)
                if match:
                    filename = match.groupdict()['filename'] if match.groupdict()['filename'] else None
                    self.cmd_list = [{'type': 'M71', 'filename': filename}]
                else:
                    self.cmd_list = [{'type': 'M60'}]

                return self.cmd_list

            # M72 - End sequence
            elif cmd == 'M72':
                match = re.search(r'(?i)^M72\s?(F"(?P<filename>\w{1,40})(?:.csv)?")?\s*$', string)
                if match:
                    filename = match.groupdict()['filename'] if match.groupdict()['filename'] else None
                    self.cmd_list = [{'type': 'M72', 'filename': filename}]
                else:
                    self.cmd_list = [{'type': 'M60'}]

                return self.cmd_list

            else:
                self.cmd_list = [{'type': 'M60'}]
                return self.cmd_list


gcode_parser = GCODEParser()