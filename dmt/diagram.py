#!/usr/bin/env python3

import sys

from sqlalchemy import MetaData
from sqlalchemy_schemadisplay import create_schema_graph


def main():
    if len(sys.argv) < 2:
        print("Usage: " + sys.argv[0] + ' <database_name>')
        sys.exit(1)

    # create the pydot graph object by autoloading all tables via a bound metadata object
    graph = create_schema_graph(
        metadata=MetaData(
            'postgresql+psycopg2://taste:tastedb@localhost/' + sys.argv[1]),
        show_datatypes=False,  # The image would get too big if we'd show the datatypes
        show_indexes=False,    # ditto for indexes
        rankdir='LR',          # From left to right (instead of top to bottom)
        concentrate=True       # Don't try to join the relation lines together
    )
    graph.write_png(sys.argv[1] + '.png')  # write out the file


if __name__ == "__main__":
    main()
