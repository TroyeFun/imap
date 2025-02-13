# -*- coding: utf-8 -*-
#!/usr/bin/env python

# Copyright 2021 daohu527 <daohu527@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt

import imap.global_var as global_var
from imap.lib.draw import add_editor, show_map
from imap.lib.convertor import Opendrive2Apollo
from imap.lib.opendrive.map import Map as XodrMap


def convert_map_format(input_path, output_path):
    opendrive2apollo = Opendrive2Apollo(input_path, output_path)
    # todo(zero): only lane type is driving add relationship!!!
    opendrive2apollo.set_parameters(only_driving=False)
    opendrive2apollo.convert()
    opendrive2apollo.save_map()


def show_open_drive_map(map_file):
    opendrive2apollo = Opendrive2Apollo(map_file)
    opendrive2apollo.set_parameters(only_driving=False)
    opendrive2apollo.convert()


def show_open_drive_map_lane_boundaries(map_file, only_driving=False):
    suffix = map_file.split(".")[-1]
    assert suffix == "xodr"
    xodr_map = XodrMap()
    xodr_map.load(map_file)
    for road_id, road in xodr_map.roads.items():
        road.generate_reference_line()
        road.add_offset_to_reference_line()
        road.add_origin_to_reference_line(0.0, 0.0)
        road.process_lanes()
        for lane_section in road.lanes.lane_sections:
            for lane in lane_section.left + lane_section.right:
                if only_driving and lane.lane_type != 'driving':
                    continue
                left_x = [p.x for p in lane.left_boundary]
                left_y = [p.y for p in lane.left_boundary]
                right_x = [p.x for p in lane.right_boundary]
                right_y = [p.y for p in lane.right_boundary]
                polygon_x = left_x + right_x[::-1] + left_x[0:1]
                polygon_y = left_y + right_y[::-1] + left_y[0:1]
                plt.plot(polygon_x, polygon_y)
    plt.grid(True)
    plt.show()


def main(args=sys.argv):
    parser = argparse.ArgumentParser(
        description="Imap is a tool to display hdmap info on a map.",
        prog="main.py")

    parser.add_argument(
        "-m", "--map", action="store", type=str, required=False,
        help="Specify the map file in txt or binary format")
    parser.add_argument(
        "--save_fig", action="store", type=bool, required=False,
        default=False, help="Whether to save the visualization figure (only for .xodr suffix)")
    parser.add_argument(
        "-z", "--enable_z_axis", action="store", type=bool, required=False,
        default=False, help="Whether to extract z-axis coordination information to apollo hd-map")
    parser.add_argument(
        "-l", "--lane", action="store", type=str, required=False,
        help="Find lane by lane id")

    parser.add_argument(
        "-f", "--format", action="store", type=str, required=False,
        nargs='?', const="0", help="Convert format")
    parser.add_argument(
        "-i", "--input", action="store", type=str, required=False,
        help="map input path")
    parser.add_argument(
        "-o", "--output", action="store", type=str, required=False,
        help="map output path")
    parser.add_argument(
        "-s", "--sampling", action="store", type=float, required=False,
        default=1.0, help="sampling length")
    parser.add_argument(
        "-d", "--debug", action="store", type=bool, required=False,
        nargs='?', const=True, default=False, help="debug mode")

    args = parser.parse_args(args[1:])

    # 1. Init global var
    global_var._init()
    global_var.set_element_vaule("sampling_length", args.sampling)
    global_var.set_element_vaule("debug_mode", args.debug)
    global_var.set_element_vaule("enable_z_axis", args.enable_z_axis)

    # 2. show map
    if args.map is not None:
        map_file = Path(args.map)
        if not map_file.is_file():
            logging.error("File not exist! '{}'".format(args.map))
            return
        suffix = args.map.split(".")[1]
        if suffix == "bin" or suffix == "txt":
            add_editor()
            show_map(args.map, args.lane)
        elif suffix == "xodr":
            global_var.set_element_vaule("need_save_figure", args.save_fig)
            show_open_drive_map(args.map)
            show_open_drive_map_lane_boundaries(args.map)
        else:
            pass

    # 3. convert opendrive map to apollo
    if args.format is not None:
        map_file = Path(args.input)
        if not map_file.is_file():
            logging.error("File not exist! '{}'".format(args.input))
            return
        convert_map_format(args.input, args.output)


if __name__ == '__main__':
    main()