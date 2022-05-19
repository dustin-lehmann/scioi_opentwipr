from typing import List, Dict, Tuple, Set, Optional, Union, Sequence, Callable, Iterable, Iterator, \
    Any, AnyStr, TextIO, BinaryIO
import io
import os.path
import os
import csv
import yaml


class IOHandler:
    """ Base class for all file handlers """

    def __init__(self) -> None:
        pass

    # def open(self):
    #     pass
    #
    # def read(self):
    #     pass
    #
    # def write(self):
    #     pass
    #
    # def close(self):
    #     pass


class TXTHandler(IOHandler):
    directory: str
    filepath: str
    mode: str
    file: TextIO
    file_empty: bool

    def __init__(self) -> None:
        super(TXTHandler, self).__init__()
        self.directory = ''
        self.relative_filepath = ''
        self.mode = ''
        self.file = io.StringIO('')
        self.file_empty = True
        self.end_of_line = '\n'
        self.comment_symbol = '#'

    def open(self, filepath: str, mode: str = 'r') -> Optional[str]:
        try:
            self.mode = mode
            self.filepath = filepath
            self.file = open(file=self.filepath, mode=self.mode)
        except OSError as e:
            error_string = "{}. Failed to open file! ({})".format(e, self.filepath)
            return error_string

    def read(self):
        # implemented with a generator (just for fun)
        try:
            # blank lines and lines starting with a hashtag are ignored
            for raw_line in self.file:
                if raw_line[0] not in (self.end_of_line, self.comment_symbol):
                    self.file_empty = False
                    processed_line = raw_line.rstrip('\n')
                    yield processed_line
        except ValueError as e:
            print("{} Failed to read file! ({})".format(e, self.filepath))
        finally:
            if self.file_empty:
                yield 0

    def write(self) -> None:
        pass

    def close(self) -> Optional[str]:
        try:
            self.file.close()
        except OSError as e:
            error_string = "{} Failed to close file! ({})".format(e, self.filepath)
            return error_string


class CSVHandler(IOHandler):
    def __init__(self) -> None:
        super(CSVHandler, self).__init__()
        pass

    def open(self):
        pass

    @staticmethod
    def read(filepath: str, valid_field_name_combinations: List[List[str]]) -> Optional[List[Dict[str, float]]]:
        # this function should receive a relative filepath and return a list of which each
        # element is a dictionary containing the field name as well a the respective data from the
        # read row
        try:
            with open(filepath) as csv_file:
                reader = csv.DictReader(csv_file)

                # check file
                if reader.fieldnames not in valid_field_name_combinations:
                    print("Wrong fieldnames in file {}".format(filepath))
                    return

                input_data = []
                for row in reader:
                    # change the string input command to type float
                    dictionary = dict(row)
                    for key, value in dictionary.items():
                        dictionary[key] = float(value)

                    input_data.append(dictionary)

                return input_data
        except OSError:
            return None

    # CHECK
    def write(self):
        pass

    def close(self):
        pass


class YAMLHandler(IOHandler):
    """ Class for handling .yaml files containing an experiment configuration. """
    def __init__(self) -> None:
        super(YAMLHandler, self).__init__()

    @staticmethod
    def get_dictionary(filepath: str) -> Optional[Dict[str, Any]]:
        try:
            with open(filepath, 'r') as file:
                dictionary = yaml.load(file, Loader=yaml.SafeLoader)

            return dictionary
        except OSError:
            return None

    def open(self):
        pass

    def read(self):
        pass

    def write(self):
        pass

    def close(self):
        pass


class FileHandler:
    """
    An object of this class is able to create directories, copy and rename files.
    This will become very useful for managing all relevant files belonging to a specific
    experiment after its completion.
    """
    def __init__(self) -> None:
        pass


txt_handler = TXTHandler()
csv_handler = CSVHandler()
yaml_handler = YAMLHandler()
file_handler = FileHandler()