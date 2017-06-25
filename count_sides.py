"""
a script to measure polarized networks
"""
import sys, os
import polarlib.file_utils as file_utils
import polarlib.polar_utils as polar_utils
import argparse
import json
import re
import networkx as nx

if __name__ == '__main__' :

	# parse arguments

	parser = argparse.ArgumentParser()
	parser.add_argument('topic', help = 'keyword defining the topic')
	parser.add_argument('granularity', choices = ['week', 'month'],
		help = 'Granularity.')
	parser.add_argument('-o', '--output_folder',
		default = 'stressed_polarization/results',
		help = 'Folder where to store results.')


	args = parser.parse_args()

	# prepare output file
	# and test that we can write to it
	output_filename = ".".join([args.topic, args.granularity,
		"sides"])
	output_path = '/'.join([args.output_folder, output_filename])

	try:
		f = open(output_path, 'w')
		f.write('')
		f.close()
	except Exception as e:
		my_error = Error("Cannot write to output file: {}".format(output_path))
		raise my_error from e

	# this is where we store all the results
	all_sides = []
	

	# go over communities
	
	ALL_COMMUNITIES_FOLDER = 'data/twitter_under_stress/communities'
	topic_communities_folder = "/".join([ALL_COMMUNITIES_FOLDER, args.topic])

	for filename in os.listdir(topic_communities_folder):

		try:

			pattern = "".join(["liberals_", args.granularity, "([0-9]+)"])
			match = re.search(pattern, filename)

			if match is not None:

				print("At filename:", filename)
				
				num = match.group(1) # the id of the interval

				comm_1_str = "".join([topic_communities_folder, "/liberals_",
					args.granularity, str(num), ".txt"])
				comm_2_str = "".join([topic_communities_folder, "/conservatives_",
					args.granularity, str(num), ".txt"])

				# print("Sides files:\n{}\n{}".format(comm_1_str, comm_2_str))

				side_1 = file_utils.load_side_from_file(comm_1_str)
				side_2 = file_utils.load_side_from_file(comm_2_str)

				all_sides.extend([list(side_1), list(side_2)])

		except Exception as e:

			print(e, file = sys.stderr)

	with open(output_path, 'w') as output:
		output.write(json.dumps(all_sides))
		print("Dumped {} sides".format(len(all_sides)))





