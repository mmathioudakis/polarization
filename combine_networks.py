"""
a script to create a cumulative network out of individual networks
"""
import sys, os
import polarlib.file_utils as file_utils
import polarlib.polar_utils as polar_utils
import argparse
import re
import networkx as nx


class Error(Exception):
	pass


if __name__ == '__main__' :

	# parse arguments

	parser = argparse.ArgumentParser()
	parser.add_argument('kind', choices = ['retweets', 'replies'],
		default = 'retweets',
		help = 'What kind of networks to analyze.')
	parser.add_argument('topic', help = 'keyword defining the topic')
	parser.add_argument('granularity', choices = ['week', 'month'],
		help = 'Granularity.')
	parser.add_argument('--klcc', action = 'store_true',
		help = 'Work with largest connected component.')
	parser.add_argument('-o', '--output_folder',
		default = 'stressed_polarization/results',
		help = 'Folder where to store results.')


	args = parser.parse_args()

	# prepare output file
	# and test that we can write to it
	output_filename = ".".join([args.kind, args.topic, args.granularity,
		"graph"])
	output_path = '/'.join([args.output_folder, output_filename])

	try:
		f = open(output_path, 'w')
		f.write('')
		f.close()
	except Exception as e:
		my_error = Error("Cannot write to output file: {}".format(output_path))
		raise my_error from e

	global_graph = nx.DiGraph()

	# go over networks
	ALL_RT_NETWORKS_FOLDER = 'data/twitter_under_stress/networks'
	ALL_MT_NETWORKS_FOLDER = 'data/twitter_under_stress/reply_networks'

	ALL_NETWORKS_FOLDER = ALL_MT_NETWORKS_FOLDER if args.kind == 'replies' \
		else ALL_RT_NETWORKS_FOLDER

	topic_networks_folder = "/".join([ALL_NETWORKS_FOLDER, args.topic])
	
	for filename in os.listdir(topic_networks_folder):

		try:

			if args.klcc:
				pattern = "".join([args.granularity, "([0-9]+)",
					"_largest_CC.txt"])
			else:
				pattern = "".join([args.granularity, "([0-9]+)$"])

			match = re.search(pattern, filename)

			if match is not None:

				print("At filename:", filename)
				
				num = match.group(1) # the id of the interval

				network_str = "/".join([topic_networks_folder, filename])
				network = file_utils.load_network_from_file(network_str,
					is_directed = True)

				# update existing network
				for edge in network.edges(data = True):

					u, v, attr_dict = edge
					weight = attr_dict.get('weight', 1)

					current_weight = global_graph.edge.get(u, {}).get(v, {}).get('weight', 0)
					updated_weight = weight + current_weight
					global_graph.add_edge(u, v, {'weight': updated_weight})

		except Exception as e:
			raise e
			# print(e, file = sys.stderr)

	nx.write_gpickle(global_graph, output_path)



