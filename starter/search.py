from collections import namedtuple, defaultdict
from enum import Enum
import operator
from exceptions import UnsupportedFeature
from models import NearEarthObject, OrbitPath


class DateSearch(Enum):
    """
    Enum representing supported date search on Near Earth Objects.
    """
    between = 'between'
    equals = 'equals'

    @staticmethod
    def list():
        """
        :return: list of string representations of DateSearchType enums
        """
        return list(map(lambda output: output.value, DateSearch))


class Query(object):
    """
    Object representing the desired search query operation to build. The Query uses the Selectors
    to structure the query information into a format the NEOSearcher can use for date search.
    """

    Selectors = namedtuple('Selectors', ['date_search', 'number', 'filters', 'return_object'])
    DateSearch = namedtuple('DateSearch', ['type', 'values'])
    ReturnObjects = {'NEO': NearEarthObject, 'Path': OrbitPath}

    def __init__(self, **kwargs):
        """
        :param kwargs: dict of search query parameters to determine which SearchOperation query to use
        """
        # Instance variables are used for storing on the Query object!
        self.date = kwargs['date']
        self.end_date = kwargs['end_date']
        self.start_date = kwargs['start_date']
        self.number = kwargs['number']
        self.filter = kwargs['filter']
        self.return_object = kwargs['return_object']

    def build_query(self):
        """
        Transforms the provided query options, set upon initialization, into a set of Selectors that the NEOSearcher
        can use to perform the appropriate search functionality

        :return: QueryBuild.Selectors namedtuple that translates the dict of query options into a SearchOperation
        """

        # Translate the query parameters into a QueryBuild.Selectors object
        data_search = Query.DateSearch(DateSearch.equals.name, self.date) \
                                    if self.date else Query.DateSearch(DateSearch.between.name, \
                                    [self.start_date, self.end_date])

        return_to_object = Query.ReturnObjects.get(self.return_object)

        filters=[]
        
        if self.filter:
            options = Filter.create_filter_options(self.filter)
            
            for key, val in options.items():
                for selected_filter in val:
                    option = selected_filter.split(':')[0]
                    operation = selected_filter.split(':')[1]
                    value = selected_filter.split(':')[-1]
                    filters.append(Filter(option, key, operation, value))

        return Query.Selectors(data_search, self.number, filters, return_to_object)


class Filter(object):
    """
    Object representing optional filter options to be used in the date search for Near Earth Objects.
    Each filter is one of Filter.Operators provided with a field to filter on a value.
    """
    Options = {
        # Dict of filter name to the NearEarthObject or OrbitalPath property
        'diameter': 'diameter_min_km',
        'distance': 'miss_distance_kilometers',
        'is_hazardous': 'is_potentially_hazardous_asteroid'
    }

    Operators = {
        # Dict of operator symbol to an Operators method, see README Task 3 for hint        
        '=': operator.eq,
        '>': operator.gt,
        '>=': operator.ge,
    }

    def __init__(self, field, object, operation, value):
        """
        :param field:  str representing field to filter on
        :param field:  str representing object to filter on
        :param operation: str representing filter operation to perform
        :param value: str representing value to filter for
        """
        self.field = field
        self.object = object
        self.operation = operation
        self.value = value

    @staticmethod
    def create_filter_options(filter_options):
        """
        Class function that transforms filter options raw input into filters

        :param input: list in format ["filter_option:operation:value_of_option", ...]
        :return: defaultdict with key of NearEarthObject or OrbitPath and value of empty list or list of Filters
        """

        # Default dict of filters with key of NearEarthObject or OrbitPath and value of empty list or list of Filters
        value_to_return = defaultdict(list)

        for filter_option in filter_options:
            selectedfilter = filter_option.split(':')[0]

            if hasattr(NearEarthObject(), Filter.Options.get(selectedfilter)):
                value_to_return['NearEarthObject'].append(filter_option)
            elif hasattr(OrbitPath(), Filter.Options.get(selectedfilter)):
                value_to_return['OrbitPath'].append(filter_option)
        return value_to_return

    def apply(self, results):
        """
        Function that applies the filter operation onto a set of results

        :param results: List of Near Earth Object results
        :return: filtered list of Near Earth Object results
        """
        # Takes a list of NearEarthObjects and applies the value of its filter operation to the results
        filtered_list = []

        for near_earth_object in results:
            operation = Filter.Operators.get(self.operation)
            field = Filter.Options.get(self.field)
            value = getattr(near_earth_object, field)

            try:
                if operation(value, self.value):
                    filtered_list.append(near_earth_object)
            except Exception as exp:
                if operation(str(value), str(self.value)):
                    filtered_list.append(near_earth_object)

        return filtered_list


class NEOSearcher(object):
    """
    Object with date search functionality on Near Earth Objects exposed by a generic
    search interface get_objects, which, based on the query specifications, determines
    how to perform the search.
    """

    def __init__(self, db):
        """
        :param db: NEODatabase holding the NearEarthObject instances and their OrbitPath instances
        """
        self.db = db
        # Instance variable can we use to connect DateSearch 
        self.neo_date = dict(db.neo_date)
        self.date_search = None

    def get_objects(self, query):
        """
        Generic search interface that, depending on the details in the QueryBuilder (query) calls the
        appropriate instance search function, then applys any filters, with distance as the last filter.

        Once any filters provided are applied, return the number of requested objects in the query.return_object
        specified.

        :param query: Query.Selectors object with query information
        :return: Dataset of NearEarthObjects or OrbitalPaths
        """
        # This is a generic method that will need to understand, using DateSearch, how to implement search
        # Instance methods that get_objects can use to implement the two types of DateSearch your project
        # needs to support that then your filters can be applied to. Remember to return the number specified in
        # the Query.Selectors as well as in the return_type from Query.Selectors
        self.date_search = query.date_search.type
        date = query.date_search.values
        
        neos = []

        if self.date_search == DateSearch.equals.name:
            neos = self.return_date_search_equal(self.neo_date, date)
        elif self.date_search == DateSearch.between.name:
            neos = self.return_date_search_between(self.neo_date, date[0], date[1])

        distance_filter = None
        for selectedfilter in query.filters:
            if selectedfilter.field == 'distance':
                distance_filter = selectedfilter
                continue
            neos = selectedfilter.apply(neos)
        orbits = self.return_orbit_paths_from_neos(neos)

        filtered_orbits = orbits
        filtered_neos = neos

        if distance_filter:
            filtered_orbits = distance_filter.apply(orbits)

            filtered_neos = self.return_neo_from_orbit_path(filtered_orbits)

        filtered_neos = list(set(filtered_neos))
        filtered_orbits = list(set(filtered_orbits))

        if query.return_object == OrbitPath:
            return filtered_orbits[: int(query.number)]
        return filtered_neos[: int(query.number)]
    
    
    def return_date_search_equal(self, orbit_path, date):
        neos_date_equal = []
        for key, value in orbit_path.items():
            if key == date:
                neos_date_equal += value
        return neos_date_equal
    
    def return_date_search_between(self, orbit_path, start_date, end_date):
        neos_date_between = []
        for key, value in orbit_path.items():
            if key >= start_date and key <= end_date:
                neos_date_between += value
        return neos_date_between

    def return_orbit_paths_from_neos(self, neos):
        neo_paths = []
        for neo in neos:
            neo_paths += neo.orbits
        return neo_paths

    def return_neo_from_orbit_path(self, orbit_paths):
        neo = [self.db.neo_name.get(path.neo_name) for path in orbit_paths]
        return neo
