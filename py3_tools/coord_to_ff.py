import argparse
from turtle import st

from ff2geojson import *
from ForeFirepy3 import *

def main():
	ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	ap.add_argument(
        "--lat",
        help="latitude of fire start"
    )
	ap.add_argument(
        "--lon",
        help="longitude of fire start"
		)
	args = vars(ap.parse_args())
	lat = args.get('lat')
	lon = args.get('lon')

	dir_path = os.path.dirname(os.path.realpath(__file__))
	output_path = dir_path + '/../examples/aullene/'
	filename = f'{lon}_{lat}.ff'
	complete_path = output_path + filename

	[x, y] = reproject([lon, lat], inEpsg='epsg:4326', outEpsg='epsg:32632')

	ff = Forefire()
	ff.configBasicFf(lon=x, lat=y)
	ff.saveFf(complete_path)

	os.system(f'cd {output_path}; ../../bin/forefire -i {filename}')
	
	ffjson2geojson(output_path + '0-2009-07-24T14-57-39Z.json')


if __name__ == '__main__':
    main()