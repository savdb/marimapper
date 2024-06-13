import argparse
import sys

sys.path.append("./")

from lib.remesher import remesh, save_mesh
from lib.utils import cprint, Col
from lib.led_map_3d import LEDMap3D

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Convert a 3D map to a mesh")

    parser.add_argument(
        "map_filename",
        type=str,
        help="The CSV 3D map file generated by marimapper.py",
    )

    parser.add_argument(
        "mesh_filename", type=str, help="The output PLY filename", default="mesh.ply"
    )

    parser.add_argument(
        "--detail", type=int, help="the detail level of the mesh", default=8
    )

    args = parser.parse_args()

    if not args.mesh_filename.endswith(".ply"):
        cprint("Failed to remesh, file output extension must by .ply", format=Col.FAIL)
        quit()

    led_map = LEDMap3D(args.map_filename)

    if not led_map.valid:
        quit()

    mesh = remesh(led_map, args.detail)

    if not save_mesh(mesh, args.mesh_filename):
        cprint(f"Failed to save mesh to {args.mesh_filename}", format=Col.FAIL)
