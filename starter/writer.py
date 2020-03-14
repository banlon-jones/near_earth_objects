import csv
from enum import Enum


class OutputFormat(Enum):
    """
    Enum representing supported output formatting options for search results.
    """
    display = 'display'
    csv_file = 'csv_file'

    @staticmethod
    def list():
        """
        :return: list of string representations of OutputFormat enums
        """
        return list(map(lambda output: output.value, OutputFormat))


class NEOWriter(object):
    """
    Python object use to write the results from supported output formatting options.
    """

    def __init__(self):
        # Use the OutputFormat in the NEOWriter!
        self.output_formats = OutputFormat.list()

    def write(self, format, data, **kwargs):
        """
        Generic write interface that, depending on the OutputFormat selected calls the
        appropriate instance write function

        :param format: str representing the OutputFormat
        :param data: collection of NearEarthObject or OrbitPath results
        :param kwargs: Additional attributes used for formatting output e.g. filename
        :return: bool representing if write successful or not
        """
        # Using the OutputFormat, Organize our 'write' logic for output to stdout vs to csvfile into instance methods for NEOWriter
        
        if format == self.output_formats[0]:
            try:
                print(data)
                return True
            except IOError as e:
                return False
            
        elif format == self.output_formats[1]:
            try:
                neo_data_output = open('data/neo_data_results.csv', 'w', newline='')
                fieldnames = ['id', 'name', 'diameter_min_km', 'orbits', 'orbit_dates']
                writer = csv.DictWriter(neo_data_output, fieldnames=fieldnames)

                writer.writeheader()

                # output format.
                for neo_object in data:
                    writer.writerow({'id': neo_object.id, 'name': neo_object.name, \
                                    'diameter_min_km': neo_object.diameter_min_km, \
                                    'orbits': [orbit.neo_name for orbit in neo_object.orbits], \
                                    'orbit_dates': [orbit.close_approach_date for orbit in neo_object.orbits]  })
                return True
            except IOError as e:
                return False
        else:
            return False
