import os
from tempfile import TemporaryDirectory
from pathlib import Path
import pycolmap
import time
from multiprocessing import Process, Event

from lib.sfm.database_populator import populate
from lib.sfm.model import get_map_and_cams
from lib.utils import cprint, Col, SupressLogging
from lib import map_cleaner
from lib.file_monitor import DirectoryMonitor
from lib.led_map_2d import get_all_2d_led_maps


class SFM(Process):

    def __init__(self, directory: Path, rescale=False, interpolate=False):
        super().__init__()
        self.directory_monitor = DirectoryMonitor(directory)
        self.rescale = rescale
        self.interpolate = interpolate
        self.exit = Event()

    def run(self):
        self.reload()
        while not self.exit.is_set():
            time.sleep(1)
            if self.directory_monitor.has_changed():
                self.reload()

    def shutdown(self):
        self.exit.set()

    def reload(self):
        maps_2d = get_all_2d_led_maps(self.directory_monitor.directory)
        if len(maps_2d) < 2:
            return None
        map_3d = self.process(maps_2d, self.rescale, self.interpolate)
        if map_3d is None:
            return None
        map_3d.write_to_file(self.directory_monitor.directory / "led_map_3d.csv")
        return map_3d

    @staticmethod
    def process(maps_2d, rescale=False, interpolate=False):

        if len(maps_2d) < 2:
            return None

        with TemporaryDirectory() as temp_dir:
            database_path = os.path.join(temp_dir, "database.db")

            populate(database_path, maps_2d)

            options = pycolmap.IncrementalPipelineOptions()
            options.triangulation.ignore_two_view_tracks = False  # used to be true
            options.min_num_matches = 9  # default 15
            options.mapper.abs_pose_min_num_inliers = 9  # default 30
            options.mapper.init_min_num_inliers = 50  # used to be 100

            with SupressLogging():
                pycolmap.incremental_mapping(
                    database_path=database_path,
                    image_path=temp_dir,
                    output_path=temp_dir,
                    options=options,
                )

            if not os.path.exists(os.path.join(temp_dir, "0", "points3D.bin")):
                return None

            map_3d, cams = get_map_and_cams(temp_dir)

            if rescale:
                map_cleaner.rescale(map_3d, cams)

            if interpolate:
                leds_interpolated = map_cleaner.fill_gaps(map_3d)
                cprint(f"Interpolated {leds_interpolated} leds", format=Col.BLUE)

        return map_3d
