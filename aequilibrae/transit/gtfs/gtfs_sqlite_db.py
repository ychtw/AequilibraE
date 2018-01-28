import sqlite3
from collections import OrderedDict
import os
import numpy as np
import codecs
import copy


class create_gtfsdb:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.__max_chunk_size = None
        self.available_files = {}
        OrderedDict([('s',(1,2)),('p',(3,4)),('a',(5,6)),('m',(7,8))])
        self.column_order = {'agency.txt': OrderedDict([('agency_id', str),
                                                       ('agency_name', str),
                                                       ('agency_url', str),
                                                       ('agency_timezone', str),
                                                       ('agency_lang', str),
                                                       ('agency_phone', str),
                                                       ('agency_fare_url', str),
                                                       ('agency_email', str)]),

                             'routes.txt': OrderedDict([('route_id', str),
                                                       ('agency_id', str),
                                                       ('route_short_name', str),
                                                       ('route_long_name', str),
                                                       ('route_desc', str),
                                                       ('route_type', int),
                                                       ('route_url', str),
                                                       ('route_color', str),
                                                       ('route_text_color', str),
                                                       ('route_sort_order', int)]),

                             'trips.txt': OrderedDict([('route_id', str),
                                                       ('service_id', str),
                                                       ('trip_id', str),
                                                       ('trip_headsign', str),
                                                       ('trip_short_name', str),
                                                       ('direction_id', int),
                                                       ('block_id', str),
                                                       ('shape_id', str),
                                                       ('wheelchair_accessible', int),
                                                       ('bikes_allowed', int)]),

                             'stop_times.txt': OrderedDict([('trip_id', str),
                                                            ('arrival_time', str),
                                                            ('departure_time', str),
                                                            ('stop_id', str),
                                                            ('stop_sequence', int),
                                                            ('stop_headsign', str),
                                                            ('pickup_type', int),
                                                            ('shape_dist_traveled', float),
                                                            ('timepoint', int)]),

                             'calendar.txt': OrderedDict([('service_id', str),
                                                            ('monday', int),
                                                            ('tuesday', int),
                                                            ('wednesday', int),
                                                            ('thursday', int),
                                                            ('friday', int),
                                                            ('saturday', int),
                                                            ('sunday', int),
                                                            ('start_date', str),
                                                            ('end_date', str)])}
        self.set_chunk_size(30000)

    def set_chunk_size(self, chunk_size):
        if chunk_size is not None:
            if isinstance(chunk_size, int):
                self.__max_chunk_size = chunk_size

    def create_database(self, save_db=None, memory_db=False, overwrite=False):


        self.__create_database(save_db, memory_db, overwrite)
        return self.conn

    def __create_database(self, save_db, memory_db, overwrite):
        if save_db is None:
            if not memory_db:
                save_db = ":memory:"
        else:
            if memory_db:
                raise ValueError("You can't have a file name and have the file in memory at the same time")

        if not overwrite:
            if os.path.isfile(os.path.join(save_db)):
                raise ValueError("Output database exists. Please use overwrite=True or choose a different path/name")

        self.conn = sqlite3.connect(save_db)
        self.cursor = self.conn.cursor()

        # enable extension loading
        self.conn.enable_load_extension(True)

        self.__create_empty_tables()

    def __create_empty_tables(self):
        self.__create_agency_table()
        self.__create_route_table()
        self.__create_trips_table()
        self.__create_stop_times_table()
        self.__create_calendar_table()
        self.conn.commit()

    def __create_agency_table(self):
        self.cursor.execute('DROP TABLE IF EXISTS agency')
        create_query = '''CREATE TABLE 'agency' (agency_id VARCHAR PRIMARY KEY UNIQUE,
                                                 agency_name VARCHAR  NOT NULL,
                                                 agency_url VARCHAR  NOT NULL,
                                                 agency_timezone VARCHAR  NOT NULL,
                                                 agency_lang VARCHAR,
                                                 agency_phone VARCHAR,
                                                 agency_fare_url VARCHAR,
                                                 agency_email VARCHAR);'''
        self.cursor.execute(create_query)

    def __create_route_table(self):
        self.cursor.execute('DROP TABLE IF EXISTS routes')
        create_query = '''CREATE TABLE 'routes' (route_id VARCHAR PRIMARY KEY UNIQUE NOT NULL,
                                                 agency_id VARCHAR,
                                                 route_short_name VARCHAR,
                                                 route_long_name VARCHAR,
                                                 route_desc VARCHAR,
                                                 route_type NUMERIC NOT NULL,
                                                 route_url VARCHAR,
                                                 route_color VARCHAR,
                                                 route_text_color VARCHAR,
                                                 route_sort_order NUMERIC,
                                                 FOREIGN KEY(agency_id) REFERENCES agency(agency_id));'''

        self.cursor.execute(create_query)

    def __create_trips_table(self):
        self.cursor.execute('DROP TABLE IF EXISTS trips')
        #TODO: Add foreign key to calendar_dates.txt
        create_query = '''CREATE TABLE 'trips' (route_id VARCHAR NOT NULL,
                                                service_id VARCHAR NOT NULL,
                                                trip_id VARCHAR PRIMARY KEY UNIQUE NOT NULL,
                                                trip_headsign VARCHAR,
                                                trip_short_name VARCHAR,
                                                direction_id NUMERIC,
                                                block_id VARCHAR,
                                                shape_id VARCHAR,
                                                wheelchair_accessible NUMERIC,
                                                bikes_allowed NUMERIC,
                                                FOREIGN KEY(route_id) REFERENCES routes(route_id)
                                                FOREIGN KEY(service_id) REFERENCES calendar(service_id));'''

        self.cursor.execute(create_query)

    def __create_calendar_table(self):
        self.cursor.execute('DROP TABLE IF EXISTS calendar')
        create_query = '''CREATE TABLE 'calendar' (service_id VARCHAR NOT NULL,
                                                   monday NUMERIC NOT NULL DEFAULT 1,
                                                   tuesday NUMERIC NOT NULL DEFAULT 1,
                                                   wednesday NUMERIC NOT NULL DEFAULT 1,
                                                   thursday NUMERIC NOT NULL DEFAULT 1,
                                                   friday NUMERIC NOT NULL DEFAULT 1,
                                                   saturday NUMERIC NOT NULL DEFAULT 1,
                                                   sunday NUMERIC NOT NULL DEFAULT 1,
                                                   start_date VARCHAR,
                                                   end_date VARCHAR,
                                                   FOREIGN KEY(service_id) REFERENCES trips(service_id));'''

        self.cursor.execute(create_query)

    def __create_stop_times_table(self):
        self.cursor.execute('DROP TABLE IF EXISTS stop_times')
        create_query = '''CREATE TABLE 'stop_times' (trip_id VARCHAR NOT NULL,
                                                     arrival_time VARCHAR NOT NULL,
                                                     departure_time VARCHAR NOT NULL,
                                                     stop_id VARCHAR NOT NULL,
                                                     stop_sequence NUMERIC NOT NULL,
                                                     stop_headsign VARCHAR,
                                                     pickup_type NUMERIC DEFAULT 0,
                                                     drop_off_type NUMERIC  DEFAULT 0,
                                                     shape_dist_traveled NUMERIC,
                                                     timepoint NUMERIC,
                                                     FOREIGN KEY(trip_id) REFERENCES trips(trip_id)
                                                     FOREIGN KEY(stop_id) REFERENCES stops(stop_id));'''

        self.cursor.execute(create_query)

    def load_from_zip(self, file_path):
        # TODO: Unzip to temp folder
        self.load_from_folder()
        #TODO: delete temp folder

    def load_from_folder(self, path_to_folder, save_db=None, memory_db=False, overwrite=False):
        self.source_folder = path_to_folder

        # In case we have not create the database yet
        if self.conn is None:
            self.__create_database(save_db, memory_db, overwrite)

        tables = ['agency', 'routes', 'trips', "stop_times", "calendar"]
        for tbl in tables:
            self.__load_tables(tbl)

    def __load_tables(self, table_name):
        # Agency
        file_to_open = table_name + '.txt'
        data_file = os.path.join(self.source_folder, file_to_open)
        if not os.path.isfile(data_file):
            self.available_files[file_to_open] = False
            return

        self.available_files[file_to_open] = True
        data = self.open(data_file, column_order= self.column_order[file_to_open])
        dt = tuple(data.tolist())
        cols = data.dtype.names
        fields = ','.join(len(cols)*["?"])
        if not isinstance(dt[0], tuple):
            dt = [dt]

        self.cursor.executemany("INSERT into " + table_name + " (" + ",".join(cols) + ") VALUES(" + fields + ")", dt)

        self.conn.commit()

    @staticmethod
    def open(file_name, column_order=False):
        # Read the stops and cleans the names of the columns
        data = np.genfromtxt(file_name, delimiter=',', names=True, dtype=None,)
        content = [str(unicode(x.strip(codecs.BOM_UTF8), 'utf-8')) for x in data.dtype.names]
        data.dtype.names = content
        if column_order:
            col_names = [x for x in column_order.keys() if x in content]
            data = data[col_names]

            # Define sizes for the string variables
            column_order = copy.deepcopy(column_order)
            for c in col_names:
                if column_order[c] is str:
                    if data[c].dtype.char.upper() == "S":
                        column_order[c] = data[c].dtype
                    else:
                        column_order[c] = "S16"

            new_data_dt = [(f, column_order[f]) for f in col_names]

            if int(data.shape.__len__())> 0:
                new_data = np.array(data, new_data_dt)
            else:
                new_data = data


        else:
            new_data = data
        return new_data
    # "SELECT InitSpatialMetaData()"
    # "SELECT AddGeometryColumn( 'links', 'geometry', 4326, 'LINESTRING', 'XY' )"
    # "SELECT CreateSpatialIndex( 'links' , 'geometry' )"
    # '''CREATE INDEX links_a_node_idx ON links (a_node)'''
    # '''CREATE INDEX links_b_node_idx ON links (b_node)'''
    #
    # cur.execute("CREATE TABLE definitions (def_id INTEGER, def TEXT,"
    #             "word_def INTEGER, FOREIGN KEY(word_def) REFERENCES vocab(vocab_id))")
